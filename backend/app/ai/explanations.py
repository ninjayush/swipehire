"""Match explanation generation service using Claude.

Produces evidence-grounded explanations explaining why a candidate is a
direct or adjacent fit, or why they failed mandatory criteria.
Never manufactures candidate facts or verified status without backing data.
"""

from __future__ import annotations

from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord


def generate_match_explanation(
    requirements: JobRequirements,
    candidate: PersonRecord,
    evaluation: CandidateEvaluation,
) -> str:
    """Generate a concise, evidence-grounded explanation for candidate fit.

    Args:
        requirements: Canonical job requirements.
        candidate: Candidate person record.
        evaluation: Candidate evaluation outcome.

    Returns:
        str: Concise human-readable explanation.

    Raises:
        NotImplementedError: Raised in scaffolding until prompt implements the Claude explanation pipeline.
    """
    raise NotImplementedError(
        "Explanation generation with Claude is scheduled for implementation in a subsequent prompt."
    )
