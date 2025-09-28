from fastapi.testclient import TestClient
from src.main import app  # adjust import if your FastAPI app is elsewhere

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}  # adapt to your actual response

