"""Anthropic client wrapper and error types for Person 2 AI services.

Uses the synchronous Anthropic client with configurable timeouts and environment variables.
Never hardcodes keys or model names.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_TIMEOUT_SECONDS = 30.0


class AIError(Exception):
    """Base exception for AI parsing and generation errors."""


class AIConfigurationError(AIError):
    """Raised when required Anthropic credentials or configurations are missing."""


class AIParsingError(AIError):
    """Raised when an LLM response cannot be parsed into expected structured data."""


def get_anthropic_model() -> str:
    """Return configured model name or default."""
    return os.environ.get("ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL


def get_anthropic_client(
    api_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> anthropic.Anthropic:
    """Return an authenticated synchronous Anthropic client.

    Raises:
        AIConfigurationError: if ANTHROPIC_API_KEY is missing.
    """
    effective_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not effective_key:
        raise AIConfigurationError(
            "ANTHROPIC_API_KEY is not set. Please provide it via environment variable or argument."
        )
    return anthropic.Anthropic(api_key=effective_key, timeout=timeout)


def extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Defensively extract JSON from markdown fences or raw string."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if match:
            cleaned = match.group(1).strip()

    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise AIParsingError(f"Expected JSON object, got {type(data).__name__}")
        return data
    except json.JSONDecodeError as exc:
        raise AIParsingError(f"Failed to decode JSON from model output: {exc}") from exc
