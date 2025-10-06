import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


#første test er bare for å se at vi får 200 tilbake
def test_homepage_status_code():
    response = client.get("/")
    assert response.status_code == 200

# ser om vi får svar på arrangemnter eller Bergen
def test_homepage_content():
    response = client.get("/")
    assert "Arrangementer" in response.text or "Bergen" in response.text

#se på formantet vi mottar data i
def test_event_data_structure():
    response = client.get("/")
    assert "<html" in response.text.lower()
    assert "</body>" in response.text.lower()