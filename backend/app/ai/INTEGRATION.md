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

## 6. Job Description Parser Specification (Prompt 3 Deliverable)

### Public Signature
```python
from app.ai.jd_parser import parse_job_description
from app.database.schemas import JobRequirements

job_req: JobRequirements = parse_job_description(raw_jd: str)
```

### Output Semantics & Rules
1. **Mandatory vs. Preferred Separation**:
   - `must_have_skills` contains only explicitly compulsory skills (e.g., "Must have Python", "Required: PostgreSQL").
   - `preferred_skills` contains nice-to-have, bonus, or preferred skills. Overlapping skills in both lists are resolved by keeping the skill in `must_have_skills` and pruning it from `preferred_skills`.
2. **Explicit Dealbreakers & Required Candidate Fields**:
   - `dealbreakers` records hard geographic, authorization, or work mode mandates.
   - `required_fields` contains candidate fields (such as notice period or portfolio) only when explicitly demanded by the recruiter/JD.
3. **Ambiguities & Surfacing**:
   - Subjective phrases ("strong communication", "rockstar attitude") or contradictory statements ("junior role requiring 8 years") are placed in `unknown_or_needs_confirmation`. They are never converted into hard filters.
4. **Numeric Experience Bounds**:
   - `min_experience_years` and `max_experience_years` are parsed only when explicit numeric figures are stated. Vague phrases like "experienced" leave these fields `None`.
5. **Exact Preservation of Raw Text**:
   - `raw_jd` always contains the exact input text provided by the caller.

### Sample Validated Output
```json
{
  "title": "Senior Backend Engineer",
  "seniority": "Senior",
  "min_experience_years": 5.0,
  "max_experience_years": null,
  "locations": ["San Francisco, CA"],
  "work_modes": ["hybrid"],
  "must_have_skills": ["Python", "PostgreSQL", "Docker"],
  "preferred_skills": ["Kubernetes", "GraphQL"],
  "mandatory_qualifications": [],
  "preferred_qualifications": [],
  "required_fields": [],
  "dealbreakers": [],
  "unknown_or_needs_confirmation": [],
  "raw_jd": "Role: Senior Backend Engineer\n..."
}
```

## 7. Resume Parser Specification & Mapping Notes (Prompt 4 Deliverable)

### Public Signature
```python
from app.ai.resume_parser import parse_resume_text

resume_data: dict[str, Any] = parse_resume_text(resume_text: str)
```

### Output Contract
Returns a pure JSON-serializable Python dictionary:
- `skills`: `list[str]` (Explicitly supported technologies, deduplicated).
- `projects`: `list[dict]` (Project name, description, technologies, and explicit metrics).
- `achievements`: `list[str]` (Concrete awards, honors, publications).
- `metrics`: `list[str]` (Explicit numeric metrics preserved with units and context).
- `employment_history`: `list[dict]` (Company, title, start_date, end_date, is_current, role_type, highlights).
- `education`: `list[dict]` (Institution, degree, field_of_study, graduation_year).
- `summary`: `str | None` (Factual summary based strictly on resume facts).
- `extraction_warnings`: `list[str]` (Missing dates or ambiguous details flagged for review).

### Person 1 Schema Mapping Guide
Person 1 can map this output directly into `PersonRecord` fields without schema changes:
1. `PersonRecord.skills`: Map directly from `resume_data["skills"]`.
2. `PersonRecord.employment_history`: Map directly from `resume_data["employment_history"]`.
3. `PersonRecord.education`: Map directly from `resume_data["education"]`.
4. `PersonRecord.resume_highlights`: Populate using a list containing project highlights, metrics, and achievements:
   ```python
   resume_highlights = [
       {"type": "project", "name": p["name"], "metrics": p["metrics"]}
       for p in resume_data["projects"]
   ] + [
       {"type": "metric", "content": m} for m in resume_data["metrics"]
   ] + [
       {"type": "achievement", "content": a} for a in resume_data["achievements"]
   ]
   ```
5. `PersonRecord.source_metadata`: Append:
   ```python
   {"source": "resume_extracted", "warnings": resume_data["extraction_warnings"]}
   ```

### Sample Sanitized Output
```json
{
  "skills": ["Go", "Python", "FastAPI", "PostgreSQL", "Docker"],
  "projects": [
    {
      "name": "Distributed KV Store",
      "description": "Implemented Raft consensus in Go from scratch",
      "technologies": ["Go"],
      "metrics": ["Benchmarked throughput at 100k ops/sec"],
      "provenance": "resume_extracted"
    }
  ],
  "achievements": [],
  "metrics": [
    "Reduced API response latency by 40% across 50M daily requests",
    "Benchmarked throughput at 100k ops/sec"
  ],
  "employment_history": [
    {
      "company": "Synthetic Cloud Corp",
      "title": "Staff Backend Engineer",
      "start_date": "Jan 2022",
      "end_date": "Present",
      "is_current": true,
      "role_type": "full_time",
      "description": "Architected real-time event pipeline using Apache Kafka and Go",
      "highlights": ["Reduced API response latency by 40% across 50M daily requests"],
      "provenance": "resume_extracted"
    }
  ],
  "education": [
    {
      "institution": "University of Technology",
      "degree": "B.S.",
      "field_of_study": "Computer Science",
      "graduation_year": "2019",
      "provenance": "resume_extracted"
    }
  ],
  "summary": "Backend engineer specializing in distributed systems, Go, and cloud architecture.",
  "extraction_warnings": []
}
```
