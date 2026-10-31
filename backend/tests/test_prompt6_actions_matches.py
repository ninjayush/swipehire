import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.action_service import ActionService

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# -------------------------------------------------------------
# 1. Recruiter Actions: Shortlist Registered vs Sourced Non-Member
# -------------------------------------------------------------
def test_shortlist_registered_candidate_creates_interest_request(client):
    # 1. Setup company and job
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Actions Test Corp"})
    comp_id = comp_res.json()["company_id"]
    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {"title": "Full Stack Dev"}
    })
    job_id = job_res.json()["job_id"]

    # 2. Register candidate
    cand_res = client.post("/api/candidates/register", json={
        "name": "Registered Alice",
        "email": "alice_registered@example.com",
        "profile_url": "https://linkedin.com/in/alice-reg"
    })
    person_id = cand_res.json()["person"]["person_id"]

    # 3. Recruiter shortlists candidate
    action_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "shortlist"
    })
    assert action_res.status_code == 200
    data = action_res.json()
    assert data["status"] == "success"
    assert data["membership_status"] == "registered"
    # InterestRequest IS created for registered candidates
    assert data["interest_request_id"] is not None

def test_shortlist_sourced_non_member_is_internal_only(client):
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Actions Test Corp"})
    comp_id = comp_res.json()["company_id"]
    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {"title": "DevOps Engineer"}
    })
    job_id = job_res.json()["job_id"]

    # Register sourced person directly (not registered as member)
    import uuid
    sourced_id = f"sourced-nonmember-{uuid.uuid4().hex[:8]}"
    from app.database.db import SessionLocal
    from app.models.person import Person
    db = SessionLocal()
    p = Person(
        id=sourced_id,
        name="Sourced Non-Member",
        origin="crustdata_sourced",
        membership_status="not_registered"
    )
    db.add(p)
    db.commit()
    db.close()

    # Shortlist sourced non-member
    action_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": sourced_id,
        "action": "shortlist"
    })
    assert action_res.status_code == 200
    data = action_res.json()
    assert data["status"] == "success"
    assert data["membership_status"] == "not_registered"
    # No InterestRequest created for non-members
    assert data["interest_request_id"] is None

def test_pass_and_save_actions(client):
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Actions Test Corp"})
    comp_id = comp_res.json()["company_id"]
    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {"title": "QA Engineer"}
    })
    job_id = job_res.json()["job_id"]

    cand_res = client.post("/api/candidates/register", json={
        "name": "Candidate Bob",
        "profile_url": "https://linkedin.com/in/cand-bob"
    })
    person_id = cand_res.json()["person"]["person_id"]

    # Action: save
    save_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "save"
    })
    assert save_res.status_code == 200
    assert save_res.json()["action"] == "save"

    # Action: pass
    pass_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "pass"
    })
    assert pass_res.status_code == 200
    assert pass_res.json()["action"] == "pass"

# -------------------------------------------------------------
# 2. Candidate Interest Response & Idempotent Mutual Match
# -------------------------------------------------------------
def test_interest_accept_and_idempotent_match(client):
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Match Test Corp"})
    comp_id = comp_res.json()["company_id"]
    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {"title": "Mobile Engineer"}
    })
    job_id = job_res.json()["job_id"]

    cand_res = client.post("/api/candidates/register", json={
        "name": "Registered Candidate Eve",
        "email": "eve@example.com",
        "profile_url": "https://linkedin.com/in/eve-mobile"
    })
    person_id = cand_res.json()["person"]["person_id"]

    # Recruiter shortlists
    action_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "shortlist"
    })
    interest_id = action_res.json()["interest_request_id"]

    # Candidate accepts -> Mutual Match created
    resp_res = client.post(f"/api/interests/{interest_id}/respond", json={"response": "accept"})
    assert resp_res.status_code == 200
    match_id = resp_res.json()["match_id"]
    assert match_id is not None

    # Idempotent: Second accept returns the SAME match_id without creating duplicate
    resp_res2 = client.post(f"/api/interests/{interest_id}/respond", json={"response": "accept"})
    assert resp_res2.status_code == 200
    assert resp_res2.json()["match_id"] == match_id

    # Verify match appears in GET /api/matches
    matches_res = client.get("/api/matches")
    assert matches_res.status_code == 200
    match_list = matches_res.json()["matches"]
    matches_for_eve = [m for m in match_list if m["person_id"] == person_id and m["job_id"] == job_id]
    assert len(matches_for_eve) == 1
    assert matches_for_eve[0]["match_id"] == match_id

def test_interest_reject_creates_no_match(client):
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Match Test Corp"})
    comp_id = comp_res.json()["company_id"]
    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {"title": "Security Analyst"}
    })
    job_id = job_res.json()["job_id"]

    cand_res = client.post("/api/candidates/register", json={
        "name": "Candidate Dave",
        "email": "dave@example.com",
        "profile_url": "https://linkedin.com/in/dave-sec"
    })
    person_id = cand_res.json()["person"]["person_id"]

    # Recruiter shortlists
    action_res = client.post(f"/api/jobs/{job_id}/actions", json={
        "person_id": person_id,
        "action": "shortlist"
    })
    interest_id = action_res.json()["interest_request_id"]

    # Candidate rejects
    resp_res = client.post(f"/api/interests/{interest_id}/respond", json={"response": "reject"})
    assert resp_res.status_code == 200
    assert resp_res.json()["match_id"] is None

# -------------------------------------------------------------
# 3. Privacy & Salary Visibility Sanitization
# -------------------------------------------------------------
def test_salary_hidden_when_visibility_is_false():
    private_profile = {
        "name": "Private Candidate",
        "candidate_preferences": {
            "salary_visible": False,
            "expected_salary": 180000,
            "current_salary": 150000,
            "location_preference": "Remote"
        }
    }

    sanitized = ActionService.sanitize_candidate_profile_for_viewer(private_profile)
    prefs = sanitized["candidate_preferences"]
    assert "expected_salary" not in prefs
    assert "current_salary" not in prefs
    assert prefs["salary_visible"] is False
    assert prefs["location_preference"] == "Remote"
