"""Direct vs. adjacent fit classification.

Classifies eligible candidates who pass all hard filters into:
- "direct": Strong match on title, domain, must-have and preferred requirements.
- "adjacent": Passed all hard filters, strong transferable capability, but misses
  one or more preferred requirements or literal title/terminology alignment.

Candidates who failed hard filters are never classified as direct or adjacent.
"""

from __future__ import annotations

from typing import Literal

from app.database.schemas import JobRequirements, PersonRecord

FIT_TYPE_DIRECT: Literal["direct"] = "direct"
FIT_TYPE_ADJACENT: Literal["adjacent"] = "adjacent"

# Initial engineering default thresholds (tunable)
DEFAULT_DIRECT_MIN_SCORE: float = 70.0
DEFAULT_ADJACENT_MIN_SCORE: float = 55.0


def classify_fit_type(
    requirements: JobRequirements,
    candidate: PersonRecord,
    fit_score: float,
    component_scores: dict[str, float],
) -> Literal["direct", "adjacent"]:
    """Classify an eligible candidate as direct or adjacent fit.

    Args:
        requirements: Confirmed job requirements.
        candidate: Candidate person record.
        fit_score: Overall calculated fit score (0-100).
        component_scores: Component scores breakdown.

    Returns:
        Literal["direct", "adjacent"]

    Raises:
        NotImplementedError: Raised in scaffolding until classification prompt.
    """
    raise NotImplementedError(
        "Candidate classification will be implemented in subsequent prompt."
    )
