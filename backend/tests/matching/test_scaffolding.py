"""Scaffolding and integration boundary tests for app.matching."""

import pytest

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.classification import (
    DEFAULT_ADJACENT_MIN_SCORE,
    DEFAULT_DIRECT_MIN_SCORE,
    FIT_TYPE_ADJACENT,
    FIT_TYPE_DIRECT,
    classify_fit_type,
)
from app.matching.deck import MAX_ADJACENT_RATIO, build_candidate_deck
from app.matching.filters import evaluate_hard_filters
from app.matching.normalization import (
    normalize_location,
    normalize_skill,
    normalize_skills,
)
from app.matching.scoring import SCORING_WEIGHTS, score_candidate


def test_matching_module_exports() -> None:
    """Verify all expected public interfaces and constants are importable."""
    assert callable(build_candidate_deck)
    assert callable(evaluate_hard_filters)
    assert callable(score_candidate)
    assert callable(classify_fit_type)
    assert FIT_TYPE_DIRECT == "direct"
    assert FIT_TYPE_ADJACENT == "adjacent"
    assert MAX_ADJACENT_RATIO == 0.20


def test_scoring_weights_sum_to_one() -> None:
    """Verify component weights sum to 1.0 (100%)."""
    total_weight = sum(SCORING_WEIGHTS.values())
    assert pytest.approx(total_weight) == 1.0
    assert SCORING_WEIGHTS["skills"] == 0.30
    assert SCORING_WEIGHTS["experience"] == 0.25
    assert SCORING_WEIGHTS["role_domain"] == 0.20
    assert SCORING_WEIGHTS["trajectory"] == 0.15
    assert SCORING_WEIGHTS["context"] == 0.10


def test_normalize_skill_aliases_and_casing() -> None:
    """Verify skill normalization handles casing, spaces, and aliases."""
    assert normalize_skill("  PyTorch  ") == "pytorch"
    assert normalize_skill("ML") == "machine learning"
    assert normalize_skill("nlp") == "natural language processing"
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill("golang") == "go"


def test_normalize_skills_deduplication() -> None:
    """Verify list normalization deduplicates normalized variants."""
    raw = ["Python", "python", "ML", "machine learning", "Docker"]
    normalized = normalize_skills(raw)
    assert normalized == ["python", "machine learning", "docker"]


def test_normalize_location() -> None:
    """Verify location normalization cleans punctuation and whitespace."""
    assert normalize_location("San Francisco, CA") == "san francisco ca"
    assert normalize_location("  New-York / NY  ") == "new york ny"
    assert normalize_location(None) == ""


def test_deck_builder_invalid_deck_size() -> None:
    """Verify build_candidate_deck validates deck_size."""
    req = JobRequirements(title="Synthetic Role")
    with pytest.raises(ValueError, match="deck_size must be at least 1"):
        build_candidate_deck(requirements=req, candidates=[], deck_size=0)


def test_deck_builder_scaffolding_contract() -> None:
    """Verify build_candidate_deck raises NotImplementedError rather than returning fake candidate evaluations."""
    req = JobRequirements(title="Synthetic Role")
    person = PersonRecord(
        person_id="p-001",
        origin="registered",
        membership_status="registered",
    )
    with pytest.raises(NotImplementedError):
        build_candidate_deck(requirements=req, candidates=[person])


def test_filter_and_score_contracts() -> None:
    """Verify filter and score functions execute deterministically."""
    req = JobRequirements(title="Synthetic Role", must_have_skills=["python"])
    person = PersonRecord(
        person_id="p-001",
        origin="registered",
        membership_status="registered",
        skills=["python"],
        experience_years=3.0,
        current_title="Synthetic Role",
    )
    eligible, reasons, breakdown = evaluate_hard_filters(req, person)
    assert eligible is True
    assert reasons == []

    scored = score_candidate(req, person)
    assert scored["fit_score"] > 0.0
    assert "skills" in scored["component_scores"]

    fit_type = classify_fit_type(req, person, fit_score=scored["fit_score"], component_scores=scored["component_scores"])
    assert fit_type in {"direct", "adjacent", None}
