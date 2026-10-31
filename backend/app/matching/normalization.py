"""Candidate and requirement normalization utilities.

Provides deterministic helpers to normalize skills, aliases, locations,
and job title variants without external paid services.
"""

from __future__ import annotations

import re

# Small canonical synonym map for common tech skills & domain aliases
CANONICAL_SKILL_SYNONYMS: dict[str, str] = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "dl": "deep learning",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "postgres": "postgresql",
    "reactjs": "react",
    "nextjs": "next.js",
    "vuejs": "vue",
    "golang": "go",
}


def normalize_skill(skill: str) -> str:
    """Normalize skill name: lowercase, strip punctuation/spaces, and map aliases."""
    if not skill:
        return ""
    cleaned = skill.strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Check synonym map
    return CANONICAL_SKILL_SYNONYMS.get(cleaned, cleaned)


def normalize_skills(skills: list[str]) -> list[str]:
    """Deduplicate and normalize a list of skill strings while preserving uniqueness."""
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        norm = normalize_skill(s)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def normalize_location(location: str | None) -> str:
    """Normalize location string for deterministic comparison."""
    if not location:
        return ""
    cleaned = location.strip().lower()
    cleaned = re.sub(r"[,\-\/]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()
