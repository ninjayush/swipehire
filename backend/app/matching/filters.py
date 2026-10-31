"""Hard filter evaluation engine.

Deterministic hard filter verification for mandatory requirements:
- must_have_skills
- mandatory_qualifications
- dealbreakers
- required candidate fields (e.g. availability, salary, resume)

Adjacent candidates cannot override failed hard filters.
Missing optional data remains unknown and does not exclude.
"""

from __future__ import annotations

from typing import Any

from app.database.schemas import JobRequirements, PersonRecord


def evaluate_hard_filters(
    requirements: JobRequirements,
    candidate: PersonRecord,
) -> tuple[bool, list[str], dict[str, Any]]:
    """Evaluate candidate against explicitly mandatory criteria and dealbreakers.

    Args:
        requirements: Confirmed job requirements.
        candidate: Canonical candidate person record.

    Returns:
        tuple[bool, list[str], dict[str, Any]]:
            - eligible: True if passed all mandatory filters, False otherwise.
            - exclusion_reasons: Stable reason codes explaining failed conditions.
            - filter_results: Breakdown of individual filter evaluations.

    Raises:
        NotImplementedError: Raised in scaffolding until filters prompt implements evaluation logic.
    """
    raise NotImplementedError(
        "Hard filter evaluation logic will be implemented in subsequent prompt."
    )
