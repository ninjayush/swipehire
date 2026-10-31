"""Scaffolding and integration boundary tests for app.ai."""

import os
import pytest

from app.ai.anthropic_client import (
    AIConfigurationError,
    AIParsingError,
    extract_json_payload,
    get_anthropic_client,
    get_anthropic_model,
)
from app.ai.explanations import generate_match_explanation
from app.ai.jd_parser import parse_job_description
from app.ai.resume_parser import parse_resume_text
from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord


def test_ai_module_exports() -> None:
    """Verify all expected public interfaces are importable."""
    assert callable(parse_job_description)
    assert callable(parse_resume_text)
    assert callable(generate_match_explanation)
    assert callable(get_anthropic_client)


def test_anthropic_client_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify AIConfigurationError is raised when ANTHROPIC_API_KEY is not set."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(AIConfigurationError, match="ANTHROPIC_API_KEY is not set"):
        get_anthropic_client()


def test_extract_json_payload_clean() -> None:
    """Verify raw JSON parsing."""
    raw = '{"skills": ["python", "fastapi"]}'
    res = extract_json_payload(raw)
    assert res == {"skills": ["python", "fastapi"]}


def test_extract_json_payload_markdown_fences() -> None:
    """Verify JSON in markdown code blocks is properly extracted."""
    raw = "```json\n{\"role\": \"backend engineer\"}\n```"
    res = extract_json_payload(raw)
    assert res == {"role": "backend engineer"}


def test_extract_json_payload_invalid() -> None:
    """Verify AIParsingError is raised on malformed JSON."""
    with pytest.raises(AIParsingError):
        extract_json_payload("not valid json at all")


def test_jd_parser_empty_input_validation() -> None:
    """Verify parse_job_description rejects empty text."""
    with pytest.raises(ValueError, match="raw_jd must not be empty"):
        parse_job_description("")

    with pytest.raises(ValueError, match="raw_jd must not be empty"):
        parse_job_description("   \n\t  ")


def test_jd_parser_scaffolding_contract() -> None:
    """Verify parse_job_description raises NotImplementedError rather than returning fake data."""
    with pytest.raises(NotImplementedError):
        parse_job_description("Senior Python Engineer with 5+ years experience")


def test_resume_parser_empty_input_validation() -> None:
    """Verify parse_resume_text rejects empty text."""
    with pytest.raises(ValueError, match="resume_text must not be empty"):
        parse_resume_text("")

    with pytest.raises(ValueError, match="resume_text must not be empty"):
        parse_resume_text("   ")


def test_resume_parser_scaffolding_contract() -> None:
    """Verify parse_resume_text raises NotImplementedError rather than returning fake data."""
    with pytest.raises(NotImplementedError):
        parse_resume_text("Experience: Software Developer at Synthetic Corp")


def test_shared_schemas_instantiation() -> None:
    """Verify canonical schemas from app.database.schemas can be instantiated with synthetic test data."""
    req = JobRequirements(
        title="Synthetic Engineer",
        must_have_skills=["python"],
        preferred_skills=["fastapi"],
    )
    assert req.title == "Synthetic Engineer"
    assert req.must_have_skills == ["python"]

    person = PersonRecord(
        person_id="synth-001",
        origin="registered",
        membership_status="registered",
        name="Alex Synthetic",
        skills=["python", "fastapi"],
    )
    assert person.person_id == "synth-001"

    eval_result = CandidateEvaluation(
        person_id="synth-001",
        eligible=True,
        fit_score=85.0,
        fit_type="direct",
    )
    assert eval_result.eligible is True
    assert eval_result.fit_type == "direct"
