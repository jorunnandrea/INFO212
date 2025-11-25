import os
import requests

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"

def fetch_events(startDate=None, endDate=None, classification=None, keyword=None, size=200):
    api_key = os.environ.get("API_KEY")
    if not api_key: #hvis det ikke er noe å hente så kommer det en tom liste - kankje bedre med en feilmelding? 
        return []

    #parameter for å hente info fra APIet
    params = {
        "apikey": api_key,
        "countryCode": "NO",
        "latlong": "60.39299,5.32415",
        "radius": "20",
        "unit": "km",
        "locale": "*",
        "size": size,
        "sort": "date,asc",
    }
    
    if startDate and endDate:cd HTML/INFO212/fastapi_mvp
        params["startDateTime"] = f"{startDate}T00:00:00Z"
        params["endDateTime"] = f"{endDate}T23:59:59Z"

    if classification:
        params["classificationName"] = classification

    if keyword:
        params["keyword"] = keyword

    try:
        response = requests.get(TICKETMASTER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return (data.get("_embedded") or {}).get("events", []) or []
    except requests.RequestException:
        return []