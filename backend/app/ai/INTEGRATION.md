# Person 2 — AI & Matching Integration Note

This document specifies the integration boundary, shared contracts, and public API signatures implemented by Person 2 (`backend/app/ai/` and `backend/app/matching/`).

## 1. Ownership Boundary

- **Person 2 owns:**
  - `backend/app/ai/`
  - `backend/app/matching/`
  - `backend/tests/ai/`
  - `backend/tests/matching/`
  - `backend/app/ai/INTEGRATION.md`
- **Person 1 owns:**
  - `backend/app/api/`
  - `backend/app/integrations/`
  - `backend/app/models/`
  - `backend/app/database/` (including canonical `schemas.py`)
  - `backend/app/main.py`, `backend/app/config.py`, `.env.example`, `requirements.txt`
- **Person 3 owns:**
  - `frontend/`

## 2. Shared Contracts Consumed

Person 2 imports canonical Pydantic models from `app.database.schemas` (never duplicates or modifies them):

- `JobRequirements`: Title, experience bounds, locations, work modes, must-have/preferred skills, mandatory/preferred qualifications, dealbreakers, unknown requirements, and raw JD.
- `PersonRecord`: Normalized candidate data from both registered members and Crustdata-sourced professionals.
- `CandidateEvaluation`: Eligibility, exclusion reasons, numeric fit score, component scores, evidence coverage, fit type (`direct` | `adjacent`), explanation, and rank.

## 3. Required Public Functions

All public functions are synchronous and conform strictly to the agreed signatures:

```python
# 1. Job Description Parsing (Claude)
from app.ai.jd_parser import parse_job_description

def parse_job_description(raw_jd: str) -> JobRequirements:
    ...

# 2. Resume Text Structuring (Claude)
from app.ai.resume_parser import parse_resume_text

def parse_resume_text(resume_text: str) -> dict:
    ...

# 3. Dynamic Deck Assembly (Deterministic Matching)
from app.matching.deck import build_candidate_deck

def build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]:
    ...
```

## 4. Architectural Separation

1. **Language tasks (Claude via Anthropic Messages API):**
   - Untrusted JD parsing and extraction into structured criteria.
   - Untrusted resume plain text structuring into projects, skills, metrics.
   - Natural language match explanation grounded strictly in verified evaluation metrics.
2. **Deterministic matching (Pure Python):**
   - Hard filter evaluation: Mandatory criteria fail closed; missing optional data remains unknown.
   - Fit scoring: 5 weighted components (Skills 30%, Experience 25%, Domain 20%, Trajectory 15%, Context 10%).
   - Direct vs. adjacent classification: Adjacent candidates must pass ALL hard filters; may miss preferred criteria only.
   - Deck allocation: Capped at maximum 20% adjacent candidates (max 4 in a 20-card deck). No filler.

## 5. Claude Client & Configuration Specification (Prompt 2 Deliverable)

### Dependency Required from Person 1
Person 1 owns `requirements.txt`. Please ensure the following dependency is listed:
```text
anthropic>=0.40.0
```

### Environment / Settings Variables
| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | *None* | Anthropic API authentication key. |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-20241022` | Claude model name for structured extraction and explanations. |
| `ANTHROPIC_TIMEOUT` | No | `30.0` | Finite timeout (seconds) for synchronous API requests. |

### Error Hierarchy (`app.ai.anthropic_client`)
- `AIError`: Root exception for all AI operations.
  - `AIConfigurationError`: Missing API key or configuration.
  - `AIAuthenticationError`: 401/403 credentials failure (non-retryable).
  - `AIRateLimitError`: 429 rate limit exceeded.
  - `AITimeoutError`: Finite timeout exceeded.
  - `AIConnectionError`: Network/transport connection error.
  - `AIServerError`: 5xx upstream service outage or overload.
  - `AIParsingError`: Payload validation failure after at most 1 repair attempt.

### Bounded Repair & Prompt Safety
- Documents are explicitly guarded as **untrusted data**. Prompts enforce prompt-injection immunity.
- Primary extraction uses Anthropic Tool Use / JSON Schema.
- If primary output is malformed, exactly **one** repair attempt is executed including the validation diagnostics.
- If repair fails, an `AIParsingError` is raised with a concise diagnostic. No infinite loops or unredacted credential leaks.
