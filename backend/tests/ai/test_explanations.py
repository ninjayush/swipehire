"""Unit tests for grounded match explanation generation (explanations.py)."""

from unittest.mock import MagicMock
from anthropic.types import TextBlock
import pytest

from app.ai.anthropic_client import ClaudeClient
from app.ai.explanations import (
    generate_deterministic_explanation,
    generate_match_explanation,
)
from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord


def test_deterministic_explanation_direct_fit() -> None:
    req = JobRequirements(
        title="Backend Engineer",
        must_have_skills=["Python", "PostgreSQL"],
    )
    person = PersonRecord(
        person_id="p-exp-1",
        origin="registered",
        membership_status="registered",
        current_title="Backend Engineer",
        skills=["Python", "PostgreSQL"],
        experience_years=5.0,
    )
    evaluation = CandidateEvaluation(
        person_id="p-exp-1",
        eligible=True,
        fit_score=92.0,
        fit_type="direct",
        evidence_coverage=1.0,
        reasons=["Skills matched: Python, PostgreSQL"],
    )

    explanation = generate_deterministic_explanation(req, person, evaluation)
    assert "Strong direct fit" in explanation
    assert "92.0/100" in explanation
    assert "Backend Engineer" in explanation
    assert "5.0 years" in explanation


def test_deterministic_explanation_adjacent_fit() -> None:
    req = JobRequirements(
        title="Machine Learning Engineer",
        must_have_skills=["Python"],
        preferred_skills=["PyTorch"],
    )
    person = PersonRecord(
        person_id="p-exp-2",
        origin="registered",
        membership_status="registered",
        current_title="Data Engineer",
        skills=["Python", "Spark"],
        experience_years=4.0,
    )
    evaluation = CandidateEvaluation(
        person_id="p-exp-2",
        eligible=True,
        fit_score=72.0,
        fit_type="adjacent",
        evidence_coverage=0.8,
        reasons=["Data Engineer aligns with transferable capabilities"],
    )

    explanation = generate_deterministic_explanation(req, person, evaluation)
    assert "Transferable adjacent fit" in explanation
    assert "Data Engineer" in explanation
    assert "PyTorch" in explanation


def test_explanation_limited_evidence_warning() -> None:
    req = JobRequirements(title="Software Engineer")
    person = PersonRecord(
        person_id="p-exp-3",
        origin="registered",
        membership_status="registered",
        skills=["Python"],
    )
    evaluation = CandidateEvaluation(
        person_id="p-exp-3",
        eligible=True,
        fit_score=60.0,
        fit_type="direct",
        evidence_coverage=0.20,  # Below 0.50
    )

    explanation = generate_deterministic_explanation(req, person, evaluation)
    assert "Limited profile evidence documented" in explanation


def test_generate_match_explanation_claude_fallback_on_error() -> None:
    """Verify that if Claude fails, explanation generator cleanly returns deterministic text."""
    mock_sdk = MagicMock()
    mock_sdk.messages.create.side_effect = RuntimeError("Claude provider timeout")
    failing_client = ClaudeClient(client=mock_sdk)

    req = JobRequirements(title="Developer", must_have_skills=["Python"])
    person = PersonRecord(
        person_id="p-exp-4",
        origin="registered",
        membership_status="registered",
        skills=["Python"],
        experience_years=3.0,
    )
    evaluation = CandidateEvaluation(
        person_id="p-exp-4",
        eligible=True,
        fit_score=80.0,
        fit_type="direct",
    )

    explanation = generate_match_explanation(req, person, evaluation, client=failing_client)
    assert "Strong direct fit" in explanation
    assert "80.0/100" in explanation
