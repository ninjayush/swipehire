"""Deterministic candidate fit scoring engine.

Computes weighted score components based on locked context weights:
- skills: 30% (0.30)
- experience: 25% (0.25)
- role_domain: 20% (0.20)
- trajectory: 15% (0.15)
- context: 10% (0.10)

Also calculates evidence_coverage (0.0 to 1.0) indicating source data completeness.
Deterministic, transparent, and non-LLM based.
"""

from __future__ import annotations

from typing import Any

from app.database.schemas import JobRequirements, PersonRecord

SCORING_WEIGHTS: dict[str, float] = {
    "skills": 0.30,
    "experience": 0.25,
    "role_domain": 0.20,
    "trajectory": 0.15,
    "context": 0.10,
}


def score_candidate(
    requirements: JobRequirements,
    candidate: PersonRecord,
) -> dict[str, Any]:
    """Score candidate deterministically against job requirements.

    Args:
        requirements: Confirmed job requirements.
        candidate: Candidate person record.

    Returns:
        dict[str, Any]:
            - fit_score: float (0.0 - 100.0)
            - component_scores: dict[str, float] (each 0.0 - 100.0)
            - evidence_coverage: float (0.0 - 1.0)
            - reasons: list[str]

    Raises:
        NotImplementedError: Raised in scaffolding until scoring prompt implements calculations.
    """
    raise NotImplementedError(
        "Candidate scoring engine will be implemented in subsequent prompt."
    )
