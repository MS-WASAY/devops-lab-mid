from fastapi.testclient import TestClient
from app import app, submissions

client = TestClient(app)

def setup_function():
    submissions.clear()

def test_valid_submission():
    response = client.post("/submit", data={
        "name": "Ahmed Raza",
        "reg_no": "FA23-BCS-045",
        "title": "Lab Mid",
        "url": "https://github.com/ahmed/devops-mid"
    })
    assert response.status_code == 200
    assert "Ahmed Raza" in response.text
    assert "FA23-BCS-045" in response.text
    assert len(submissions) == 1

def test_missing_registration_number():
    response = client.post("/submit", data={
        "name": "Ahmed Raza",
        "reg_no": "",
        "title": "Lab Mid",
        "url": "https://github.com/ahmed/devops-mid"
    })
    assert response.status_code == 400
    assert "Validation Error" in response.text
    assert len(submissions) == 0

def test_invalid_submission_url():
    response = client.post("/submit", data={
        "name": "Ahmed Raza",
        "reg_no": "FA23-BCS-045",
        "title": "Lab Mid",
        "url": "not-a-valid-url"
    })
    assert response.status_code == 400
    assert len(submissions) == 0
