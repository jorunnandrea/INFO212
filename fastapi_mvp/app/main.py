import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from passlib.context import CryptContext
import sqlite3
from app.services.repository import fetch_events

# Load environment
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")

def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        db.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        db.execute("ALTER TABLE users ADD COLUMN reset_token_expires INTEGER")
    except sqlite3.OperationalError:
        pass
    db.commit()
    db.close()

init_db()

def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")
    if user_id:
        db = get_db()
        user = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        db.close()
        return user
    return None

@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    if user and pwd_context.verify(password, user["password_hash"]):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })

@app.get("/signup", response_class=HTMLResponse)
def show_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = get_db()
    hashed_password = pwd_context.hash(password)
    try:
        db.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                   (username, email, hashed_password))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Brukernavn eller e-post er allerede i bruk"
        })
    db.close()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/forgot-password", response_class=HTMLResponse)
def show_forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
def forgot_password(
    request: Request,
    username: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
):
    if new_password != confirm_new_password:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Nytt passord må matche bekreftelse"
        })
    if len(new_password) < 6:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Passord må være minst 6 tegn"
        })
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        db.close()
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Brukernavn ikke funnet"
        })
    hashed_password = pwd_context.hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user["id"]))
    db.commit()
    db.close()
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    return response

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

@app.get("/change-password", response_class=HTMLResponse)
def show_change_password(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("change_password.html", {
        "request": request,
        "username": user["username"]
    })

@app.post("/change-password")
def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    if new_password != confirm_new_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "Nytt passord må matche"
        })
    if len(new_password) < 6:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "Passord må være minst 6 tegn"
        })
    db = get_db()
    db_user = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not pwd_context.verify(current_password, db_user["password_hash"]):
        db.close()
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "Nåværende passord er feil"
        })
    new_hashed_password = pwd_context.hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hashed_password, user["id"]))
    db.commit()
    db.close()
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["username"]
    })

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    startDate: str | None = None,
    endDate: str | None = None,
    classification: str | None = None,
    keyword: str | None = None,
):
    user = get_current_user(request)
    events = fetch_events(startDate, endDate, classification, keyword)
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "events": events,
            "startDate": startDate or "",
            "endDate": endDate or "",
            "classification": classification or "",
            "keyword": keyword or "",
            "current_user": user
        },
    )