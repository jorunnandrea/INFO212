import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# kun for å se at vi får 200/ok tilbake
def test_homepage_status_code():
    response = client.get("/")
    assert response.status_code == 200

# ser om det er noe svar på å kalle på arrangemnter eller Bergen 
def test_homepage_content():
    response = client.get("/")
    assert "Arrangementer" in response.text or "Bergen" in response.text

# sjekke format
def test_event_data_structure():
    response = client.get("/")
    assert "<html" in response.text.lower()
    assert "</body>" in response.text.lower()

# Dummy-event som matcher feltene i home.html
DUMMY_EVENT = {
    "name": "Metallica",
    "dates": {"start": {"localDate": "2025-11-20"}},
    "_embedded": {"venues": [{"name": "Bergenhus Festning"}]},
    "images": [{"url": "https://example.com/metallica.jpg"}],
    "url": "https://tickets.example.com/metallica",
}

#hvis det ikke er noen events skal denne meldingen komme
def test_home_shows_empty_message_when_no_events(monkeypatch):
    monkeypatch.setattr("app.main.fetch_events", lambda *a, **k: [])
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Ingen arrangementer funnet" in resp.text

#siden viser nanv, dato, sted, bilde og lenke - henter data fra dummy
def test_home_renders_single_event(monkeypatch):
    monkeypatch.setattr("app.main.fetch_events", lambda *a, **k: [DUMMY_EVENT])
    resp = client.get("/")
    body = resp.text
    assert "Metallica" in body
    assert "2025-11-20" in body
    assert "Bergenhus Festning" in body
    assert "https://example.com/metallica.jpg" in body
    assert "Finn billetter" in body
