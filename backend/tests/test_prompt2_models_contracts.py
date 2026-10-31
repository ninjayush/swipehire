import pytest
import uuid
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database.db import Base
from app.database.schemas import (
    JobRequirements,
    PersonRecord,
    CandidateEvaluation,
    CandidateDeckResponse,
    EvidenceItem as EvidenceItemSchema,
)
from app.models.user import User, CandidateProfile
from app.models.person import Person
from app.models.company import Company
from app.models.job import JobRole
from app.models.match import MatchRun, CandidateMatch, InterestRequest, Match, EvidenceItem

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

# -------------------------------------------------------------
# 1. Pydantic Contract Validation and Defaults
# -------------------------------------------------------------
def test_job_requirements_validation():
    # Valid model
    job = JobRequirements(title="Backend Engineer", min_experience_years=2.0)
    assert job.min_experience_years == 2.0
    assert job.locations == []
    assert job.must_have_skills == []

    # Negative experience should fail
    with pytest.raises(ValidationError):
        JobRequirements(title="Backend Engineer", min_experience_years=-1.0)

def test_candidate_evaluation_score_bounds():
    # Valid score
    ev = CandidateEvaluation(person_id="p-1", eligible=True, fit_score=85.5, rank=1)
    assert ev.fit_score == 85.5
    assert ev.rank == 1

    # Fit score > 100 should fail
    with pytest.raises(ValidationError):
        CandidateEvaluation(person_id="p-1", eligible=True, fit_score=105.0)

    # Fit score < 0 should fail
    with pytest.raises(ValidationError):
        CandidateEvaluation(person_id="p-1", eligible=True, fit_score=-5.0)

    # Rank < 1 should fail
    with pytest.raises(ValidationError):
        CandidateEvaluation(person_id="p-1", eligible=True, rank=0)

# -------------------------------------------------------------
# 2. Person / User Separation & Unique Constraints
# -------------------------------------------------------------
def test_person_user_separation(db_session):
    # Sourced candidate exists as Person without User or CandidateProfile
    person = Person(
        id=str(uuid.uuid4()),
        crustdata_person_id=99999,
        profile_url="https://linkedin.com/in/sourceduser",
        origin="crustdata_sourced",
        membership_status="not_registered",
        name="Sourced Professional"
    )
    db_session.add(person)
    db_session.commit()

    assert db_session.query(Person).count() == 1
    assert db_session.query(User).count() == 0
    assert db_session.query(CandidateProfile).count() == 0

def test_unique_crustdata_id_constraint(db_session):
    p1 = Person(id="p-1", crustdata_person_id=12345, name="Person 1")
    p2 = Person(id="p-2", crustdata_person_id=12345, name="Person 2")
    db_session.add(p1)
    db_session.commit()

    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_unique_profile_url_constraint(db_session):
    p1 = Person(id="p-1", profile_url="https://linkedin.com/in/sameurl", name="Person 1")
    p2 = Person(id="p-2", profile_url="https://linkedin.com/in/sameurl", name="Person 2")
    db_session.add(p1)
    db_session.commit()

    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

# -------------------------------------------------------------
# 3. JobRequirements Persistence Round-Trip
# -------------------------------------------------------------
def test_job_requirements_round_trip(db_session):
    company = Company(id="comp-1", name="Tech Corp")
    db_session.add(company)
    db_session.commit()

    req = JobRequirements(
        title="ML Engineer",
        seniority="Senior",
        min_experience_years=5.0,
        must_have_skills=["PyTorch", "Python"],
        locations=["San Francisco, CA"]
    )

    job = JobRole(
        id="job-1",
        company_id=company.id,
        title=req.title,
        requirements=req.model_dump()
    )
    db_session.add(job)
    db_session.commit()

    fetched = db_session.query(JobRole).filter(JobRole.id == "job-1").first()
    restored_req = JobRequirements(**fetched.requirements)

    assert restored_req.title == "ML Engineer"
    assert restored_req.min_experience_years == 5.0
    assert "PyTorch" in restored_req.must_have_skills

# -------------------------------------------------------------
# 4. Relationships: Job -> MatchRun -> CandidateMatch -> EvidenceItem
# -------------------------------------------------------------
def test_model_relationships(db_session):
    company = Company(id="c-1", name="Acme Corp")
    job = JobRole(id="j-1", company_id="c-1", title="DevOps Engineer", requirements={})
    person = Person(id="p-1", name="Alice Dev", origin="crustdata_sourced", membership_status="not_registered")
    match_run = MatchRun(id="mr-1", job_id="j-1", status="completed", total_candidates=1, direct_count=1)
    
    cand_match = CandidateMatch(
        id="cm-1",
        job_id="j-1",
        match_run_id="mr-1",
        person_id="p-1",
        eligible=True,
        fit_score=92.0,
        fit_type="direct",
        rank=1
    )

    evidence = EvidenceItem(
        id="ev-1",
        candidate_match_id="cm-1",
        criterion="Kubernetes experience",
        evidence_text="Managed EKS cluster for 3 years",
        confidence_score=0.95
    )

    db_session.add_all([company, job, person, match_run, cand_match, evidence])
    db_session.commit()

    # Query relationships
    queried_job = db_session.query(JobRole).filter(JobRole.id == "j-1").first()
    assert len(queried_job.match_runs) == 1
    assert len(queried_job.candidate_matches) == 1

    queried_cm = db_session.query(CandidateMatch).filter(CandidateMatch.id == "cm-1").first()
    assert queried_cm.fit_score == 92.0
    assert len(queried_cm.evidence_items) == 1
    assert queried_cm.evidence_items[0].criterion == "Kubernetes experience"
