"""Candidate deck assembly service.

Coordinates hard filtering, deterministic fit scoring, direct/adjacent
classification, dynamic deck assembly (strictly capping adjacent candidates at 20%),
and evidence-grounded explanation generation.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from app.ai.anthropic_client import ClaudeClient
from app.ai.explanations import generate_match_explanation
from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord
from app.matching.classification import (
    FIT_TYPE_ADJACENT,
    FIT_TYPE_DIRECT,
    classify_fit_type,
)
from app.matching.filters import evaluate_hard_filters
from app.matching.scoring import score_candidate

logger = logging.getLogger(__name__)

MAX_DECK_SIZE: int = 20
MAX_ADJACENT_RATIO: float = 0.20
MAX_ADJACENT_COUNT: int = 4


def build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
    client: ClaudeClient | None = None,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
    """Assemble a ranked candidate deck and list of excluded candidates.

    Algorithm:
    1. Validate deck_size (1 to 20).
    2. Deduplicate candidate records by person_id.
    3. Apply hard filters: ineligible candidates are routed directly to exclusions with stable reason codes.
    4. Score all eligible candidates deterministically across 5 components.
    5. Classify eligible candidates into direct or adjacent pools (or exclude if evidence/score is insufficient).
    6. Sort both pools deterministically by fit_score (descending), evidence_coverage (descending), person_id (ascending).
    7. Select candidates strictly respecting the adjacent cap (max 20% of actual displayed deck, max 4 cards).
       Never add low-quality candidates as filler.
    8. Assign ranks (1..N) to displayed cards, and rank=None to excluded cards.
    9. Attach grounded match explanations to displayed cards.

    Args:
        requirements: Canonical JobRequirements object.
        candidates: List of normalized PersonRecord objects.
        deck_size: Maximum cards to return for the displayed deck (default 20, max 20).
        client: Optional ClaudeClient instance for explanation polishing.

    Returns:
        tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
            - displayed_evaluations: Ranked eligible evaluations (rank 1..N).
            - excluded_evaluations: Non-displayed evaluations (rank=None).

    Raises:
        ValueError: If deck_size is less than 1.
    """
    if deck_size < 1:
        raise ValueError(f"deck_size must be at least 1, got {deck_size}")

    target_size = min(deck_size, MAX_DECK_SIZE)

    # 1. Deduplicate incoming candidates by person_id deterministically
    seen_ids: set[str] = set()
    unique_candidates: list[PersonRecord] = []
    for cand in candidates:
        if cand.person_id not in seen_ids:
            seen_ids.add(cand.person_id)
            unique_candidates.append(cand)

    excluded_evaluations: list[CandidateEvaluation] = []
    direct_pool: list[tuple[PersonRecord, float, dict[str, float], float, list[str]]] = []
    adjacent_pool: list[tuple[PersonRecord, float, dict[str, float], float, list[str]]] = []

    # 2. Hard filter evaluation, scoring, and classification
    for cand in unique_candidates:
        eligible, exclusion_reasons, _ = evaluate_hard_filters(requirements, cand)
        if not eligible:
            excluded_evaluations.append(
                CandidateEvaluation(
                    person_id=cand.person_id,
                    eligible=False,
                    exclusion_reasons=exclusion_reasons,
                    fit_score=None,
                    component_scores={},
                    evidence_coverage=None,
                    fit_type=None,
                    match_explanation=None,
                    reasons=exclusion_reasons,
                    rank=None,
                )
            )
            continue

        # Score eligible candidate
        score_data = score_candidate(requirements, cand)
        fit_score = score_data["fit_score"]
        component_scores = score_data["component_scores"]
        evidence_cov = score_data["evidence_coverage"]
        reasons = score_data["reasons"]

        # Classify fit type
        fit_type = classify_fit_type(requirements, cand, fit_score, component_scores)

        if fit_type == FIT_TYPE_DIRECT:
            direct_pool.append((cand, fit_score, component_scores, evidence_cov, reasons))
        elif fit_type == FIT_TYPE_ADJACENT:
            adjacent_pool.append((cand, fit_score, component_scores, evidence_cov, reasons))
        else:
            # Candidate passed mandatory filters but lacks sufficient score/evidence for deck inclusion
            excluded_evaluations.append(
                CandidateEvaluation(
                    person_id=cand.person_id,
                    eligible=True,
                    exclusion_reasons=["insufficient_fit_or_evidence"],
                    fit_score=fit_score,
                    component_scores=component_scores,
                    evidence_coverage=evidence_cov,
                    fit_type=None,
                    match_explanation=None,
                    reasons=[
                        "Candidate passed mandatory filters but fit score or evidence did not meet deck threshold."
                    ]
                    + reasons,
                    rank=None,
                )
            )

    # 3. Deterministic sorting: (-fit_score, -evidence_coverage, person_id)
    def sort_key(item: tuple[PersonRecord, float, dict[str, float], float, list[str]]) -> tuple:
        cand, score, _, cov, _ = item
        return (-score, -cov, cand.person_id)

    direct_pool.sort(key=sort_key)
    adjacent_pool.sort(key=sort_key)

    # 4. Adjacent Cap Calculation (Maximum 20% of displayed deck, maximum 4 in a 20-card deck)
    # Never add weak adjacent filler. Maximize direct candidates up to target_size.
    max_adj_possible = min(len(adjacent_pool), MAX_ADJACENT_COUNT)
    chosen_adj_count = 0
    chosen_direct_count = min(len(direct_pool), target_size)

    # Search for maximum valid adjacent count that satisfies: adj <= floor(displayed_total * 0.20)
    for a in range(max_adj_possible, -1, -1):
        d = min(len(direct_pool), target_size - a)
        displayed_total = d + a
        if displayed_total == 0:
            continue
        if a <= math.floor(displayed_total * MAX_ADJACENT_RATIO):
            chosen_adj_count = a
            chosen_direct_count = d
            break

    selected_direct = direct_pool[:chosen_direct_count]
    selected_adjacent = adjacent_pool[:chosen_adj_count]

    # Non-selected candidates from pools are added to excluded/non-displayed
    for cand, score, comps, cov, rsn in direct_pool[chosen_direct_count:]:
        excluded_evaluations.append(
            CandidateEvaluation(
                person_id=cand.person_id,
                eligible=True,
                exclusion_reasons=["deck_capacity_reached"],
                fit_score=score,
                component_scores=comps,
                evidence_coverage=cov,
                fit_type=FIT_TYPE_DIRECT,
                match_explanation=None,
                reasons=["Eligible direct candidate ranked outside available deck capacity."] + rsn,
                rank=None,
            )
        )

    for cand, score, comps, cov, rsn in adjacent_pool[chosen_adj_count:]:
        excluded_evaluations.append(
            CandidateEvaluation(
                person_id=cand.person_id,
                eligible=True,
                exclusion_reasons=["adjacent_cap_reached" if chosen_adj_count >= MAX_ADJACENT_COUNT else "deck_capacity_reached"],
                fit_score=score,
                component_scores=comps,
                evidence_coverage=cov,
                fit_type=FIT_TYPE_ADJACENT,
                match_explanation=None,
                reasons=["Eligible adjacent candidate not selected due to adjacent cap or deck capacity."] + rsn,
                rank=None,
            )
        )

    # 5. Build displayed evaluations sorted by fit_score and assign stable ranks
    displayed_items = [
        (cand, score, comps, cov, rsn, FIT_TYPE_DIRECT) for cand, score, comps, cov, rsn in selected_direct
    ] + [
        (cand, score, comps, cov, rsn, FIT_TYPE_ADJACENT) for cand, score, comps, cov, rsn in selected_adjacent
    ]

    displayed_items.sort(key=lambda item: (-item[1], -item[3], item[0].person_id))

    displayed_evaluations: list[CandidateEvaluation] = []
    for rank_idx, (cand, score, comps, cov, rsn, f_type) in enumerate(displayed_items, start=1):
        base_eval = CandidateEvaluation(
            person_id=cand.person_id,
            eligible=True,
            exclusion_reasons=[],
            fit_score=score,
            component_scores=comps,
            evidence_coverage=cov,
            fit_type=f_type,
            match_explanation=None,
            reasons=rsn,
            rank=rank_idx,
        )

        # Generate grounded explanation (Claude with deterministic fallback)
        explanation = generate_match_explanation(requirements, cand, base_eval, client=client)
        base_eval.match_explanation = explanation
        displayed_evaluations.append(base_eval)

    return displayed_evaluations, excluded_evaluations
