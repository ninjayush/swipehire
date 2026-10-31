"""Hard filter evaluation engine.

Deterministic hard filter verification for mandatory requirements:
- must_have_skills
- mandatory_qualifications
- min_experience_years / max_experience_years (when specified)
- required_fields (fails closed if unknown)
- dealbreakers (locations, work modes, citizenship)

Adjacent candidates cannot override failed hard filters.
Missing optional data remains unknown and does not exclude.
"""

from __future__ import annotations

import re
from typing import Any

from app.database.schemas import JobRequirements, PersonRecord
from app.matching.normalization import (
    normalize_location,
    normalize_skill,
    normalize_skills,
)


def _extract_all_candidate_skills(candidate: PersonRecord) -> set[str]:
    """Gather all normalized skills from direct skills list, employment, and resume highlights."""
    skills = set(normalize_skills(candidate.skills))

    # Also extract skills mentioned in resume highlights
    for highlight in candidate.resume_highlights:
        if isinstance(highlight, dict):
            for tech in highlight.get("technologies", []):
                norm = normalize_skill(tech)
                if norm:
                    skills.add(norm)

    return skills


def _extract_all_candidate_qualifications(candidate: PersonRecord) -> set[str]:
    """Gather normalized degree and qualification names from education and highlights."""
    quals: set[str] = set()
    for edu in candidate.education:
        if isinstance(edu, dict):
            deg = edu.get("degree")
            field = edu.get("field_of_study")
            if deg:
                quals.add(deg.strip().lower())
            if field:
                quals.add(field.strip().lower())
            if deg and field:
                quals.add(f"{deg.strip().lower()} in {field.strip().lower()}")

    for highlight in candidate.resume_highlights:
        if isinstance(highlight, dict) and highlight.get("type") == "achievement":
            content = highlight.get("content")
            if content:
                quals.add(content.strip().lower())

    return quals


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
    """
    exclusion_reasons: list[str] = []
    filter_results: dict[str, Any] = {
        "skills_passed": True,
        "qualifications_passed": True,
        "experience_passed": True,
        "required_fields_passed": True,
        "dealbreakers_passed": True,
    }

    # 1. Mandatory Skills
    candidate_skills = _extract_all_candidate_skills(candidate)
    missing_mandatory_skills: list[str] = []

    for req_skill in requirements.must_have_skills:
        norm_req = normalize_skill(req_skill)
        # Check exact or substring containment in candidate skills
        matched = any(
            norm_req == cs or norm_req in cs or cs in norm_req for cs in candidate_skills
        )
        if not matched:
            missing_mandatory_skills.append(req_skill)
            exclusion_reasons.append(f"missing_mandatory_skill: {req_skill}")

    if missing_mandatory_skills:
        filter_results["skills_passed"] = False
        filter_results["missing_skills"] = missing_mandatory_skills

    # 2. Mandatory Qualifications
    candidate_quals = _extract_all_candidate_qualifications(candidate)
    missing_quals: list[str] = []

    for qual in requirements.mandatory_qualifications:
        norm_qual = qual.strip().lower()
        matched = any(
            norm_qual in cq or cq in norm_qual for cq in candidate_quals
        )
        if not matched:
            missing_quals.append(qual)
            exclusion_reasons.append(f"missing_mandatory_qualification: {qual}")

    if missing_quals:
        filter_results["qualifications_passed"] = False
        filter_results["missing_qualifications"] = missing_quals

    # 3. Explicit Experience Range Bounds
    if requirements.min_experience_years is not None:
        if candidate.experience_years is None:
            exclusion_reasons.append("experience_unknown_required")
            filter_results["experience_passed"] = False
        elif candidate.experience_years < requirements.min_experience_years:
            exclusion_reasons.append("experience_below_minimum")
            filter_results["experience_passed"] = False

    if (
        requirements.max_experience_years is not None
        and candidate.experience_years is not None
    ):
        if candidate.experience_years > requirements.max_experience_years:
            exclusion_reasons.append("experience_above_maximum")
            filter_results["experience_passed"] = False

    # 4. Required Candidate Fields (Fails closed when unknown)
    prefs = candidate.candidate_preferences or {}
    for field in requirements.required_fields:
        f_norm = field.strip().lower()
        if "avail" in f_norm or "notice" in f_norm:
            if not prefs.get("availability") and not prefs.get("notice_period"):
                exclusion_reasons.append("availability_unknown_required")
                filter_results["required_fields_passed"] = False
        elif "salary" in f_norm or "comp" in f_norm:
            if not prefs.get("expected_salary") and not prefs.get("salary"):
                exclusion_reasons.append("salary_unknown_required")
                filter_results["required_fields_passed"] = False
        elif "resume" in f_norm:
            if not candidate.resume_highlights and not candidate.employment_history:
                exclusion_reasons.append("resume_missing_required")
                filter_results["required_fields_passed"] = False
        elif "loc" in f_norm:
            if not candidate.location and not prefs.get("location"):
                exclusion_reasons.append("location_unknown_required")
                filter_results["required_fields_passed"] = False
        else:
            code = f_norm.replace(" ", "_")
            if code not in prefs and getattr(candidate, code, None) is None:
                exclusion_reasons.append(f"{code}_unknown_required")
                filter_results["required_fields_passed"] = False

    # 5. Dealbreakers
    cand_loc_norm = normalize_location(candidate.location or prefs.get("location"))
    for db in requirements.dealbreakers:
        db_low = db.strip().lower()

        # Location dealbreakers (e.g. "must reside in US", "New York only")
        if "reside" in db_low or "location" in db_low or "based in" in db_low:
            if not cand_loc_norm:
                exclusion_reasons.append("location_unknown_required")
                filter_results["dealbreakers_passed"] = False
            else:
                # Check for country or state/city keywords in location
                keywords = [
                    w for w in re.findall(r"\b[a-zA-Z]{2,}\b", db_low)
                    if w not in {"must", "reside", "in", "location", "based", "only", "required"}
                ]
                if keywords and not any(kw in cand_loc_norm for kw in keywords):
                    exclusion_reasons.append("location_mismatch")
                    filter_results["dealbreakers_passed"] = False

        # Work mode dealbreakers (e.g. "onsite only", "no remote")
        if ("onsite only" in db_low or "in-office only" in db_low or "no remote" in db_low):
            cand_work_mode = prefs.get("work_mode") or prefs.get("work_modes")
            if isinstance(cand_work_mode, str) and cand_work_mode.lower() == "remote":
                exclusion_reasons.append("work_mode_mismatch")
                filter_results["dealbreakers_passed"] = False

    eligible = len(exclusion_reasons) == 0
    return eligible, exclusion_reasons, filter_results
