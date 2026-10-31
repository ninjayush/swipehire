# SwipeHire — Person 1: Six Sequential Antigravity Implementation Prompts

These six prompts are for **Person 1 — Backend, Database & Crustdata Integration**. Run them in order in the same repository/work branch. They are intentionally split into small, verifiable increments so the backend can be integrated with Person 2's AI/matching work and Person 3's frontend with minimal merge conflicts.

## How to use this file

1. Keep the following five reference files in the repository root (or their agreed shared location):
   - `context.md`
   - `README.md` (or `readme.md`)
   - `to-do.md`
   - `person-1-backend-crustdata.md`
   - The complete combined Crustdata LLM documentation Markdown file supplied to the team.
2. Paste **one prompt at a time** into Antigravity. Do not run Prompt 2 until Prompt 1's acceptance checks pass, and so on.
3. Use the same Git branch for all six prompts: `work/person-1-backend`.
4. Person 1 owns the backend foundation, data models, shared Pydantic contracts, Crustdata adapter, backend routes and orchestration glue. Person 2 owns `backend/app/ai/` and `backend/app/matching/`. Person 3 owns `frontend/`.
5. Do not change locked product decisions or invent Crustdata fields, response shapes, filter values or endpoint permissions.

---

# Prompt 1 of 6 — Repository audit and backend foundation

```text
You are implementing Person 1's SwipeHire workstream: Backend, Database & Crustdata Integration.

FIRST: Read all five project reference files completely:
1. context.md
2. README.md (or readme.md)
3. to-do.md
4. person-1-backend-crustdata.md
5. The complete combined Crustdata LLM documentation Markdown file supplied to the team.

Treat context.md as the product source of truth, person-1-backend-crustdata.md as the ownership/implementation brief, README.md as the architecture reference, to-do.md as the project checklist, and the combined Crustdata docs as the source of truth for API request/response details. If any file is missing, report that fact and inspect the files that are present; do not fabricate its content.

TASK
Audit the existing repository, then implement the backend foundation only. Do not merely propose a plan.

OWNERSHIP BOUNDARIES
- You own backend foundation, backend configuration, database setup, shared Pydantic contracts, Crustdata adapter, backend routes and backend orchestration glue.
- Do not edit frontend/.
- Do not implement or edit backend/app/ai/ or backend/app/matching/; Person 2 owns those packages.
- Do not rewrite the shared context.md, README.md or to-do.md.
- Do not create microservices or replace the agreed stack.

TECHNOLOGY
- Python 3.11+
- FastAPI
- SQLAlchemy with SQLite for the prototype
- Pydantic schemas
- httpx for async external API requests
- Secrets loaded from environment variables

IMPLEMENT
1. Inspect the repository before creating files. Preserve existing valid work and report any structure mismatch.
2. Create or complete the backend package structure specified in person-1-backend-crustdata.md.
3. Add backend/app/config.py using environment-based settings. Support at least:
   - CRUSTDATA_API_KEY
   - ANTHROPIC_API_KEY (configuration only; do not implement Person 2's LLM module)
   - ANTHROPIC_MODEL
   - DATABASE_URL (default to a local SQLite database)
   - UPLOAD_DIR
   - CORS/frontend origin configuration
4. Add backend/app/database/db.py with SQLAlchemy engine, session factory, declarative base and a safe database initialization function.
5. Add backend/app/main.py with FastAPI app creation, router registration placeholders where needed, CORS for the local frontend development origin, and GET /health.
6. Add backend/requirements.txt with the backend dependencies only. Do not add duplicate or unnecessary packages. Coordinate any resume-parser dependency with Person 2 rather than reimplementing their parser.
7. Add root .env.example containing variable names and safe blank/example values only. Never put real keys in it.
8. Add or update .gitignore for .env files, SQLite databases, uploads, Python caches, virtual environments, frontend build output and local model caches. Do not commit uploaded resumes or API response dumps containing personal data.
9. Add a short backend setup section in a backend-owned document only if needed; do not edit the shared README.

QUALITY REQUIREMENTS
- The backend must import and start cleanly.
- Use clear package imports and avoid circular imports.
- Keep settings in one place.
- Do not expose any secret through an endpoint or frontend environment variable.
- Do not add fake business logic or mock-only API routes.

VERIFY
- Create/activate a Python virtual environment if practical.
- Install requirements if the environment permits.
- Run a Python import check and start FastAPI.
- Verify GET /health returns a small JSON healthy response.
- If dependencies cannot be installed, state the exact blocker and still run static/import checks possible in the environment.

ACCEPTANCE CHECKS
- backend/app/main.py starts with the documented uvicorn command.
- GET /health works.
- Database engine/session initialization works against SQLite.
- .env.example contains no real credentials.
- No files under frontend/, backend/app/ai/ or backend/app/matching/ were edited.

At the end, report: files created/changed, commands run, test results, unresolved issues and the exact next step. Make a small commit on work/person-1-backend with message: `backend: scaffold FastAPI foundation` if Git is available and the branch is correct.
```

**Expected output:** A runnable FastAPI foundation, environment configuration, database connection and health endpoint. No Crustdata logic yet.

---

# Prompt 2 of 6 — Freeze shared Pydantic contracts and build the database models

```text
Continue Person 1's SwipeHire backend work. Before editing, re-read context.md, person-1-backend-crustdata.md, README.md, to-do.md and the complete combined Crustdata LLM documentation Markdown file. Inspect the code produced by Prompt 1 and preserve it.

TASK
Implement the shared Pydantic contracts and SQLAlchemy data model. These contracts are the integration boundary for Person 2 (AI/matching) and Person 3 (frontend), so consistency is more important than adding extra fields.

OWNERSHIP
- You own backend/app/database/schemas.py and backend/app/models/.
- Do not edit frontend/, backend/app/ai/, backend/app/matching/ or the shared root documentation files.
- Do not implement the scoring algorithm, JD parser or resume parser.

A. SHARED PYDANTIC CONTRACTS
Implement the exact canonical names and meanings defined in person-1-backend-crustdata.md:

1. JobRequirements
   - title
   - seniority
   - min_experience_years
   - max_experience_years
   - locations
   - work_modes
   - must_have_skills
   - preferred_skills
   - mandatory_qualifications
   - preferred_qualifications
   - required_fields
   - dealbreakers
   - unknown_or_needs_confirmation
   - raw_jd

2. PersonRecord
   - person_id (SwipeHire canonical ID)
   - crustdata_person_id
   - profile_url
   - origin: registered | crustdata_sourced
   - membership_status: registered | not_registered
   - name, headline, current_title, current_company, location
   - skills, experience_years, employment_history, education
   - resume_highlights, candidate_preferences, source_metadata

3. CandidateEvaluation
   - person_id
   - eligible
   - exclusion_reasons
   - fit_score
   - component_scores
   - evidence_coverage
   - fit_type: direct | adjacent | null
   - match_explanation
   - reasons
   - rank

4. CandidateDeckResponse
   - job_id
   - match_run_id
   - status: completed | failed | processing
   - total_candidates
   - direct_count
   - adjacent_count
   - excluded_count
   - cards

Also define typed request/response schemas for the backend routes listed in person-1-backend-crustdata.md. Keep the public field names stable for Person 3.

Use Pydantic Field(default_factory=list/dict) for collection defaults. Add validation for enums, score bounds (0–100), non-negative experience and required identifiers. Do not use mutable literal defaults.

B. SQLALCHEMY MODELS
Implement the models from the shared spec:
- User
- Person
- CandidateProfile
- Resume
- Company
- CompanyMember
- JobRole
- MatchRun
- CandidateMatch
- RecruiterAction
- InterestRequest
- Match
- EvidenceItem (optional but recommended)

Requirements:
- Person is a canonical professional identity and is NOT the same as a registered User.
- A Crustdata-sourced Person may exist without a User or CandidateProfile.
- A registered candidate User/CandidateProfile links to a Person.
- Enforce uniqueness for non-null crustdata_person_id and normalized professional-network profile URL.
- Store origin and membership state explicitly.
- Store normalized profile JSON and relevant source metadata/retrieval timestamps.
- Store raw JD and structured JobRequirements on JobRole.
- Persist match run status, counts and diagnostics.
- Persist candidate score components, hard-filter results, exclusion reasons, fit type, explanation and rank.
- Restrict InterestRequest to registered people at the service layer; do not rely only on frontend restrictions.
- Create Match only after a registered candidate accepts interest.
- Use foreign keys, relationships and indexes sensibly.

C. DATABASE INITIALIZATION
- Register/import all models so create_all sees them.
- Implement prototype-friendly schema initialization. If Alembic is already configured, use it; do not introduce a complex migration system unnecessarily.
- Add a deterministic seed mechanism for demo recruiter/candidate/company records only if it helps testing. Clearly mark seed data as demo data.

D. TESTS
Add tests for:
- Pydantic contract validation and defaults.
- Person/User separation.
- unique Crustdata ID/profile URL constraints.
- JobRequirements persistence/round-trip.
- Relationships between job, match run, person and candidate match.
- Interest/match model constraints that can be enforced at the database level.

ACCEPTANCE CHECKS
- All canonical Pydantic model names match the person-1 assignment exactly.
- Person 2 can import JobRequirements, PersonRecord and CandidateEvaluation from the agreed schemas module.
- Person 3 can use the documented request/response schemas without knowing raw Crustdata payloads.
- SQLite tables initialize successfully.
- Tests pass.

IMPORTANT HANDOFF
After implementing, print the complete public schema definitions and a concise field-by-field contract summary for Persons 2 and 3. Do not rename or silently change fields later. If you discover a necessary contract change, explain it and ask the team before making a breaking change.

Commit with message: `backend: add shared schemas and database models` if Git is available and the branch is correct.
```

**Expected output:** Stable shared contracts and a functioning database model layer. Send `schemas.py` to Persons 2 and 3 immediately after this prompt passes.

---

# Prompt 3 of 6 — Implement the Crustdata API client and diagnostics

```text
Continue Person 1's SwipeHire backend. Re-read the five project reference files, especially the complete combined Crustdata LLM documentation Markdown file. Inspect the API schemas created in Prompt 2 and do not change their public meaning.

TASK
Implement the production-minded, backend-only Crustdata adapter for the four core endpoints:
- POST /person/enrich
- POST /person/search
- POST /company/identify
- POST /company/enrich

The exact request body, supported field groups, required identifier formats, response nesting, filters, pagination and error details MUST be taken from the supplied combined Crustdata docs. Do not guess them. If the full docs do not specify a detail, inspect the corresponding reference linked by the docs if network access is available; otherwise isolate the uncertainty and do not invent a payload.

CLIENT LOCATION
backend/app/integrations/crustdata.py

API CONFIGURATION
Base URL: https://api.crustdata.com
Headers on every request:
- Authorization: Bearer <CRUSTDATA_API_KEY>
- Content-Type: application/json
- x-api-version: 2025-11-01

IMPLEMENT
1. Create a reusable asynchronous httpx client with configurable finite timeout and connection limits.
2. Add typed methods for:
   - person_enrich(profile_urls, fields=...)
   - person_search(query/filters/fields/limit/cursor as supported by the docs)
   - company_identify(name/domain or other documented supported identifier)
   - company_enrich(company identifiers, fields=...)
3. Build request payloads according to the supplied API docs. Enforce the documented rule that exactly one identifier type is sent where required.
4. Preserve raw JSON at the adapter boundary for debugging/tests, but do not let raw Crustdata shapes leak into API routes, SQLAlchemy models or Person 2's matching module.
5. Create typed/internal response wrappers for results, pagination cursor and safe metadata. Account for documented response variants only; do not add speculative parsing branches.
6. Handle HTTP errors distinctly:
   - 400: invalid request/field/filter; return a sanitized actionable error; do not retry.
   - 401: invalid/missing credentials; clear auth error; do not retry.
   - 403: endpoint/field permission denied; report the exact denied capability without leaking secrets; do not retry.
   - 429: bounded retry using documented Retry-After/rate-limit behavior where present; avoid infinite retries.
   - 5xx/timeouts: bounded retry with exponential backoff and jitter for safe read/search/enrichment calls only.
7. Do not blindly retry non-retryable client errors.
8. Capture request ID, endpoint, HTTP status, latency and credit metadata from response headers when available. Never log API keys or full profile payloads.
9. Add caching for person/company enrichment keyed by canonical identifier with a configurable TTL. Use an existing project cache if present; otherwise implement a simple SQLite-backed or in-process TTL cache appropriate for the prototype. Make cache behavior explicit and testable.
10. Implement pagination support for Person Search using the exact documented cursor field and response shape. Support a bounded result count to avoid uncontrolled API spend.
11. Add a diagnostics script/command that, where documented and enabled, checks endpoint permissions, enabled fields, effective rate limits and remaining credits. If account diagnostics are not enabled, show a warning and continue with small smoke tests.
12. Add a safe configuration path for field selection. Request only fields needed for candidate discovery/profile display; do not request contact details.

SMOKE TESTS
Create opt-in live smoke tests controlled by environment variables. Do not make ordinary pytest depend on a live API key.
Test each core endpoint with a small, permitted example only if the team provides the necessary identifiers. If no test identifier is provided, build the test harness and clearly report which live check remains unrun.

UNIT TESTS
Use mocked httpx responses/sanitized fixtures to verify:
- exact headers and base URL;
- correct endpoint paths and payload shape;
- successful response parsing;
- cursor propagation;
- 400/401/403/429/5xx handling;
- bounded retries;
- no secret or raw PII logging;
- cache hit/miss behavior.

ACCEPTANCE CHECKS
- All four wrapper methods work with mocked fixtures.
- Every request contains the required API version header.
- API key is read from server environment only.
- Person Search pagination is bounded and cursor-aware.
- Error messages are safe and useful.
- No optional endpoint is required for the core MVP.

Do not implement Company/Person service logic or backend routes in this prompt. Keep this prompt focused on the API adapter and tests.

Commit with message: `backend: implement Crustdata client and diagnostics` if Git is available and the branch is correct.
```

**Expected output:** A reusable Crustdata client that can be tested offline and safely smoke-tested against the supplied API key.

---

# Prompt 4 of 6 — Company/person services, identity normalization and onboarding routes

```text
Continue Person 1's SwipeHire backend. Read all five reference files, inspect the implemented client and schemas, and preserve their public contracts.

TASK
Build the company and person domain services and the corresponding onboarding routes. This prompt should turn raw Crustdata responses into canonical SwipeHire records.

OWNERSHIP
You own:
- backend/app/services/company_service.py
- backend/app/services/person_service.py
- backend/app/api/companies.py
- backend/app/api/candidates.py
- related tests

Person 2 owns the resume parser implementation under backend/app/ai/. You own the upload endpoint and its persistence/orchestration boundary, not the parsing algorithm. Do not edit the ai/ or matching/ packages.

A. COMPANY RESOLUTION
Implement POST /api/companies/resolve:
1. Accept company_name OR domain according to the agreed internal request schema.
2. Call Crustdata Company Identify using the exact documented payload.
3. Parse match candidates and confidence in the service layer.
4. If there is no reliable result or multiple plausible matches, return an ambiguity response with choices. Never silently attach a recruiter to a weak/ambiguous company.
5. Once the recruiter/company match is confirmed, call Company Enrich with the canonical Crustdata company ID and selected available field groups.
6. Upsert the Company by canonical Crustdata identity and persist normalized fields plus source metadata and retrieval time.
7. Link the demo recruiter to the resolved Company through CompanyMember.

B. PERSON ENRICHMENT AND NORMALIZATION
Implement POST /api/candidates/enrich:
1. Accept a professional-network profile URL.
2. Validate URL format and reject unsupported or malformed URLs cleanly.
3. Call Crustdata Person Enrich with documented fields only.
4. Normalize the returned profile to the canonical PersonRecord schema. Handle nullable/missing fields and only response shapes verified by docs/fixtures.
5. Preserve provenance: origin=crustdata_sourced and membership_status=not_registered for a person without a SwipeHire account.
6. Upsert Person by Crustdata person ID and normalized profile URL. Handle uniqueness races safely.
7. Return a normalized preview for candidate confirmation. Do not treat LinkedIn URL as authentication.

C. PERSON IDENTITY AND REGISTRATION LINKING
Implement a reusable upsert/link method:
- First look up by non-null crustdata_person_id.
- Also look up by normalized profile URL.
- If both resolve to different Person rows, detect the conflict and reconcile safely; do not create a third row or silently merge unrelated identities.
- When a sourced person registers, attach User and CandidateProfile to the existing canonical Person.
- Preserve recruiter actions/match-run history attached to that Person.
- Enforce one canonical Person per Crustdata identity/profile URL.

Implement POST /api/candidates/register and GET /api/candidates/{id}. Use a simple local demo identity/session mechanism only; do not build LinkedIn OAuth or external authentication. Keep the mechanism clearly isolated for future replacement.

D. RESUME UPLOAD BOUNDARY
Implement POST /api/candidates/{id}/resume:
- Accept PDF/DOCX only (per the agreed requirements).
- Enforce a conservative upload-size limit configurable by environment.
- Generate server-side filenames; prevent path traversal and arbitrary filesystem paths.
- Store files under UPLOAD_DIR, not in the Git repository.
- Extract text using Person 2's documented public integration function when available; do not implement a second resume parser.
- Expected Person 2 function contract: parse_resume_text(resume_text: str) -> dict. If their package is not present yet, create a small adapter/interface and return an explicit integration-not-ready error rather than fabricating parsed output.
- Persist original file metadata, extracted text and parsed JSON where available.
- Never expose the local filesystem path in the API response.

E. DATA PROVENANCE
For each normalized profile/company, store source, source identifier, source URL where available, retrieval time and field-level unknowns where practical. Do not claim career information has been independently verified. Do not fabricate salary, availability, resume, preferences, consent or registration for a sourced non-member.

TESTS
- Company Identify → Company Enrich sequence.
- Ambiguous company identity response.
- Person Enrich normalization with sanitized fixtures.
- Missing/null profile fields.
- Duplicate person by Crustdata ID and profile URL.
- Sourced Person registration attaches to existing Person.
- Invalid URL and unsupported resume type.
- Oversized upload and path traversal attempts.
- Resume parser integration-not-ready behavior.

ACCEPTANCE CHECKS
- All company and candidate onboarding routes listed above work with fixtures.
- Company canonical ID is persisted.
- PersonRecord is normalized and matches the shared schema.
- Registration does not duplicate an existing sourced Person.
- Sourced profiles are clearly not registered.
- Resume upload is safe and never commits personal files.

Commit with message: `backend: add company and candidate onboarding services` if Git is available and the branch is correct.
```

**Expected output:** Working company resolution, person enrichment, canonical identity linking, candidate registration and a safe resume-upload integration boundary.

---

# Prompt 5 of 6 — Job routes and end-to-end candidate discovery orchestration

```text
Continue Person 1's SwipeHire backend. Re-read the project references and inspect the exact public schemas from Prompt 2. Preserve the contracts. Person 2 owns the JD parser and matching algorithm; you own the backend route and orchestration that call those modules.

TASK
Implement job creation/listing and the complete backend candidate-discovery pipeline from a confirmed job to a persisted candidate deck.

OWNERSHIP
- You own backend/app/services/discovery_service.py, backend/app/api/jobs.py and the required job orchestration glue.
- Person 2 owns backend/app/ai/ and backend/app/matching/ implementations.
- Do not copy/reimplement JD parsing, hard filters, scoring, direct/adjacent classification or deck selection in your files.
- Do not edit frontend/ or shared root docs.

A. JOB CREATION
Implement:
- POST /api/jobs
- GET /api/jobs
- PATCH /api/jobs/{id} for recruiter edits/confirmation if needed by the review-before-discovery workflow; document this route for Person 3.

POST /api/jobs supports:
1. Structured mode: validate and save JobRequirements.
2. JD mode: save the raw JD, call Person 2's parse_job_description(raw_jd), validate the returned JobRequirements and set the job to needs_review/needs_confirmation until recruiter confirmation.

Expected Person 2 function:
parse_job_description(raw_jd: str) -> JobRequirements

If Person 2's package is not merged yet, implement a narrow import adapter with a clear dependency-not-ready error. Do not invent parser output and do not add a second implementation.

Requirements:
- Job must belong to a resolved Company.
- Persist raw JD and normalized requirements.
- Require recruiter confirmation before candidate discovery if the JD was parsed automatically.
- Do not silently classify ambiguous JD statements as hard requirements. Preserve them in unknown_or_needs_confirmation.

B. CANDIDATE DISCOVERY
Implement POST /api/jobs/{id}/discover and GET /api/jobs/{id}/deck.
The service must:
1. Load the confirmed JobRequirements and create a MatchRun with processing status.
2. Load registered candidate Person records and associated CandidateProfiles from the local database.
3. Call Crustdata Person Search using a query built from the job title, role context and relevant skills. Build filters only using fields/operators proven by the supplied Crustdata docs. Do not use preferred skills as exclusionary filters. Do not over-constrain the Crustdata search so that only literal JD matches can be found.
4. Use a configurable bounded search limit (initial default around 50); preserve/paginate cursors only as needed and prevent unbounded credit usage.
5. Normalize search results and enrich a bounded top subset with Person Enrich when profile URLs/identifiers are available and enrichment is needed. Avoid enriching duplicates or already sufficiently enriched/cached profiles.
6. Convert registered and sourced records into the shared PersonRecord schema.
7. Deduplicate by canonical Crustdata person ID and normalized professional-network URL.
8. Preserve origin and membership_status; a sourced person without a platform account must remain not_registered.
9. Call Person 2's public matching interface. Expected contract:
   build_candidate_deck(requirements: JobRequirements, candidates: list[PersonRecord], deck_size: int = 20) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]
   The tuple is (displayed_evaluations, excluded_evaluations).
10. Support sync or async implementation consistently. If Person 2 chooses async functions, adapt the call with an explicit, tested await path. Do not mix sync/async ambiguously.
11. The matching module owns the 30/25/20/15/10 weighted fit score, strict mandatory filters, unknown-required exclusion, direct/adjacent classification and 20% adjacent cap. Your orchestration must not override those decisions.
12. Persist MatchRun status, total counts, displayed evaluations, exclusions, source metadata and diagnostics. Persist CandidateMatch rows in a way that preserves rank and all score/exclusion fields.
13. Return CandidateDeckResponse. On failure, mark MatchRun failed with a sanitized diagnostic and leave prior completed runs intact.

C. SEARCH FALLBACKS AND ROBUSTNESS
- If Crustdata Person Search is denied/unavailable, show a clear API integration error. Do not silently substitute fabricated people.
- If enrichment is unavailable for an individual record, preserve search fields and mark missing details unknown; do not discard all results automatically.
- Handle zero results, fewer than 20 results, repeated cursors, malformed records and duplicate records.
- Use cached responses where valid.

D. FRONTEND CONTRACT HANDOFF
Document exact JSON examples for:
- POST /api/jobs (structured)
- POST /api/jobs (JD)
- PATCH /api/jobs/{id} confirmation/update
- POST /api/jobs/{id}/discover
- GET /api/jobs/{id}/deck
Include status values, error shape, card structure, membership status and fit_type. Person 3 must not need to read raw Crustdata responses.

TESTS
- Structured job creation.
- JD parser adapter contract (mock Person 2 function only at the boundary).
- Discovery merges registered and external candidates.
- Deduplication.
- Cursor/bounded search behavior.
- Matching bridge receives canonical PersonRecords.
- CandidateEvaluation persistence and deck response.
- Excluded candidates have reasons and are not placed in deck.
- MatchRun transitions processing → completed/failed.
- Search/enrich partial failure behavior.

ACCEPTANCE CHECKS
- A confirmed job can run discovery end-to-end using Crustdata fixtures or a live key.
- Person 2's matching implementation is called; there is no duplicate scoring logic in the discovery service.
- A deck of up to 20 cards is persisted and retrievable.
- Adjacent candidates and exclusions follow Person 2's returned evaluations without alteration.
- All API response objects match the shared Pydantic contracts.

Commit with message: `backend: add job and candidate discovery orchestration` if Git is available and the branch is correct.
```

**Expected output:** Job creation plus the core job-to-candidate-deck backend pipeline. This is the most important integration milestone.

---

# Prompt 6 of 6 — Recruiter actions, candidate interest, mutual matching and integration hardening

```text
Complete Person 1's SwipeHire backend work. Read the five reference files again, inspect all code from Prompts 1–5 and preserve the shared contracts. Do not take ownership of Person 2's ai/matching algorithms or Person 3's frontend.

TASK
Finish recruiter actions and registered-candidate mutual matching, add/complete tests, harden the backend and prepare a clear integration handoff for the team.

A. RECRUITER ACTIONS
Implement POST /api/jobs/{id}/actions and GET /api/jobs/{id}/shortlist.
Supported actions:
- shortlist
- pass
- save

Rules:
1. Validate that the Person is included in the job's candidate pool or has a valid candidate record for the job.
2. Store recruiter action with job, person, recruiter/company identity and timestamp.
3. For a registered candidate, recruiter shortlist/right-swipe creates a pending InterestRequest.
4. For a Crustdata-sourced non-member, shortlist creates only an internal recruiter action. Do not create an InterestRequest.
5. Pass and save/maybe are persisted as actions; prevent duplicate/contradictory state from becoming inconsistent. Define whether a new action updates the prior action or creates an action history, and document the choice.
6. Do not send email, LinkedIn messages, webhooks to real people or external notifications.

B. CANDIDATE INTERESTS AND MUTUAL MATCH
Implement:
- GET /api/candidates/{id}/interests
- POST /api/interests/{id}/respond
- GET /api/matches

Rules:
1. Only a registered candidate user linked to the Person can see/respond to interest requests.
2. Candidate response is accept or reject.
3. On accept, create exactly one Match linked to the InterestRequest. Make the operation idempotent so repeated accept requests do not create duplicate matches.
4. On reject, mark the InterestRequest rejected and do not create a Match.
5. Sourced non-members cannot receive or respond to interest requests and cannot form a Match.
6. Use the local demo identity mechanism from the backend foundation; do not add OAuth or external identity providers.
7. Return clear errors for unauthorized actor, nonexistent request, wrong state and non-member.

C. SECURITY AND PRIVACY
- Confirm Crustdata and Anthropic API keys never leave the backend.
- Do not log full resumes, raw profile payloads, emails or secrets.
- Ensure salary visibility is honored; do not return salary to companies if candidate visibility is false.
- Validate uploaded file types, size, generated storage path and file ownership.
- Avoid exposing raw filesystem paths, local exception traces or secret-bearing upstream response bodies.
- Keep CORS restricted to the configured frontend origin(s) for the prototype.
- Keep all interactions local/in-app for the hackathon; never contact external people.

D. TESTS AND END-TO-END VALIDATION
Add or complete tests for:
- shortlist action on registered candidate → pending interest;
- shortlist action on sourced non-member → internal action only;
- pass/save actions;
- registered candidate accepts → one Match created;
- registered candidate rejects → no Match;
- non-member cannot receive/respond/mutual-match;
- repeated accept is idempotent;
- salary hidden when visibility is false;
- malformed requests and missing records return safe errors;
- no external outreach code is invoked.

Run all backend tests. Also run the complete local path using fixtures:
company resolve → job create/confirm → candidate discovery → deck retrieval → recruiter shortlist → candidate accepts → mutual match.
If a live Crustdata key is available, run one small smoke test as well, but do not make normal tests depend on it.

E. FINAL CONTRACT AND MERGE HANDOFF
Create a backend-owned `backend/INTEGRATION.md` containing:
1. Backend setup/run commands.
2. Required environment variables.
3. All internal routes with methods and request/response examples.
4. Canonical Pydantic schema locations and exact public contracts.
5. Person 2 integration function names and sync/async behavior.
6. Any Crustdata endpoints/fields disabled for the supplied key.
7. Known limitations and intentionally deferred endpoints/features.
8. How to run tests and opt-in live smoke tests.
9. Any seed/demo identity details.

Do not edit the root shared README/context/to-do files; send the integration handoff to the team so the repository integrator can update shared docs if needed.

F. FINAL ACCEPTANCE CHECKLIST
- Backend starts with a single documented command.
- Health endpoint works.
- Company Identify/Enrich works through the internal route.
- Candidate Person Enrich works through the internal route.
- Company and Person records persist with canonical IDs/provenance.
- Job structured/JD creation works through the shared contract.
- Discovery uses Crustdata and Person 2's matching module.
- Deck response contains score, component reasons, fit_type and membership status.
- Recruiter actions work.
- Only registered candidate acceptance creates a Match.
- Tests pass and no secrets/personal files are committed.
- No frontend, Person 2 ai/matching or shared root docs were edited.

Run `git status`, inspect the diff, remove accidental local databases/uploads/credentials from the staged files, and make a final small commit with message: `backend: complete recruiter actions and integration hardening` if Git is available and the branch is correct.

Finally provide an integration summary for the team:
- files created/changed;
- commands to run;
- API routes available;
- shared schema locations;
- Person 2 functions required;
- Person 3 frontend assumptions;
- test outcomes;
- live Crustdata smoke-test outcomes;
- remaining blockers.
```

**Expected output:** Complete backend workstream, tested interaction state transitions, clean API contracts and a handoff document that Persons 2 and 3 can integrate against.

---

# Cross-prompt rules for Person 1

These rules apply to every prompt:

1. **Read before editing.** Re-read the five shared/reference files at the start of every prompt and inspect the current code. Do not assume Antigravity remembers earlier work accurately.
2. **Own only your area.** Never modify `frontend/`, `backend/app/ai/`, `backend/app/matching/` or the shared root docs.
3. **Contracts first.** `backend/app/database/schemas.py` is the canonical shared Pydantic contract. Tell Person 2 and Person 3 when it changes; do not make silent breaking changes.
4. **Use actual Crustdata docs.** The complete combined documentation file is the authority for payloads, fields and endpoint behavior. Do not invent schemas or rely on guessed response shapes.
5. **Real integration, safe fallback.** Use Crustdata for real data. Fixtures are for deterministic tests, not a substitute for the live integration in the demo.
6. **No external outreach.** All demo notifications and candidate responses remain local and in-app.
7. **No fabricated candidate information.** Unknown stays unknown. Sourced non-members have no invented resume, preferences, consent, salary or availability.
8. **No independent scoring implementation.** Person 2 owns eligibility rules, weighted scoring, adjacent classification and deck allocation. Person 1 orchestrates and persists its output.
9. **Bound API spend.** Cache enrichment, use limited search results, paginate intentionally and avoid redundant calls.
10. **Test after each increment.** Do not carry a broken foundation into the next prompt.

## Suggested commit sequence

```text
backend: scaffold FastAPI foundation
backend: add shared schemas and database models
backend: implement Crustdata client and diagnostics
backend: add company and candidate onboarding services
backend: add job and candidate discovery orchestration
backend: complete recruiter actions and integration hardening
```

## Final outcome expected from Person 1

Person 1 is finished when the backend exposes stable APIs that allow this full path:

```text
Company resolves through Crustdata
        ↓
Recruiter creates/confirms a job
        ↓
Backend searches registered + Crustdata people
        ↓
Canonical people are normalized and deduplicated
        ↓
Person 2's AI/matching modules evaluate the pool
        ↓
Backend persists and serves the candidate deck
        ↓
Recruiter shortlists/passes/saves
        ↓
Registered candidate accepts/rejects locally
        ↓
Mutual Match is created only after acceptance
```
