"""Job Description (JD) parsing service using Claude.

Converts untrusted raw JD text into validated JobRequirements.
"""

from __future__ import annotations

from app.database.schemas import JobRequirements


def parse_job_description(raw_jd: str) -> JobRequirements:
    """Parse raw job description text into validated JobRequirements.

    Args:
        raw_jd: Raw text of the job description.

    Returns:
        JobRequirements: Canonical schema populated with extracted fields.

    Raises:
        ValueError: If raw_jd is empty or whitespace.
        NotImplementedError: Raised in scaffolding until Prompt 2 implements the full extraction pipeline.
    """
    if not raw_jd or not raw_jd.strip():
        raise ValueError("raw_jd must not be empty or whitespace only.")

    raise NotImplementedError(
        "Job description parsing pipeline with Claude is scheduled for implementation in Prompt 2."
    )
