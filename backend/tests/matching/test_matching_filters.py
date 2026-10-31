"""Unit tests for deterministic hard filter evaluation (filters.py).

Tests cover:
- Mandatory skill pass and fail (stable reason codes)
- Mandatory qualifications pass and fail
- Experience minimum, maximum, and unknown when required
- Required-field missing (fails closed) vs. optional-field missing (allowed)
- Ambiguous criteria NOT treated as hard filters
- Location dealbreaker pass, fail, and unknown location
- Work mode dealbreaker evaluation
"""

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.filters import evaluate_hard_filters


def test_mandatory_skill_pass() -> None:
    req = JobRequirements(
        title="Python Engineer",
        must_have_skills=["Python", "PostgreSQL"],
    )
    person = PersonRecord(
        person_id="p-001",
        origin="registered",
        membership_status="registered",
        skills=["python", "postgresql", "docker"],
    )
    eligible, reasons, breakdown = evaluate_hard_filters(req, person)
    assert eligible is True
    assert reasons == []
    assert breakdown["skills_passed"] is True


def test_mandatory_skill_fail() -> None:
    req = JobRequirements(
        title="Python Engineer",
        must_have_skills=["Python", "Go"],
    )
    person = PersonRecord(
        person_id="p-002",
        origin="registered",
        membership_status="registered",
        skills=["python"],
    )
    eligible, reasons, breakdown = evaluate_hard_filters(req, person)
    assert eligible is False
    assert any("missing_mandatory_skill: Go" in r for r in reasons)
    assert breakdown["skills_passed"] is False


def test_mandatory_qualification_pass_and_fail() -> None:
    req = JobRequirements(
        title="Data Scientist",
        mandatory_qualifications=["B.S. in Computer Science"],
    )
    # 1. Matching candidate
    p_pass = PersonRecord(
        person_id="p-003",
        origin="registered",
        membership_status="registered",
        education=[{"degree": "B.S.", "field_of_study": "Computer Science"}],
    )
    eligible_pass, reasons_pass, _ = evaluate_hard_filters(req, p_pass)
    assert eligible_pass is True
    assert reasons_pass == []

    # 2. Candidate without required degree
    p_fail = PersonRecord(
        person_id="p-004",
        origin="registered",
        membership_status="registered",
        education=[{"degree": "B.A.", "field_of_study": "History"}],
    )
    eligible_fail, reasons_fail, _ = evaluate_hard_filters(req, p_fail)
    assert eligible_fail is False
    assert any("missing_mandatory_qualification" in r for r in reasons_fail)


def test_experience_bounds_evaluation() -> None:
    req = JobRequirements(
        title="Senior Developer",
        min_experience_years=5.0,
        max_experience_years=10.0,
    )

    # 1. Candidate within range
    p_ok = PersonRecord(
        person_id="p-exp-1",
        origin="registered",
        membership_status="registered",
        experience_years=6.5,
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_ok)
    assert eligible is True

    # 2. Candidate below minimum
    p_under = PersonRecord(
        person_id="p-exp-2",
        origin="registered",
        membership_status="registered",
        experience_years=3.0,
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_under)
    assert eligible is False
    assert "experience_below_minimum" in reasons

    # 3. Candidate above maximum
    p_over = PersonRecord(
        person_id="p-exp-3",
        origin="registered",
        membership_status="registered",
        experience_years=14.0,
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_over)
    assert eligible is False
    assert "experience_above_maximum" in reasons

    # 4. Unknown experience when minimum is mandatory
    p_unknown = PersonRecord(
        person_id="p-exp-4",
        origin="registered",
        membership_status="registered",
        experience_years=None,
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_unknown)
    assert eligible is False
    assert "experience_unknown_required" in reasons


def test_required_field_missing_fails_closed() -> None:
    req = JobRequirements(
        title="Role",
        required_fields=["availability", "salary"],
    )

    # Candidate missing both
    p_missing = PersonRecord(
        person_id="p-req-1",
        origin="registered",
        membership_status="registered",
        candidate_preferences={},
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_missing)
    assert eligible is False
    assert "availability_unknown_required" in reasons
    assert "salary_unknown_required" in reasons


def test_missing_optional_field_does_not_exclude() -> None:
    # Notice: preferred skills, salary, availability are NOT in required_fields
    req = JobRequirements(
        title="Role",
        must_have_skills=["Python"],
        preferred_skills=["Kubernetes", "Rust"],
        unknown_or_needs_confirmation=["Prefer local candidate if possible"],
    )

    p_optional = PersonRecord(
        person_id="p-opt-1",
        origin="registered",
        membership_status="registered",
        skills=["Python"],  # misses Kubernetes and Rust
        candidate_preferences={},  # missing salary/availability
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_optional)
    assert eligible is True
    assert reasons == []


def test_location_dealbreaker_evaluation() -> None:
    req = JobRequirements(
        title="Role",
        dealbreakers=["Must reside in California"],
    )

    # 1. Matching candidate
    p_ca = PersonRecord(
        person_id="p-loc-1",
        origin="registered",
        membership_status="registered",
        location="San Francisco, California",
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_ca)
    assert eligible is True

    # 2. Non-matching candidate
    p_ny = PersonRecord(
        person_id="p-loc-2",
        origin="registered",
        membership_status="registered",
        location="New York, NY",
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_ny)
    assert eligible is False
    assert "location_mismatch" in reasons

    # 3. Unknown location under mandatory dealbreaker
    p_unknown = PersonRecord(
        person_id="p-loc-3",
        origin="registered",
        membership_status="registered",
        location=None,
    )
    eligible, reasons, _ = evaluate_hard_filters(req, p_unknown)
    assert eligible is False
    assert "location_unknown_required" in reasons
