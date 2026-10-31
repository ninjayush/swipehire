import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"

def test_list_jobs(client):
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data

def test_resolve_company(client):
    response = client.post("/api/companies/resolve", json={"company_name": "Demo Corp", "domain": "democorp.io"})
    assert response.status_code == 200
    data = response.json()
    assert "company_id" in data
    assert data["name"] == "Demo Corp"

def test_create_and_fetch_job(client):
    # Fetch demo company id
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Demo Corp"})
    company_id = comp_res.json()["company_id"]

    job_res = client.post("/api/jobs", json={
        "company_id": company_id,
        "input_type": "structured",
        "requirements": {
            "title": "Backend Python Lead",
            "must_have_skills": ["Python", "FastAPI"]
        }
    })
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["requirements"]["title"] == "Backend Python Lead"

def test_candidate_registration_and_action(client):
    # Register candidate
    reg_res = client.post("/api/candidates/register", json={
        "email": "test_candidate@swipehire.local",
        "name": "Jordan Candidate",
        "profile_url": "https://linkedin.com/in/jordancandidate",
        "candidate_preferences": {"role": "Backend"}
    })
    assert reg_res.status_code == 200
    person_id = reg_res.json()["person"]["person_id"]

    # Fetch jobs
    jobs_res = client.get("/api/jobs")
    job_id = jobs_res.json()["jobs"][0]["job_id"]

    # Shortlist candidate
    action_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "shortlist"
    })
    assert action_res.status_code == 200
    action_data = action_res.json()
    assert action_data["status"] == "success"
    assert action_data["interest_request_id"] is not None

    # Candidate responds to interest request
    interest_id = action_data["interest_request_id"]
    respond_res = client.post(f"/api/interests/{interest_id}/respond", json={
        "response": "accept"
    })
    assert respond_res.status_code == 200
    assert respond_res.json()["match_id"] is not None

    # Verify match appears in GET /api/matches
    matches_res = client.get("/api/matches")
    assert matches_res.status_code == 200
    matches = matches_res.json()["matches"]
    assert any(m["person_id"] == person_id for m in matches)
