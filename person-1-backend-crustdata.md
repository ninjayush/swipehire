# Person 1 — Backend, Database & Crustdata Integration

> **Antigravity task file.** Use this file together with the shared `context.md`, `to-do.md`, and `README.md`. This assignment is the source of truth for your workstream. Build only the backend foundation, data layer, Crustdata adapter, API routes, and orchestration glue described here.

## 1. Mission

Build the backend foundation that allows SwipeHire to:

1. Resolve/enrich a company using Crustdata.
2. Accept a job created from structured requirements or a parsed JD.
3. Discover registered and Crustdata-sourced people.
4. Normalize and deduplicate people into one canonical Person model.
5. Call the AI/matching modules built by Person 2.
6. Persist the candidate deck, exclusions, recruiter actions, interest requests, and mutual matches.
7. Expose stable REST APIs for the frontend built by Person 3.

You own the **backend integration boundary and shared contracts**. Person 2 owns the internal AI and matching algorithms. Person 3 owns the frontend.

## 2. Files you own

Create/modify only these areas unless the team explicitly agrees otherwise:

```text
backend/
  app/
    main.py
    config.py
    api/
      candidates.py
      companies.py
      jobs.py
      matches.py
    integrations/
      crustdata.py
    models/
      user.py
      person.py
      company.py
      job.py
      match.py
    database/
      db.py
      schemas.py       # shared Pydantic contracts defined below
    services/
      company_service.py
      person_service.py
      discovery_service.py
      action_service.py
  tests/
    test_crustdata_client.py
    test_identity_deduplication.py
    test_api_contracts.py
  uploads/              # runtime storage; do not commit uploaded personal files
  requirements.txt

.env.example           # root-level shared example; Person 1 owns it
```

**Do not edit:** `frontend/`, `backend/app/ai/`, `backend/app/matching/`, or the shared root `context.md`, `to-do.md`, and `README.md` unless asked. Person 2 owns `ai/` and `matching/`; Person 3 owns `frontend/`.

## 3. Technical choices

- Python 3.11+ and FastAPI.
- SQLAlchemy with SQLite for the prototype.
- Pydantic request/response schemas.
- `httpx` for asynchronous Crustdata requests.
- Load all secrets from environment variables.
- Keep Crustdata calls server-side. Never expose the key to the browser.
- Use a single backend application. Do not create microservices.

Required Crustdata headers:

```http
Authorization: Bearer <CRUSTDATA_API_KEY>
Content-Type: application/json
x-api-version: 2025-11-01
```

Base URL: `https://api.crustdata.com`.

## 4. Crustdata integration to implement

Implement typed wrappers in `backend/app/integrations/crustdata.py` for these core endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /person/enrich` | Enrich candidate from professional-network profile URL |
| `POST /person/search` | Discover external candidates |
| `POST /company/identify` | Resolve a company name/domain to its canonical Crustdata identity |
| `POST /company/enrich` | Enrich the identified company |

Optional endpoints (`company/search`, `job/search`, web search/fetch, Watcher) must not block the MVP. Do not call them unless the core workflow is already working.

### Client requirements

- Set a finite timeout on every request.
- Handle non-2xx responses and return useful, sanitized errors.
- Handle 401/403, 429, and transient 5xx responses distinctly.
- Use bounded retry/backoff only for retryable failures. Do not blindly retry bad requests.
- Read and preserve pagination cursors where the endpoint returns them.
- Support field selection so we request only what the UI/matching flow needs.
- Cache person/company enrichment by canonical identifier for the local prototype.
- Record request ID, endpoint, status, latency and credit metadata when returned. Never log API keys or full sensitive payloads.
- Normalize Crustdata payload variations in this adapter/service layer; frontend and matching code must not depend on raw response shapes.

At startup or during a diagnostics command, check account permissions/fields/rate limits/credits if those account endpoints are enabled. If not, print a clear warning and proceed with a small smoke test. Do not assume all fields/endpoints are enabled for the supplied key.

## 5. Shared data contracts — freeze these names

Person 2 and Person 3 will code against these contracts. Implement these Pydantic schemas in `backend/app/database/schemas.py` and send the file to the team as soon as it is stable. Keep names and field meanings unchanged unless the team agrees on a versioned change.

### `JobRequirements`

```python
class JobRequirements(BaseModel):
    title: str
    seniority: str | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    locations: list[str] = []
    work_modes: list[str] = []       # e.g. onsite, hybrid, remote
    must_have_skills: list[str] = []
    preferred_skills: list[str] = []
    mandatory_qualifications: list[str] = []
    preferred_qualifications: list[str] = []
    required_fields: list[str] = []  # e.g. availability, resume, salary
    dealbreakers: list[str] = []
    unknown_or_needs_confirmation: list[str] = []
    raw_jd: str | None = None
```

Use Pydantic `Field(default_factory=list)` in the real implementation, not mutable list defaults.

### `PersonRecord`

```python
class PersonRecord(BaseModel):
    person_id: str                         # SwipeHire canonical ID (UUID/string)
    crustdata_person_id: int | None = None
    profile_url: str | None = None
    origin: Literal["registered", "crustdata_sourced"]
    membership_status: Literal["registered", "not_registered"]
    name: str | None = None
    headline: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    location: str | None = None
    skills: list[str] = []
    experience_years: float | None = None
    employment_history: list[dict] = []
    education: list[dict] = []
    resume_highlights: list[dict] = []
    candidate_preferences: dict = {}
    source_metadata: list[dict] = []
```

### `CandidateEvaluation`

```python
class CandidateEvaluation(BaseModel):
    person_id: str
    eligible: bool
    exclusion_reasons: list[str] = []
    fit_score: float | None = None
    component_scores: dict[str, float] = {}
    evidence_coverage: float | None = None
    fit_type: Literal["direct", "adjacent"] | None = None
    match_explanation: str | None = None
    reasons: list[str] = []
    rank: int | None = None
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
    cards: list[dict]  # serialized PersonRecord + CandidateEvaluation
```

Person 2 may add internal schemas in their own package, but must consume/return the shared types above or provide explicit conversion functions. Do not duplicate the canonical schema in a second file.

## 6. Database models to implement

Use SQLAlchemy models for:

- `User`: registered candidate/recruiter account and role.
- `Person`: canonical identity; nullable Crustdata person ID and profile URL; `origin`; normalized profile JSON; timestamps.
- `CandidateProfile`: optional one-to-one relationship to a registered Person; target role and candidate-only preferences.
- `Resume`: file metadata, extracted text, parsed JSON, candidate profile relationship.
- `Company`: canonical Crustdata company ID, domain, name, enriched JSON.
- `CompanyMember`: recruiter-to-company relationship.
- `JobRole`: company, raw JD, structured `JobRequirements`, status.
- `MatchRun`: job, status, input hash, timestamps, counts and diagnostics.
- `CandidateMatch`: Person/Job/MatchRun association, component scores, fit score, fit type, filter results, reason, rank.
- `RecruiterAction`: `shortlist`, `pass`, or `save`.
- `InterestRequest`: pending recruiter interest for registered Person only.
- `Match`: created only after a registered candidate accepts.

**Identity is critical:** a Person is not the same thing as a User. Enforce unique constraints on non-null Crustdata person IDs and normalized professional-network URLs. When a sourced person registers, attach the new User/CandidateProfile to the existing Person; never create a duplicate Person.

Store source metadata and retrieval timestamps. Never fabricate resume, salary, availability, preferences, consent, or membership status for sourced candidates.

## 7. Backend REST routes to implement

These are SwipeHire routes, not Crustdata routes. Keep route names and request/response meanings consistent with this table because Person 3 will integrate against them.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/candidates/enrich` | Enrich a LinkedIn/profile URL |
| `POST` | `/api/candidates/register` | Register/link candidate and save preferences |
| `POST` | `/api/candidates/{id}/resume` | Upload resume and invoke Person 2's resume parser |
| `GET` | `/api/candidates/{id}` | Retrieve candidate profile |
| `POST` | `/api/companies/resolve` | Identify and enrich company |
| `POST` | `/api/jobs` | Create job from structured data or raw JD |
| `GET` | `/api/jobs` | List jobs for demo company |
| `POST` | `/api/jobs/{id}/discover` | Run discovery and matching workflow |
| `GET` | `/api/jobs/{id}/deck` | Retrieve ranked candidate cards |
| `GET` | `/api/jobs/{id}/shortlist` | Retrieve shortlist |
| `POST` | `/api/jobs/{id}/actions` | Shortlist/pass/save candidate |
| `GET` | `/api/candidates/{id}/interests` | Candidate's incoming interest requests |
| `POST` | `/api/interests/{id}/respond` | Candidate accepts/rejects interest |
| `GET` | `/api/matches` | List mutual matches |

### Request/response conventions

**Enrich candidate**

Request:
```json
{"profile_url":"https://www.linkedin.com/in/example/"}
```
Response:
```json
{"person": {"person_id":"...","name":"...","origin":"crustdata_sourced","membership_status":"not_registered"}}
```

**Resolve company**

Request:
```json
{"company_name":"Example Inc","domain":"example.com"}
```
Only one identifier is required. Return canonical company ID and a short summary; if identity is ambiguous, return choices rather than silently selecting a weak match.

**Create job**

Request (JD mode):
```json
{"company_id":"...","input_type":"jd","raw_jd":"..."}
```
Request (structured mode):
```json
{"company_id":"...","input_type":"structured","requirements":{}}
```
Response contains `job_id`, parsed/validated `requirements`, and a status. Call Person 2's `parse_job_description(raw_jd)` for JD mode.

**Discover candidates**

`POST /api/jobs/{id}/discover` runs synchronously for the prototype. It should:
1. Query registered candidates.
2. Call Crustdata Person Search.
3. Enrich a bounded set of relevant external profiles.
4. Normalize and deduplicate both pools.
5. Call Person 2's matching/deck function.
6. Persist eligible cards, exclusions and run metadata.
7. Return `CandidateDeckResponse` or a compact run summary; the frontend then calls `GET /deck`.

**Recruiter action**

Request:
```json
{"person_id":"...","action":"shortlist"}
```
`action` is `shortlist`, `pass`, or `save`. For a registered candidate, `shortlist` creates a pending `InterestRequest`. For a non-member, `shortlist` creates only an internal recruiter action. Non-members cannot receive notifications or be matched.

**Candidate response**

Request:
```json
{"response":"accept"}
```
`response` is `accept` or `reject`. Create a `Match` only after an accepted response for a registered candidate.

## 8. Integration with Person 2's modules

Person 2 owns:

```text
backend/app/ai/
  anthropic_client.py
  jd_parser.py
  resume_parser.py
  explanations.py
backend/app/matching/
  filters.py
  scoring.py
  classification.py
  deck.py
```

Expected public functions (agree before implementation):

```python
parse_job_description(raw_jd: str) -> JobRequirements
parse_resume_text(resume_text: str) -> dict
build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]
```

The tuple is `(displayed_evaluations, excluded_evaluations)`. If Person 2 needs async functions, make them consistently `async def` and tell the team before integration. Person 1 owns the route/orchestration that calls these functions; Person 2 must not edit route files.

## 9. Minimal demo identity / authentication

No third-party OAuth login is part of this MVP. Implement a simple local demo mode with seeded recruiter and candidate users, or a development-only demo identity mechanism. Clearly isolate it so it can be replaced by real authentication later. Do not build LinkedIn OAuth; the LinkedIn URL is an enrichment input, not a login credential.

## 10. Tests and acceptance criteria

- [ ] Backend starts with documented commands.
- [ ] Core Crustdata smoke tests work with supplied key (or fail with clear sanitized diagnostics).
- [ ] Required Crustdata headers are attached to every call.
- [ ] Company Identify → Company Enrich works.
- [ ] Person Enrich works with a profile URL.
- [ ] Person Search produces normalized PersonRecords.
- [ ] Pagination, timeouts, rate limits and missing fields are handled.
- [ ] Duplicate Crustdata/profile URL identities merge into one Person.
- [ ] A sourced Person can later be linked to a registered User without losing prior actions.
- [ ] All internal routes match the contract in Section 7.
- [ ] Discovery calls Person 2's matching module rather than reimplementing scoring.
- [ ] Non-members can be saved/shortlisted but cannot get interest requests or mutual matches.
- [ ] A registered candidate can accept/reject interest; only acceptance creates Match.
- [ ] Sanitized fixtures are used in tests. No API keys or actual uploaded resumes are committed.

## 11. Git / merge rules

- Work on branch: `work/person-1-backend`.
- Commit only your owned paths plus `backend/requirements.txt` and root `.env.example`.
- Do not modify root `context.md`, `to-do.md`, `README.md`, or the other two workstreams' files.
- Commit the shared Pydantic schemas early and send the exact file/API contract to Persons 2 and 3.
- Use small commits: `backend: add shared contracts`, `backend: add Crustdata client`, `backend: add company/person routes`, etc.
- Before merge, run backend tests and provide a short integration note listing routes, environment variables, and any API fields that were unavailable.

## 12. Antigravity instruction

Read the shared `context.md`, `to-do.md`, and `README.md` completely before editing. Follow this assignment, preserve the locked product decisions, and implement real working backend code rather than mock-only endpoints. Where Crustdata account permissions or live response details are unknown, probe the supplied API safely and document the observed behavior; do not invent response fields. Keep all API credentials in environment variables.
