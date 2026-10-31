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

# Common seniority keywords mapped to ordinal rank
SENIORITY_RANKS: dict[str, int] = {
    "intern": 1,
    "entry": 2,
    "junior": 2,
    "associate": 3,
    "mid": 4,
    "senior": 5,
    "sr": 5,
    "lead": 6,
    "staff": 7,
    "principal": 8,
    "director": 9,
    "head": 9,
    "vp": 10,
}


def normalize_skill(skill: str) -> str:
    """Normalize skill name: lowercase, strip punctuation/spaces, and map aliases."""
    if not skill:
        return ""
    cleaned = skill.strip().lower()
    cleaned = re.sub(r"[\.,\/#!$%\^&\*;:{}=\-_`~()]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
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


def normalize_title(title: str | None) -> str:
    """Clean and normalize a job title string."""
    if not title:
        return ""
    cleaned = title.strip().lower()
    cleaned = re.sub(r"[\.,\/#!$%\^&\*;:{}=\-_`~()]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def extract_seniority(text: str | None) -> str | None:
    """Extract standard seniority tier from text or title."""
    if not text:
        return None
    low = text.lower()
    for kw in sorted(SENIORITY_RANKS.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(kw)}\b", low):
            # Map sr -> senior, entry -> junior
            if kw == "sr":
                return "senior"
            if kw == "entry":
                return "junior"
            return kw
    return None


def calculate_token_overlap(str1: str, str2: str) -> float:
    """Calculate Jaccard similarity between two token sets (0.0 to 1.0)."""
    t1 = set(normalize_title(str1).split())
    t2 = set(normalize_title(str2).split())
    # Remove common filler words
    filler = {"and", "or", "the", "a", "an", "at", "for", "in", "of", "with"}
    t1 = t1 - filler
    t2 = t2 - filler
    if not t1 or not t2:
        return 0.0
    intersection = len(t1.intersection(t2))
    union = len(t1.union(t2))
    return float(intersection) / float(union) if union > 0 else 0.0
