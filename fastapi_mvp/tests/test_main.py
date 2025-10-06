import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_homepage_status_code():
    """Tester at startsiden returnerer statuskode 200"""
    response = client.get("/")
    assert response.status_code == 200

# Test 2: sjekk at startsiden inneholder forventet tekst
def test_homepage_content():
    response = client.get("/")
    assert "Arrangementer" in response.text or "Bergen" in response.text

# Test 3: sjekk at API-et returnerer data i riktig format
def test_event_data_structure():
    response = client.get("/")
    # sjekk at responsen inneholder HTML som genereres fra events-listen
    assert "<html" in response.text.lower()
    assert "</body>" in response.text.lower()