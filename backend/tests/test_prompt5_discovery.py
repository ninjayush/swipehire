import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.db import Base, get_db
from app.models.job import JobRole
from app.models.company import Company
from app.models.person import Person
from app.models.match import MatchRun, CandidateMatch
from app.database.schemas import JobRequirements, PersonRecord, CandidateEvaluation
from app.services.discovery_service import DiscoveryService, fallback_build_candidate_deck

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# -------------------------------------------------------------
# 1. Structured & JD Job Creation and PATCH Confirmation
# -------------------------------------------------------------
def test_structured_job_creation(client):
    # Resolve company
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Acme Corp"})
    comp_id = comp_res.json()["company_id"]

    # Structured creation
    res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {
            "title": "Senior Python Architect",
            "must_have_skills": ["Python", "FastAPI", "SQLAlchemy"],
            "min_experience_years": 5.0
        }
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["requirements"]["title"] == "Senior Python Architect"

def test_jd_mode_and_patch_confirmation(client):
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Acme Corp"})
    comp_id = comp_res.json()["company_id"]

    # JD Mode sets status to needs_confirmation
    jd_text = "Looking for Senior React Specialist\nMust have 4 years experience with Next.js and TypeScript."
    res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "jd",
        "raw_jd": jd_text
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "needs_confirmation"
    job_id = data["job_id"]

    # Recruiter reviews and confirms with PATCH
    patch_res = client.patch(f"/api/jobs/{job_id}", json={
        "status": "active",
        "requirements": {
            "preferred_skills": ["TailwindCSS"]
        }
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "active"
    assert "TailwindCSS" in patch_res.json()["requirements"]["preferred_skills"]

# -------------------------------------------------------------
# 2. Matching Deck Bridge and Dealbreaker Exclusion
# -------------------------------------------------------------
def test_matching_deck_evaluation_and_exclusions():
    req = JobRequirements(
        title="Backend Lead",
        min_experience_years=4.0,
        must_have_skills=["Python", "Docker"]
    )

    candidates = [
        # Candidate 1: Meets skills & experience -> DIRECT FIT
        PersonRecord(
            person_id="p-1",
            origin="registered",
            membership_status="registered",
            name="Alice Direct",
            skills=["Python", "Docker", "AWS"],
            experience_years=6.0
        ),
        # Candidate 2: Partial skills -> ADJACENT FIT
        PersonRecord(
            person_id="p-2",
            origin="crustdata_sourced",
            membership_status="not_registered",
            name="Bob Adjacent",
            skills=["Python"],
            experience_years=4.5
        ),
        # Candidate 3: Fails min experience -> EXCLUDED
        PersonRecord(
            person_id="p-3",
            origin="registered",
            membership_status="registered",
            name="Charlie Junior",
            skills=["Python", "Docker"],
            experience_years=1.5
        )
    ]

    displayed, excluded = fallback_build_candidate_deck(req, candidates, deck_size=20)

    # 2 displayed, 1 excluded
    assert len(displayed) == 2
    assert len(excluded) == 1

    # Alice is direct and rank 1
    assert displayed[0].person_id == "p-1"
    assert displayed[0].fit_type == "direct"
    assert displayed[0].rank == 1

    # Bob is adjacent
    assert displayed[1].person_id == "p-2"
    assert displayed[1].fit_type == "adjacent"

    # Charlie is excluded with reasons
    assert excluded[0].person_id == "p-3"
    assert excluded[0].eligible is False
    assert any("Requires 4.0+ yrs" in r for r in excluded[0].exclusion_reasons)

# -------------------------------------------------------------
# 3. Discovery Pipeline End-to-End & Deck Retrieval
# -------------------------------------------------------------
def test_discovery_pipeline_and_deck_endpoint(client):
    # Setup job
    comp_res = client.post("/api/companies/resolve", json={"company_name": "Discovery Test Corp"})
    comp_id = comp_res.json()["company_id"]

    job_res = client.post("/api/jobs", json={
        "company_id": comp_id,
        "input_type": "structured",
        "requirements": {
            "title": "Cloud Architect",
            "must_have_skills": ["AWS", "Terraform"]
        }
    })
    job_id = job_res.json()["job_id"]

    # Register candidate to ensure local candidate pool
    client.post("/api/candidates/register", json={
        "name": "Local Cloud Eng",
        "email": "cloud_eng@example.com",
        "candidate_preferences": {"skills": ["AWS", "Terraform"]}
    })

    # Trigger discovery
    disc_res = client.post(f"/api/jobs/{job_id}/discover")
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert disc_data["status"] == "completed"
    assert "cards" in disc_data
    assert "direct_count" in disc_data

    # Fetch deck via GET
    deck_res = client.get(f"/api/jobs/{job_id}/deck")
    assert deck_res.status_code == 200
    deck_data = deck_res.json()
    assert deck_data["status"] == "completed"
    assert deck_data["job_id"] == job_id
