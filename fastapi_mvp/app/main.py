import os
import requests
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# 🚀 Sørg for at vi alltid finner .env i rotmappa
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    startDate: str = None,
    endDate: str = None,
    classification: str = None,
    size: int = 200,
):
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise HTTPException(500, "Mangler API_KEY")

    params = {
        "apikey": api_key,
        "countryCode": "NO",
        "latlong": "60.39299,5.32415",  # Bergen sentrum
        "radius": "20",
        "unit": "km",
        "locale": "*",
        "size": size,
        "sort": "date,asc"
    }

    if startDate and endDate:
        params["startDateTime"] = f"{startDate}T00:00:00Z"
        params["endDateTime"] = f"{endDate}T23:59:59Z"

    if classification:
        params["classificationName"] = classification

    response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params)
    data = response.json()

    events = data.get("_embedded", {}).get("events", [])
    #return templates.TemplateResponse("home.html", {"request": request, "events": events})
    return templates.TemplateResponse(request, "home.html", {"events": events})

