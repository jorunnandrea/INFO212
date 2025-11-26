import os
import requests

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events"

def fetch_events(startDate=None, endDate=None, classification=None, keyword=None, size=200):
    api_key = os.getenv("API_KEY")
    if not api_key:
        # Log or handle missing key if needed
        return []

    params = {
        "apikey": api_key,
        "countryCode": "NO",
        "latlong": "60.39299,5.32415",  # Bergen, Norway
        "radius": "20",
        "unit": "km",
        "locale": "*",
        "size": size,
        "sort": "date,asc",
    }
    
    if startDate and endDate:
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
        events = data.get("_embedded", {}).get("events", [])
        return events if isinstance(events, list) else []
    except requests.RequestException as e:
        # Optional: print(e) for debugging
        return []