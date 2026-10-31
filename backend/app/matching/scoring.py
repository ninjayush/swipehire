"""Deterministic candidate fit scoring engine.

Computes weighted score components based on locked context weights:
- skills: 30% (0.30)
- experience: 25% (0.25)
- role_domain: 20% (0.20)
- trajectory: 15% (0.15)
- context: 10% (0.10)

Formula:
fit_score = 0.30*skills + 0.25*experience + 0.20*role_domain + 0.15*trajectory + 0.10*context

Calculates evidence_coverage (0.0 to 1.0) indicating source data completeness.
Deterministic, transparent, reproducible, and non-LLM based.
"""

from __future__ import annotations

import math
from typing import Any

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.filters import _extract_all_candidate_skills
from app.matching.normalization import (
    SENIORITY_RANKS,
    calculate_token_overlap,
    extract_seniority,
    normalize_location,
    normalize_skill,
    normalize_title,
)

SCORING_WEIGHTS: dict[str, float] = {
    "skills": 0.30,
    "experience": 0.25,
    "role_domain": 0.20,
    "trajectory": 0.15,
    "context": 0.10,
}


def _clamp(val: float, low: float = 0.0, high: float = 100.0) -> float:
    """Clamp float to [low, high], handling NaN and inf safely."""
    if math.isnan(val) or math.isinf(val):
        return low
    return max(low, min(high, float(val)))


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
            - reasons: list[str] (component-level explanation notes)
    """
    reasons: list[str] = []
    candidate_skills = _extract_all_candidate_skills(candidate)
    prefs = candidate.candidate_preferences or {}

    # Track evidenced dimensions for evidence_coverage
    evidenced_flags: dict[str, bool] = {
        "skills": len(candidate_skills) > 0,
        "experience": candidate.experience_years is not None or len(candidate.employment_history) > 0,
        "role_domain": bool(candidate.current_title or candidate.headline),
        "trajectory": bool(len(candidate.employment_history) > 0 or candidate.current_title),
        "context": bool(candidate.location or prefs),
    }

    # =========================================================================
    # 1. Skills Scoring (Weight: 30%)
    # =========================================================================
    must_have_req = requirements.must_have_skills
    preferred_req = requirements.preferred_skills

    m_matches = [
        s for s in must_have_req
        if any(normalize_skill(s) in cs or cs in normalize_skill(s) for cs in candidate_skills)
    ]
    p_matches = [
        s for s in preferred_req
        if any(normalize_skill(s) in cs or cs in normalize_skill(s) for cs in candidate_skills)
    ]

    cov_m = (len(m_matches) / len(must_have_req)) if must_have_req else 1.0
    cov_p = (len(p_matches) / len(preferred_req)) if preferred_req else 1.0

    if not evidenced_flags["skills"]:
        skills_score = 0.0
        reasons.append("Skills: No skills recorded in profile.")
    elif must_have_req and preferred_req:
        skills_score = (0.70 * cov_m + 0.30 * cov_p) * 100.0
        reasons.append(
            f"Skills: Matched {len(m_matches)}/{len(must_have_req)} must-have skills "
            f"and {len(p_matches)}/{len(preferred_req)} preferred skills."
        )
    elif must_have_req:
        skills_score = cov_m * 100.0
        reasons.append(f"Skills: Matched {len(m_matches)}/{len(must_have_req)} must-have skills.")
    elif preferred_req:
        skills_score = cov_p * 100.0
        reasons.append(f"Skills: Matched {len(p_matches)}/{len(preferred_req)} preferred skills.")
    else:
        skills_score = 75.0 if len(candidate_skills) >= 3 else 50.0
        reasons.append(f"Skills: Candidate possesses {len(candidate_skills)} documented skills.")

    skills_score = _clamp(skills_score)

    # =========================================================================
    # 2. Experience Scoring (Weight: 25%)
    # =========================================================================
    exp_years = candidate.experience_years
    min_exp = requirements.min_experience_years
    max_exp = requirements.max_experience_years

    if exp_years is None:
        # Check if calculable from employment history count
        if candidate.employment_history:
            exp_years = float(len(candidate.employment_history) * 1.5)  # conservative heuristic
        else:
            exp_years = None

    if exp_years is None:
        experience_score = 0.0
        reasons.append("Experience: Experience years unevidenced in candidate profile.")
    elif min_exp is not None and max_exp is not None:
        if min_exp <= exp_years <= max_exp:
            experience_score = 100.0
            reasons.append(
                f"Experience: {exp_years:.1f} years falls directly within requested {min_exp:.0f}–{max_exp:.0f} year range."
            )
        elif exp_years < min_exp:
            experience_score = _clamp((exp_years / min_exp) * 80.0)
            reasons.append(
                f"Experience: {exp_years:.1f} years is below requested minimum of {min_exp:.0f} years."
            )
        else:
            experience_score = _clamp(100.0 - (exp_years - max_exp) * 4.0, low=70.0)
            reasons.append(
                f"Experience: {exp_years:.1f} years exceeds requested maximum of {max_exp:.0f} years."
            )
    elif min_exp is not None:
        if exp_years >= min_exp:
            experience_score = min(100.0, 90.0 + min(10.0, (exp_years - min_exp) * 2.0))
            reasons.append(
                f"Experience: {exp_years:.1f} years meets or exceeds requested {min_exp:.0f}+ years."
            )
        else:
            experience_score = _clamp((exp_years / min_exp) * 80.0)
            reasons.append(
                f"Experience: {exp_years:.1f} years is below requested {min_exp:.0f}+ years."
            )
    elif max_exp is not None:
        if exp_years <= max_exp:
            experience_score = 100.0
            reasons.append(f"Experience: {exp_years:.1f} years is within {max_exp:.0f} years limit.")
        else:
            experience_score = _clamp(100.0 - (exp_years - max_exp) * 5.0, low=60.0)
            reasons.append(f"Experience: {exp_years:.1f} years exceeds {max_exp:.0f} years limit.")
    else:
        experience_score = _clamp(60.0 + min(40.0, exp_years * 5.0))
        reasons.append(f"Experience: {exp_years:.1f} years of relevant professional experience.")

    experience_score = _clamp(experience_score)

    # =========================================================================
    # 3. Role & Domain Alignment (Weight: 20%)
    # =========================================================================
    req_title = requirements.title or ""
    cand_title = candidate.current_title or candidate.headline or ""

    if not cand_title:
        role_domain_score = 0.0
        reasons.append("Role/Domain: Current job title and headline unevidenced.")
    else:
        norm_req_t = normalize_title(req_title)
        norm_cand_t = normalize_title(cand_title)

        if norm_req_t == norm_cand_t:
            role_domain_score = 100.0
            reasons.append(f"Role/Domain: Exact title match with '{cand_title}'.")
        else:
            overlap = calculate_token_overlap(norm_req_t, norm_cand_t)
            if overlap >= 0.5:
                role_domain_score = 75.0 + 25.0 * overlap
                reasons.append(f"Role/Domain: Strong title keyword alignment ({cand_title}).")
            elif overlap >= 0.2:
                role_domain_score = 50.0 + 25.0 * overlap
                reasons.append(f"Role/Domain: Moderate domain alignment ({cand_title}).")
            else:
                # Check for core functional words (engineer, developer, architect, analyst)
                core_words = {"engineer", "developer", "architect", "scientist", "manager", "lead"}
                t1_core = set(norm_req_t.split()).intersection(core_words)
                t2_core = set(norm_cand_t.split()).intersection(core_words)
                if t1_core and t1_core == t2_core:
                    role_domain_score = 50.0
                    reasons.append(f"Role/Domain: Adjacent functional alignment ({cand_title}).")
                else:
                    role_domain_score = 10.0
                    reasons.append(f"Role/Domain: Distinct role title ({cand_title}).")

    role_domain_score = _clamp(role_domain_score)

    # =========================================================================
    # 4. Seniority & Career Trajectory (Weight: 15%)
    # =========================================================================
    req_sen = requirements.seniority or extract_seniority(req_title)
    cand_sen = extract_seniority(cand_title) or (
        extract_seniority(candidate.headline) if candidate.headline else None
    )

    req_rank = SENIORITY_RANKS.get(req_sen.lower(), 4) if req_sen else None
    cand_rank = SENIORITY_RANKS.get(cand_sen.lower(), 4) if cand_sen else None

    history_len = len(candidate.employment_history)
    progression_bonus = min(15.0, history_len * 5.0)

    if not evidenced_flags["trajectory"]:
        trajectory_score = 0.0
        reasons.append("Trajectory: Career history unevidenced.")
    elif req_rank is not None and cand_rank is not None:
        diff = cand_rank - req_rank
        if diff == 0:
            trajectory_score = 90.0 + (5.0 if history_len >= 2 else 0.0)
            reasons.append(f"Trajectory: Seniority level '{cand_sen}' matches role requirement.")
        elif diff == 1:
            trajectory_score = 85.0
            reasons.append(f"Trajectory: Seniority '{cand_sen}' slightly senior to role.")
        elif diff == -1:
            trajectory_score = 65.0 + progression_bonus
            reasons.append(f"Trajectory: Seniority '{cand_sen}' one step below role tier.")
        elif diff < -1:
            trajectory_score = 40.0 + progression_bonus
            reasons.append(f"Trajectory: Seniority '{cand_sen}' junior relative to role requirements.")
        else:
            trajectory_score = 70.0
            reasons.append(f"Trajectory: Seniority '{cand_sen}' substantially above role tier.")
    else:
        trajectory_score = 75.0 + progression_bonus
        reasons.append("Trajectory: General career trajectory across available history.")

    trajectory_score = _clamp(trajectory_score)

    # =========================================================================
    # 5. Contextual Preferences / Fit (Weight: 10%)
    # =========================================================================
    cand_loc = normalize_location(candidate.location or prefs.get("location"))
    cand_work_mode = str(prefs.get("work_mode", "")).lower()

    job_locs = [normalize_location(l) for l in requirements.locations if l]
    job_modes = [m.lower() for m in requirements.work_modes]

    context_matches = 0
    context_evaluations = 0

    if job_locs:
        context_evaluations += 1
        if cand_loc and any(jl in cand_loc or cand_loc in jl for jl in job_locs):
            context_matches += 1

    if job_modes:
        context_evaluations += 1
        if "remote" in job_modes and ("remote" in cand_work_mode or not cand_work_mode):
            context_matches += 1
        elif cand_work_mode and any(jm in cand_work_mode for jm in job_modes):
            context_matches += 1

    if not evidenced_flags["context"]:
        context_score = 50.0  # neutral baseline when candidate provided no preferences
        reasons.append("Context: Location and work mode preferences not specified (neutral).")
    elif context_evaluations > 0:
        context_score = (context_matches / context_evaluations) * 100.0
        reasons.append(f"Context: {context_matches}/{context_evaluations} location/work-mode preferences aligned.")
    else:
        context_score = 80.0
        reasons.append("Context: Flexible location/mode requirements.")

    context_score = _clamp(context_score)

    # =========================================================================
    # Evidence Coverage & Final Weighted Fit Score
    # =========================================================================
    evidenced_count = sum(1 for is_ev in evidenced_flags.values() if is_ev)
    evidence_coverage = round(evidenced_count / 5.0, 2)

    component_scores: dict[str, float] = {
        "skills": round(skills_score, 1),
        "experience": round(experience_score, 1),
        "role_domain": round(role_domain_score, 1),
        "trajectory": round(trajectory_score, 1),
        "context": round(context_score, 1),
    }

    # Deterministic weighted formula:
    # fit_score = 0.30*skills + 0.25*experience + 0.20*role_domain + 0.15*trajectory + 0.10*context
    fit_score = (
        SCORING_WEIGHTS["skills"] * component_scores["skills"]
        + SCORING_WEIGHTS["experience"] * component_scores["experience"]
        + SCORING_WEIGHTS["role_domain"] * component_scores["role_domain"]
        + SCORING_WEIGHTS["trajectory"] * component_scores["trajectory"]
        + SCORING_WEIGHTS["context"] * component_scores["context"]
    )
    fit_score = _clamp(round(fit_score, 1))

    return {
        "fit_score": fit_score,
        "component_scores": component_scores,
        "evidence_coverage": evidence_coverage,
        "reasons": reasons,
    }
