import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .services.repository import fetch_events

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    startDate: str | None = None,
    endDate: str | None = None,
    classification: str | None = None,
    keyword: str | None = None,
):
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
        },
    )
