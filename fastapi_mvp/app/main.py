from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pathlib import Path
import os
import requests

# 🚀 Sørg for at vi alltid finner .env i rotmappa
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI()

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


@app.get("/ping")
def ping():
    return {"ok": True}


@app.get("/events")
def events(country: str = "US", size: int = 3):
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise HTTPException(500, "Mangler API_KEY (sjekk .env)")
    
    params = {
        "apikey": api_key,
        "countryCode": country,
        "size": size
    }
    
    r = requests.get(TICKETMASTER_URL, params=params, timeout=10)
    if r.status_code == 401:
        raise HTTPException(401, "Feil / ugyldig API key (Consumer Key). Sjekk at 'Discovery API' er aktivert.")
    r.raise_for_status()
    
    data = r.json()
    raw_events = data.get("_embedded", {}).get("events", [])
    simplified = [{"id": e.get("id"), "name": e.get("name")} for e in raw_events]
    
    return {"count": len(simplified), "events": simplified}
