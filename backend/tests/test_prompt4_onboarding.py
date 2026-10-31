import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.db import Base, get_db
from app.models.person import Person
from app.models.company import Company
from app.services.person_service import PersonService, normalize_profile_url

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# -------------------------------------------------------------
# 1. Company Resolution & Ambiguity
# -------------------------------------------------------------
def test_company_resolution_sequence(client):
    res = client.post("/api/companies/resolve", json={"company_name": "Acme Inc", "domain": "acme.com"})
    assert res.status_code == 200
    data = res.json()
    assert "company_id" in data
    assert bool(data["name"])
    assert data["domain"] == "acme.com"
    assert isinstance(data["ambiguous_options"], list)

def test_company_resolution_missing_inputs(client):
    res = client.post("/api/companies/resolve", json={})
    assert res.status_code == 400

# -------------------------------------------------------------
# 2. Person URL Validation & Normalization
# -------------------------------------------------------------
def test_valid_profile_urls():
    assert normalize_profile_url("https://www.linkedin.com/in/john-doe/") == "https://linkedin.com/in/john-doe"
    assert normalize_profile_url("http://github.com/torvalds") == "http://github.com/torvalds"

def test_invalid_profile_urls():
    with pytest.raises(ValueError):
        normalize_profile_url("not-a-valid-domain")

def test_enrich_candidate_invalid_url(client):
    res = client.post("/api/candidates/enrich", json={"profile_url": "ftp://malformed-url"})
    assert res.status_code == 400

# -------------------------------------------------------------
# 3. Registration Attaches to Sourced Person (No Duplicates)
# -------------------------------------------------------------
def test_sourced_person_registration_deduplication(client):
    test_url = "https://linkedin.com/in/marcus-sourced"

    # 1. First candidate is registered / enriched as sourced
    reg1 = client.post("/api/candidates/register", json={
        "name": "Marcus Sourced",
        "profile_url": test_url
    })
    assert reg1.status_code == 200
    p1_id = reg1.json()["person"]["person_id"]

    # 2. Candidate registers later with email and preferences
    reg2 = client.post("/api/candidates/register", json={
        "email": "marcus@example.com",
        "profile_url": test_url,
        "candidate_preferences": {"role": "Senior Engineer"}
    })
    assert reg2.status_code == 200
    p2_id = reg2.json()["person"]["person_id"]

    # Identical person ID: NO DUPLICATE CREATED
    assert p1_id == p2_id
    assert reg2.json()["person"]["membership_status"] == "registered"

# -------------------------------------------------------------
# 4. Resume Upload Boundary (Type, Size, Traversal, Parser-Not-Ready)
# -------------------------------------------------------------
def test_resume_upload_success_and_parser_status(client):
    # Register candidate first
    cand_res = client.post("/api/candidates/register", json={
        "name": "Resume Candidate",
        "email": "resume_cand@example.com",
        "profile_url": "https://linkedin.com/in/resume-cand"
    })
    person_id = cand_res.json()["person"]["person_id"]

    # Upload valid .pdf
    fake_pdf = io.BytesIO(b"%PDF-1.4 Mock PDF Content")
    res = client.post(
        f"/api/candidates/{person_id}/resume",
        files={"file": ("my_resume.pdf", fake_pdf, "application/pdf")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["filename"] == "my_resume.pdf"
    # Local filesystem path is NEVER exposed in response
    assert "file_path" not in data
    # Reports integration boundary status accurately without fabricating
    assert "parser_status" in data

def test_resume_upload_unsupported_type(client):
    # Register candidate
    cand_res = client.post("/api/candidates/register", json={"name": "Test User", "profile_url": "https://linkedin.com/in/test-unsupported"})
    person_id = cand_res.json()["person"]["person_id"]

    # Attempt to upload .exe or .png
    fake_exe = io.BytesIO(b"binary payload")
    res = client.post(
        f"/api/candidates/{person_id}/resume",
        files={"file": ("malicious.exe", fake_exe, "application/octet-stream")}
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]

def test_resume_upload_oversized(client):
    cand_res = client.post("/api/candidates/register", json={"name": "Oversize User", "profile_url": "https://linkedin.com/in/test-oversize"})
    person_id = cand_res.json()["person"]["person_id"]

    # 6MB payload (exceeds 5MB limit)
    large_content = b"A" * (6 * 1024 * 1024)
    res = client.post(
        f"/api/candidates/{person_id}/resume",
        files={"file": ("large_resume.pdf", io.BytesIO(large_content), "application/pdf")}
    )
    assert res.status_code == 400
    assert "exceeds maximum allowed size" in res.json()["detail"]

def test_resume_upload_path_traversal_sanitization(client):
    cand_res = client.post("/api/candidates/register", json={"name": "Traversal User", "profile_url": "https://linkedin.com/in/test-traversal"})
    person_id = cand_res.json()["person"]["person_id"]

    fake_doc = io.BytesIO(b"Doc content")
    res = client.post(
        f"/api/candidates/{person_id}/resume",
        files={"file": ("../../../../etc/passwd.docx", fake_doc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )
    assert res.status_code == 200
    # Directory traversal prefix was stripped securely
    assert ".." not in res.json()["filename"]
