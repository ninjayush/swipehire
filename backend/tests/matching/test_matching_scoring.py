"""Unit tests for deterministic fit scoring (scoring.py).

Tests cover:
- Exact weights (30% skills, 25% experience, 20% domain, 15% trajectory, 10% context)
- Component score bounds [0.0, 100.0] and clamping
- Missing-component handling without score inflation
- Evidence coverage calculation (0.0 - 1.0)
- Deterministic repeatability (identical inputs produce identical scores)
- Missing candidate preferences not penalized as negative
"""

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.scoring import SCORING_WEIGHTS, score_candidate


def test_scoring_weights_exact_values() -> None:
    assert SCORING_WEIGHTS["skills"] == 0.30
    assert SCORING_WEIGHTS["experience"] == 0.25
    assert SCORING_WEIGHTS["role_domain"] == 0.20
    assert SCORING_WEIGHTS["trajectory"] == 0.15
    assert SCORING_WEIGHTS["context"] == 0.10


def test_score_candidate_full_profile() -> None:
    req = JobRequirements(
        title="Senior Backend Engineer",
        seniority="Senior",
        min_experience_years=5.0,
        max_experience_years=8.0,
        locations=["San Francisco, CA"],
        work_modes=["remote", "hybrid"],
        must_have_skills=["Python", "FastAPI"],
        preferred_skills=["Docker", "Kubernetes"],
    )

    person = PersonRecord(
        person_id="p-score-1",
        origin="registered",
        membership_status="registered",
        current_title="Senior Backend Engineer",
        experience_years=6.0,
        location="San Francisco, CA",
        skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
        employment_history=[
            {"company": "Corp A", "title": "Senior Backend Engineer"},
            {"company": "Corp B", "title": "Software Engineer"},
        ],
        candidate_preferences={"work_mode": "hybrid"},
    )

    res = score_candidate(req, person)

    assert 0.0 <= res["fit_score"] <= 100.0
    for comp_name, comp_val in res["component_scores"].items():
        assert 0.0 <= comp_val <= 100.0

    # Skills: matched 2/2 must-have, 1/2 preferred -> 0.70*100 + 0.30*50 = 85.0
    assert res["component_scores"]["skills"] == 85.0
    # Experience: 6.0 in [5.0, 8.0] -> 100.0
    assert res["component_scores"]["experience"] == 100.0
    # Role Domain: exact match -> 100.0
    assert res["component_scores"]["role_domain"] == 100.0
    # All 5 dimensions evidenced
    assert res["evidence_coverage"] == 1.0
    assert len(res["reasons"]) >= 4


def test_sparse_profile_does_not_inflate_fit_score() -> None:
    """Verify that unevidenced components receive 0 and do not inflate the total score."""
    req = JobRequirements(
        title="Lead Architect",
        seniority="Lead",
        min_experience_years=8.0,
        must_have_skills=["Python"],
    )

    # Sparse profile: has 1 skill, but no experience years, no title, no history, no preferences
    sparse_person = PersonRecord(
        person_id="p-sparse-1",
        origin="registered",
        membership_status="registered",
        skills=["Python"],
    )

    res = score_candidate(req, sparse_person)

    # Evidence coverage is low (only skills evidenced)
    assert res["evidence_coverage"] == 0.20
    assert res["component_scores"]["experience"] == 0.0
    assert res["component_scores"]["role_domain"] == 0.0
    # Score is bounded and not inflated by redistributing missing weights
    assert res["fit_score"] < 40.0


def test_missing_preferences_treated_neutrally() -> None:
    req = JobRequirements(
        title="Engineer",
        locations=["Seattle, WA"],
        work_modes=["remote"],
    )
    person_no_pref = PersonRecord(
        person_id="p-nopref-1",
        origin="registered",
        membership_status="registered",
        location=None,
        candidate_preferences={},  # No preferences stated
    )

    res = score_candidate(req, person_no_pref)
    # Neutral context score (50.0), not 0.0
    assert res["component_scores"]["context"] == 50.0


def test_deterministic_repeatability() -> None:
    """Verify scoring produces identical float values across consecutive runs."""
    req = JobRequirements(
        title="Data Engineer",
        must_have_skills=["Python", "SQL"],
        min_experience_years=3.0,
    )
    person = PersonRecord(
        person_id="p-det-1",
        origin="registered",
        membership_status="registered",
        skills=["Python", "SQL", "Spark"],
        current_title="Data Engineer",
        experience_years=4.0,
    )

    res1 = score_candidate(req, person)
    res2 = score_candidate(req, person)

    assert res1["fit_score"] == res2["fit_score"]
    assert res1["component_scores"] == res2["component_scores"]
    assert res1["evidence_coverage"] == res2["evidence_coverage"]
