"""Candidate deck assembly service.

Coordinates hard filtering, scoring, direct/adjacent classification,
and dynamic deck construction (capped at 20% adjacent candidates).
"""

from __future__ import annotations

from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord

MAX_ADJACENT_RATIO: float = 0.20


def build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
    """Assemble a ranked candidate deck and list of excluded candidates.

    Args:
        requirements: Canonical JobRequirements object.
        candidates: List of normalized PersonRecord objects.
        deck_size: Maximum cards to return for the displayed deck (default 20).

    Returns:
        tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
            - displayed_evaluations: Ranked eligible evaluations (direct + up to 20% adjacent).
            - excluded_evaluations: Evaluations for ineligible candidates with exclusion reasons.

    Raises:
        ValueError: If deck_size is less than 1.
        NotImplementedError: Raised in scaffolding until the deck assembly algorithm is implemented.
    """
    if deck_size < 1:
        raise ValueError(f"deck_size must be at least 1, got {deck_size}")

    raise NotImplementedError(
        "Candidate deck assembly algorithm will be implemented in subsequent prompt."
    )
