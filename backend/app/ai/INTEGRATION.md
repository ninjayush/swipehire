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
