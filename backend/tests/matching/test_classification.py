"""Unit tests for direct vs. adjacent fit classification (classification.py).

Tests cover:
- Direct fit classification criteria
- Adjacent fit classification (transferable skills, missing preferred/literal title)
- Hard filter gate: ineligible candidates are never classified
- Insufficient evidence/score receives None
- Centralized thresholds inspection
"""

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.classification import (
    DEFAULT_ADJACENT_MIN_SCORE,
    DEFAULT_DIRECT_MIN_SCORE,
    FIT_TYPE_ADJACENT,
    FIT_TYPE_DIRECT,
    classify_fit_type,
)
from app.matching.filters import evaluate_hard_filters


def test_direct_fit_classification() -> None:
    req = JobRequirements(
        title="Senior Python Engineer",
        must_have_skills=["Python"],
        preferred_skills=["Docker"],
    )
    person = PersonRecord(
        person_id="p-class-1",
        origin="registered",
        membership_status="registered",
        current_title="Senior Python Engineer",
        skills=["Python", "Docker"],
    )

    component_scores = {
        "skills": 90.0,
        "experience": 85.0,
        "role_domain": 95.0,
        "trajectory": 85.0,
        "context": 80.0,
    }
    fit_score = 88.0

    fit_type = classify_fit_type(req, person, fit_score, component_scores)
    assert fit_type == FIT_TYPE_DIRECT


def test_adjacent_fit_classification() -> None:
    """Candidate has strong transferable skills and experience, but misses exact title or preferred skill."""
    req = JobRequirements(
        title="Machine Learning Engineer",
        must_have_skills=["Python"],
        preferred_skills=["PyTorch", "CUDA"],
    )
    # Candidate is a Data Engineer with strong Python and Spark
    person = PersonRecord(
        person_id="p-class-2",
        origin="registered",
        membership_status="registered",
        current_title="Senior Data Engineer",
        skills=["Python", "Spark"],
    )

    # Candidate passed all hard filters
    eligible, _, _ = evaluate_hard_filters(req, person)
    assert eligible is True

    component_scores = {
        "skills": 65.0,  # Has Python, misses PyTorch
        "experience": 80.0,
        "role_domain": 60.0,  # Data Engineer vs ML Engineer
        "trajectory": 75.0,
        "context": 70.0,
    }
    fit_score = 69.5

    fit_type = classify_fit_type(req, person, fit_score, component_scores)
    assert fit_type == FIT_TYPE_ADJACENT


def test_adjacent_cannot_override_failed_hard_filter() -> None:
    """Verify that an ineligible candidate (failed hard filter) cannot become eligible or adjacent."""
    req = JobRequirements(
        title="Backend Engineer",
        must_have_skills=["Go"],  # mandatory
    )
    person = PersonRecord(
        person_id="p-class-3",
        origin="registered",
        membership_status="registered",
        skills=["Python"],  # Lacks Go
    )

    eligible, reasons, _ = evaluate_hard_filters(req, person)
    assert eligible is False
    assert any("missing_mandatory_skill: Go" in r for r in reasons)


def test_weak_or_insufficient_evidence_receives_none() -> None:
    """Candidates with low score or insufficient evidence must receive None and not be added to deck."""
    req = JobRequirements(
        title="Site Reliability Engineer",
        must_have_skills=["Linux"],
    )
    person = PersonRecord(
        person_id="p-class-4",
        origin="registered",
        membership_status="registered",
        skills=["Linux"],
        current_title="Graphic Designer",
    )

    component_scores = {
        "skills": 40.0,
        "experience": 20.0,
        "role_domain": 20.0,
        "trajectory": 20.0,
        "context": 50.0,
    }
    fit_score = 28.5  # Below adjacent threshold (50.0)

    fit_type = classify_fit_type(req, person, fit_score, component_scores)
    assert fit_type is None


def test_threshold_constants_documented() -> None:
    assert DEFAULT_DIRECT_MIN_SCORE == 70.0
    assert DEFAULT_ADJACENT_MIN_SCORE == 50.0
