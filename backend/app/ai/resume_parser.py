"""Resume parsing service using Claude.

Extracts structured candidate highlights (skills, projects, achievements,
metrics, education) from pre-extracted resume plain text.
"""

from __future__ import annotations

from typing import Any


def parse_resume_text(resume_text: str) -> dict[str, Any]:
    """Parse extracted plain text of a resume into structured dictionary data.

    Expected output shape:
    {
        "skills": list[str],
        "projects": list[dict],
        "achievements": list[dict],
        "experience_summary": str | None,
        "education": list[dict],
        "certifications": list[dict]
    }

    Args:
        resume_text: Extracted plain text from candidate resume.

    Returns:
        dict[str, Any]: Structured representation of resume facts.

    Raises:
        ValueError: If resume_text is empty or whitespace.
        NotImplementedError: Raised in scaffolding until full extraction pipeline is implemented.
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must not be empty or whitespace only.")

    raise NotImplementedError(
        "Resume structuring pipeline with Claude is scheduled for implementation in a subsequent prompt."
    )
