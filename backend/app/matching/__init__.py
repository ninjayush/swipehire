"""Deterministic matching package (Person 2 owned).

Exposes hard filter evaluation, scoring, classification, normalization,
and dynamic candidate deck assembly.
"""

from __future__ import annotations

from app.matching.classification import (
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

__all__ = [
    "FIT_TYPE_ADJACENT",
    "FIT_TYPE_DIRECT",
    "MAX_ADJACENT_RATIO",
    "SCORING_WEIGHTS",
    "build_candidate_deck",
    "classify_fit_type",
    "evaluate_hard_filters",
    "normalize_location",
    "normalize_skill",
    "normalize_skills",
    "score_candidate",
]
