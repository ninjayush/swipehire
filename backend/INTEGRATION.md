# SwipeHire — Backend Integration & Contract Guide

This document is the complete handoff for **Person 2 (AI/Matching)** and **Person 3 (Frontend)**. It details setup instructions, frozen schemas, internal API routes, and integration boundaries.

---

## 1. Setup & Execution Commands

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Installation
```bash
cd backend
pip install -r requirements.txt
```

### Running the API Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- Health Probe: `http://localhost:8000/health`

### Running Automated Tests
```bash
# Run full unit/mock test suite (runs 100% offline)
python -m pytest tests

# Optional: Run live Crustdata smoke tests (requires active API key)
$env:CRUSTDATA_LIVE_TEST="true"; python -m pytest tests
```

### Crustdata Diagnostics Probe
```bash
python -m app.integrations.diagnostics
```

---

## 2. Environment Variables

Store in `.env` in the repository root (do **not** commit `.env`):

| Variable | Required | Default | Description |
|---|---|---|---|
| `CRUSTDATA_API_KEY` | **Yes** | `""` | Crustdata Bearer API key |
| `DATABASE_URL` | No | `sqlite:///swipehire.db` | SQLite database URI |
| `PORT` | No | `8000` | FastAPI server port |
| `HOST` | No | `0.0.0.0` | FastAPI bind address |
| `UPLOAD_DIR` | No | `./uploads` | Directory for resume storage |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed origins for Next.js frontend |
| `ANTHROPIC_API_KEY` | For Person 2 | `""` | Anthropic Claude API key |

---

## 3. Public Shared Pydantic Contracts (Frozen)

Location: `backend/app/database/schemas.py`

### `JobRequirements`
```python
class JobRequirements(BaseModel):
    title: str
    seniority: str | None = None
    min_experience_years: float | None = Field(default=None, ge=0.0)
    max_experience_years: float | None = Field(default=None, ge=0.0)
    locations: list[str] = Field(default_factory=list)
    work_modes: list[str] = Field(default_factory=list)        # e.g. ["onsite", "hybrid", "remote"]
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    mandatory_qualifications: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)   # e.g. ["availability", "resume"]
    dealbreakers: list[str] = Field(default_factory=list)
    unknown_or_needs_confirmation: list[str] = Field(default_factory=list)
    raw_jd: str | None = None
```

### `PersonRecord`
```python
class PersonRecord(BaseModel):
    person_id: str                         # Canonical UUID string
    crustdata_person_id: int | None = None
    profile_url: str | None = None
    origin: Literal["registered", "crustdata_sourced"]
    membership_status: Literal["registered", "not_registered"]
    name: str | None = None
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: float | None = Field(default=None, ge=0.0)
    employment_history: list[dict[str, Any]] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    resume_highlights: list[dict[str, Any]] = Field(default_factory=list)
    candidate_preferences: dict[str, Any] = Field(default_factory=dict)
    source_metadata: list[dict[str, Any]] = Field(default_factory=list)
```

### `CandidateEvaluation`
```python
class CandidateEvaluation(BaseModel):
    person_id: str
    eligible: bool
    exclusion_reasons: list[str] = Field(default_factory=list)
    fit_score: float | None = Field(default=None, ge=0.0, le=100.0)
    component_scores: dict[str, float] = Field(default_factory=dict)
    evidence_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    fit_type: Literal["direct", "adjacent"] | None = None
    match_explanation: str | None = None
    reasons: list[str] = Field(default_factory=list)
    rank: int | None = Field(default=None, ge=1)
    evidence: list[EvidenceItem] = Field(default_factory=list)
```

### `CandidateDeckResponse`
```python
class CandidateDeckResponse(BaseModel):
    job_id: str
    match_run_id: str
    status: Literal["completed", "failed", "processing"]
    total_candidates: int
    direct_count: int
    adjacent_count: int
    excluded_count: int
    cards: list[dict[str, Any]]  # [{"person": PersonRecord, "evaluation": CandidateEvaluation}]
```

---

## 4. Person 2 Integration Functions

Person 2 implements the following functions in `backend/app/ai/` and `backend/app/matching/`:

```python
# In app/ai/jd_parser.py
parse_job_description(raw_jd: str) -> JobRequirements

# In app/ai/resume_parser.py
parse_resume_text(resume_text: str) -> dict

# In app/matching/deck.py (Sync or async def supported)
build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]
# Returns: (displayed_evaluations, excluded_evaluations)
```

---

## 5. REST API Route Directory for Person 3 Frontend

### Company Endpoints
- **`POST /api/companies/resolve`**
  - Request: `{"company_name": "Stripe", "domain": "stripe.com"}` (either field)
  - Response: `{"company_id": "...", "name": "Stripe", "domain": "stripe.com", "enriched": {...}, "ambiguous_options": []}`

### Job Endpoints
- **`POST /api/jobs`**
  - Structured Request: `{"company_id": "...", "input_type": "structured", "requirements": {...}}` (status: `"active"`)
  - JD Request: `{"company_id": "...", "input_type": "jd", "raw_jd": "..."}` (status: `"needs_confirmation"`)
  - Response: `{"job_id": "...", "company_id": "...", "status": "active", "requirements": {...}}`
- **`GET /api/jobs`**
  - List all active/draft jobs.
- **`PATCH /api/jobs/{id}`**
  - Request: `{"title": "...", "status": "active", "requirements": {...}}`
- **`POST /api/jobs/{id}/discover`**
  - Triggers candidate search, enrichment, deduplication, scoring, and returns `CandidateDeckResponse`.
- **`GET /api/jobs/{id}/deck`**
  - Returns ranked cards for recruiter swipe deck.
- **`GET /api/jobs/{id}/shortlist`**
  - Returns shortlisted candidates for the job.
- **`POST /api/jobs/{id}/actions`**
  - Request: `{"person_id": "...", "action": "shortlist" | "pass" | "save"}`
  - Sourced non-members: internal shortlist only.
  - Registered candidates: generates pending `InterestRequest`.

### Candidate Endpoints
- **`POST /api/candidates/enrich`**
  - Request: `{"profile_url": "https://linkedin.com/in/..."}`
  - Response: `{"person": PersonRecord}`
- **`POST /api/candidates/register`**
  - Request: `{"email": "...", "name": "...", "profile_url": "...", "candidate_preferences": {...}}`
- **`POST /api/candidates/{id}/resume`**
  - Multipart upload (`.pdf` or `.docx` only, max 5MB).
- **`GET /api/candidates/{id}`**
  - Returns canonical candidate profile.
- **`GET /api/candidates/{id}/interests`**
  - Pending interest requests for registered candidate.
- **`POST /api/interests/{id}/respond`**
  - Request: `{"response": "accept" | "reject"}`
  - On accept: generates mutual match (idempotent).
- **`GET /api/matches`**
  - List mutual matches (`[{"match_id": "...", "job_title": "...", "candidate_name": "..."}]`).

---

## 6. Seed / Demo Data
On startup, if the database is fresh, the backend automatically seeds:
- Demo Company: `"Demo Corp"` (`democorp.io`)
- Demo Recruiter: `"Alex Recruiter"` (`recruiter@democorp.io`)
- Demo Job: `"Senior Full-Stack Engineer"`
