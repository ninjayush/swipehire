"""AI parsing and explanation package (Person 2 owned).

Exposes Claude-backed services for JD parsing, resume parsing, and match explanations.
"""

from __future__ import annotations

from app.ai.anthropic_client import (
    AIAuthenticationError,
    AIConfigurationError,
    AIConnectionError,
    AIError,
    AIParsingError,
    AIRateLimitError,
    AIServerError,
    AITimeoutError,
    ClaudeClient,
    extract_json_payload,
    get_anthropic_client,
    get_anthropic_model,
    get_claude_client,
)
from app.ai.explanations import generate_match_explanation
from app.ai.jd_parser import parse_job_description
from app.ai.resume_parser import parse_resume_text

__all__ = [
    "AIAuthenticationError",
    "AIConfigurationError",
    "AIConnectionError",
    "AIError",
    "AIParsingError",
    "AIRateLimitError",
    "AIServerError",
    "AITimeoutError",
    "ClaudeClient",
    "extract_json_payload",
    "generate_match_explanation",
    "get_anthropic_client",
    "get_anthropic_model",
    "get_claude_client",
    "parse_job_description",
    "parse_resume_text",
]
