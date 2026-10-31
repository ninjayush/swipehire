"""Direct vs. adjacent fit classification.

Classifies eligible candidates who pass all hard filters into:
- "direct": Strong match on title, domain, must-have and preferred requirements.
- "adjacent": Passed all hard filters, strong transferable capability, but misses
  one or more preferred requirements or literal title/terminology alignment.
- None: Candidate lacks sufficient evidence or score to classify as either.

Candidates who failed hard filters must NEVER be classified as direct or adjacent.
"""

from __future__ import annotations

from typing import Literal

from app.database.schemas import JobRequirements, PersonRecord

FIT_TYPE_DIRECT: Literal["direct"] = "direct"
FIT_TYPE_ADJACENT: Literal["adjacent"] = "adjacent"

# ==============================================================================
# Centralized Engineering Default Thresholds (Subject to Team Calibration)
# ==============================================================================

DEFAULT_DIRECT_MIN_SCORE: float = 70.0
DEFAULT_ADJACENT_MIN_SCORE: float = 50.0

MIN_DIRECT_SKILLS_SCORE: float = 60.0
MIN_DIRECT_ROLE_DOMAIN_SCORE: float = 50.0
MIN_ADJACENT_TRANSFERABLE_SKILLS: float = 40.0


def classify_fit_type(
    requirements: JobRequirements,
    candidate: PersonRecord,
    fit_score: float,
    component_scores: dict[str, float],
) -> Literal["direct", "adjacent"] | None:
    """Classify an eligible candidate as direct or adjacent fit.

    Args:
        requirements: Confirmed job requirements.
        candidate: Candidate person record.
        fit_score: Overall calculated fit score (0.0 - 100.0).
        component_scores: Component scores breakdown (skills, experience, role_domain, trajectory, context).

    Returns:
        Literal["direct", "adjacent"] | None:
            - "direct" if aligned strongly across title, domain, and skills.
            - "adjacent" if possessing strong transferable capability with gaps in preferred criteria or title.
            - None if fit score or evidence is insufficient for deck inclusion.
    """
    skills_score = component_scores.get("skills", 0.0)
    domain_score = component_scores.get("role_domain", 0.0)
    exp_score = component_scores.get("experience", 0.0)

    # 1. Direct Fit Criteria
    if (
        fit_score >= DEFAULT_DIRECT_MIN_SCORE
        and skills_score >= MIN_DIRECT_SKILLS_SCORE
        and domain_score >= MIN_DIRECT_ROLE_DOMAIN_SCORE
    ):
        return FIT_TYPE_DIRECT

    # 2. Adjacent Fit Criteria
    # Must meet adjacent minimum score, have transferable skills or experience,
    # but miss literal title alignment or some preferred skills.
    if fit_score >= DEFAULT_ADJACENT_MIN_SCORE:
        has_transferable_capability = (
            skills_score >= MIN_ADJACENT_TRANSFERABLE_SKILLS or exp_score >= 50.0
        )
        has_criteria_gap = (
            domain_score < 80.0
            or skills_score < 75.0
            or bool(requirements.preferred_skills)
        )

        if has_transferable_capability and has_criteria_gap:
            return FIT_TYPE_ADJACENT

    # 3. Insufficient evidence or weak fit -> None
    return None
