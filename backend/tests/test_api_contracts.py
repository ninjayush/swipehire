import pytest
from app.database.schemas import (
    JobRequirements,
    PersonRecord,
    CandidateEvaluation,
    CandidateDeckResponse,
)

def test_job_requirements_contract():
    req = JobRequirements(
        title="Full Stack Engineer",
        min_experience_years=3.5,
        must_have_skills=["Python", "FastAPI"],
        locations=["Remote"],
        work_modes=["remote"]
    )
    assert req.title == "Full Stack Engineer"
    assert req.min_experience_years == 3.5
    assert "Python" in req.must_have_skills
    assert isinstance(req.dealbreakers, list)

def test_person_record_contract():
    record = PersonRecord(
        person_id="p-12345",
        profile_url="https://linkedin.com/in/johndoe",
        origin="crustdata_sourced",
        membership_status="not_registered",
        name="John Doe",
        skills=["Python", "SQL"]
    )
    assert record.origin == "crustdata_sourced"
    assert record.membership_status == "not_registered"
    assert record.name == "John Doe"
    assert "SQL" in record.skills

def test_candidate_deck_contract():
    deck = CandidateDeckResponse(
        job_id="job-1",
        match_run_id="run-1",
        status="completed",
        total_candidates=10,
        direct_count=7,
        adjacent_count=2,
        excluded_count=1,
        cards=[]
    )
    assert deck.total_candidates == 10
    assert deck.status == "completed"
