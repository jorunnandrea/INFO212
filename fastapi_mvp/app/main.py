import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from passlib.context import CryptContext
import sqlite3
from app.services.repository import fetch_events
import secrets
import time

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



# Passordhashing
#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Passordhashing (byttet fra bcrypt til pbkdf2_sha256 pga backend-feil)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# Databasefunksjoner
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
    # Add reset_token and reset_token_expires columns for password reset
    try:
        db.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
        db.execute("ALTER TABLE users ADD COLUMN reset_token_expires INTEGER")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    db.commit()
    db.close()

# Initialiser database ved oppstart
init_db()

# Hjelpefunksjon for å sjekke om bruker er logget inn
def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")
    if user_id:
        db = get_db()
        user = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
        db.close()
        return user
    return None

# Ruter for brukerfunksjonalitet
@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
#endret fra response: Respons. Fikset bug som gjorde at siden crashet hvis man skriver feilpassord
def login(request: Request, username: str = Form(...), password: str = Form(...)):    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    db.close()
    
    if user and pwd_context.verify(password, user["password_hash"]):
        response = RedirectResponse(url="/", status_code=303)  # Changed from /dashboard to /
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
def signup(
    request: Request,
    username: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    db = get_db()
    hashed_password = pwd_context.hash(password)
    
    try:
        db.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                   (username, email, hashed_password))
        db.commit()
        db.close()
        return RedirectResponse(url="/", status_code=303)  # Changed from /login to /
    except sqlite3.IntegrityError:
        db.close()
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Username or email already exists"
        })

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("user_id")
    return response

# NEW: Forgot password route
@app.get("/forgot-password", response_class=HTMLResponse)
def show_forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/forgot-password")
def forgot_password(request: Request, username: str = Form(...)):
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    
    if user:
        # Generate a reset token
        reset_token = secrets.token_urlsafe(32)
        reset_token_expires = int(time.time()) + 3600  # Token expires in 1 hour
        
        # Save the reset token to the database
        db.execute("UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?", 
                   (reset_token, reset_token_expires, user["id"]))
        db.commit()
        # In a real application, you would send an email here with the reset link
        # For now, we'll just show a message
        db.close()
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Password reset instructions have been sent to your email. (In a real app, you would receive an email with a reset link)"
        })
    else:
        db.close()
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Username not found"
        })

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
    user_id: str = None
):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    if new_password != confirm_new_password:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "New passwords do not match"
        })
    
    if len(new_password) < 6:
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "New password must be at least 6 characters long"
        })
    
    db = get_db()
    db_user = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    
    if not pwd_context.verify(current_password, db_user["password_hash"]):
        db.close()
        return templates.TemplateResponse("change_password.html", {
            "request": request,
            "username": user["username"],
            "error": "Current password is incorrect"
        })
    
    new_hashed_password = pwd_context.hash(new_password)
    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", 
               (new_hashed_password, user["id"]))
    db.commit()
    db.close()
    
    return RedirectResponse(url="/", status_code=303)  # Redirect to homepage after successful change

@app.get("/dashboard", response_class=HTMLResponse)
def show_dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["username"]
    })

# Oppdatert hjemmesiderute med brukerinfo
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    startDate: str | None = None,
    endDate: str | None = None,
    classification: str | None = None,
    keyword: str | None = None,
):
    user = get_current_user(request)  # Sjekk om bruker er logget inn
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
            "current_user": user  # Send brukerinfo til malen
        },
    )
