"""Match explanation generation service using Claude with deterministic fallback.

Produces concise, recruiter-readable explanations explaining why a candidate is a
direct or adjacent fit, grounded strictly in computed evaluation metrics and verified candidate facts.
Never invents candidate facts or claims unverified credentials.
"""

from __future__ import annotations

import logging
from typing import Any

from app.ai.anthropic_client import ClaudeClient, get_claude_client
from app.database.schemas import CandidateEvaluation, JobRequirements, PersonRecord

logger = logging.getLogger(__name__)


def _clean_skill(skill: str) -> str:
    """Normalize skill string locally for display matching without cross-package imports."""
    return skill.strip().lower()

EXPLANATION_SYSTEM_PROMPT = """You are a hiring assistant generating a concise, factual 2-sentence candidate match explanation for a recruiter.

RULES:
1. Grounding: Rely strictly and only on the structured evaluation metrics and candidate facts provided.
2. Anti-hallucination: Never invent employers, dates, metrics, skills, or seniorities not present in the facts.
3. Verification: Never claim candidate facts or Crustdata profiles are "verified" or "independently confirmed".
4. Tone: Professional, direct, and factual. Avoid promotional adjectives like "rockstar", "exceptional", or "top performer".
5. For Adjacent Fit: Clearly highlight transferable capabilities and state the preferred (non-mandatory) criteria that were not evidenced.
6. Brevity: Keep the explanation to 2 concise sentences.
"""


def generate_deterministic_explanation(
    requirements: JobRequirements,
    candidate: PersonRecord,
    evaluation: CandidateEvaluation,
) -> str:
    """Generate an evidence-backed deterministic explanation without calling an LLM."""
    cand_title = candidate.current_title or candidate.headline or "Professional"
    fit_score = evaluation.fit_score or 0.0
    fit_type = evaluation.fit_type or "direct"

    # Identify matched must-haves
    cand_skills = {_clean_skill(s) for s in candidate.skills}
    for h in candidate.resume_highlights:
        if isinstance(h, dict):
            for t in h.get("technologies", []):
                cand_skills.add(_clean_skill(t))

    matched_must = [
        s for s in requirements.must_have_skills
        if _clean_skill(s) in cand_skills
    ]
    missing_pref = [
        s for s in requirements.preferred_skills
        if _clean_skill(s) not in cand_skills
    ]

    exp_text = (
        f"brings {candidate.experience_years:.1f} years of relevant experience"
        if candidate.experience_years is not None
        else "has demonstrated relevant professional experience"
    )

    if fit_type == "direct":
        skills_str = ", ".join(matched_must[:3]) if matched_must else "core technical requirements"
        sentence1 = (
            f"Strong direct fit ({fit_score:.1f}/100): Aligns with role '{requirements.title}' "
            f"and possesses mandatory skills in {skills_str}."
        )
        sentence2 = (
            f"Candidate {exp_text}."
        )
        explanation = f"{sentence1} {sentence2}"
    else:  # adjacent
        skills_str = ", ".join(matched_must[:3]) if matched_must else "transferable capabilities"
        pref_gap = f", though preferred {', '.join(missing_pref[:2])} is not documented" if missing_pref else ""
        sentence1 = (
            f"Transferable adjacent fit ({fit_score:.1f}/100): Background as '{cand_title}' "
            f"demonstrates transferable strength in {skills_str}."
        )
        sentence2 = (
            f"Meets all mandatory criteria with {exp_text}{pref_gap}."
        )
        explanation = f"{sentence1} {sentence2}"

    if evaluation.evidence_coverage is not None and evaluation.evidence_coverage < 0.50:
        explanation += " (Note: Limited profile evidence documented; details subject to recruiter review.)"

    return explanation


def generate_match_explanation(
    requirements: JobRequirements,
    candidate: PersonRecord,
    evaluation: CandidateEvaluation,
    client: ClaudeClient | None = None,
) -> str:
    """Generate a concise, evidence-grounded explanation for candidate fit.

    Uses Claude when available to polish wording, falling back to the deterministic
    template if Claude is unavailable, unconfigured, or returns an error.

    Args:
        requirements: Canonical job requirements.
        candidate: Candidate person record.
        evaluation: Computed candidate evaluation.
        client: Optional ClaudeClient instance.

    Returns:
        str: Concise, evidence-grounded 2-sentence explanation.
    """
    deterministic_text = generate_deterministic_explanation(requirements, candidate, evaluation)

    # Attempt LLM polish only if an active client is supplied or configured
    claude = client
    if claude is None:
        try:
            claude = get_claude_client()
        except Exception:
            # LLM not configured; use deterministic fallback directly
            return deterministic_text

    try:
        user_prompt = (
            f"Job Title: {requirements.title}\n"
            f"Candidate Current Title: {candidate.current_title or 'Unspecified'}\n"
            f"Fit Type: {evaluation.fit_type}\n"
            f"Fit Score: {evaluation.fit_score}\n"
            f"Component Scores: {evaluation.component_scores}\n"
            f"Must-Have Skills Matched: {requirements.must_have_skills}\n"
            f"Evaluation Reasons: {'; '.join(evaluation.reasons[:3])}\n"
            f"Draft Explanation: {deterministic_text}\n\n"
            "Polish the draft explanation into 2 concise, factual sentences for the recruiter card. "
            "Do not add any unverified or unstated facts."
        )

        polished = claude.generate_text(
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=150,
            temperature=0.2,
        )

        if polished and len(polished.strip()) > 20:
            return polished.strip()

    except Exception as exc:
        logger.warning("Claude explanation generation failed; using deterministic fallback: %s", exc)

    return deterministic_text
