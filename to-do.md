# SwipeHire — Implementation To-do

> Work from top to bottom. P0 items establish the end-to-end path. P1 items complete the agreed MVP. P2 items are explicitly optional and must not delay a working demo.

## Status legend

- [ ] Not started
- [~] In progress
- [x] Complete

---

## P0 — Foundation and end-to-end path

### 1. Repository and environment

- [ ] Create the repository using the agreed `frontend/` and `backend/` structure.
- [ ] Add `.gitignore` for `.env`, databases, uploaded resumes, build output, caches, and local model files.
- [ ] Add `.env.example` with `CRUSTDATA_API_KEY`, `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, `DATABASE_URL`, and `UPLOAD_DIR`.
- [ ] Add backend FastAPI skeleton and frontend Next.js/TypeScript skeleton.
- [ ] Add a health-check endpoint and confirm frontend-to-backend connectivity.
- [ ] Create a shared API contract for `Person`, `JobRequirements`, and `CandidateMatch`.

### 2. Crustdata smoke tests and permissions

- [ ] Confirm the API key works against `https://api.crustdata.com`.
- [ ] Send required headers: bearer authorization and `x-api-version: 2025-11-01`.
- [ ] Check account permissions, enabled endpoints, enabled response fields, effective rate limits, and remaining credits using the documented account endpoints.
- [ ] Test `POST /person/enrich` with a known permitted profile URL.
- [ ] Test `POST /person/search` with a small query and limited fields.
- [ ] Test `POST /company/identify` with a known company name/domain.
- [ ] Test `POST /company/enrich` using the resolved canonical company ID.
- [ ] Save small sanitized fixtures for automated tests; do not commit API keys or unnecessary personal data.
- [ ] Record actual response shapes and any key-specific field/endpoint restrictions.

### 3. Backend data model

- [ ] Implement SQLAlchemy models: `User`, `Person`, `CandidateProfile`, `Resume`, `Company`, `CompanyMember`, `JobRole`, `MatchRun`, `CandidateMatch`, `RecruiterAction`, `InterestRequest`, `Match`, and optional `EvidenceItem`.
- [ ] Add unique constraints for non-null `crustdata_person_id` and normalized professional-network URL.
- [ ] Implement the Person/User distinction so Crustdata-sourced people can exist without a SwipeHire account.
- [ ] Implement database initialization/migrations appropriate for the prototype.
- [ ] Add basic seed/demo data for one company, one job, registered candidates, and sourced candidates.

### 4. Crustdata integration adapter

- [ ] Implement a backend-only Crustdata client with authentication and required version header.
- [ ] Implement typed wrappers for Person Search and Person Enrich.
- [ ] Implement typed wrappers for Company Identify and Company Enrich.
- [ ] Normalize raw Crustdata responses into internal `Person` and `Company` structures.
- [ ] Handle missing/nullable fields and unexpected response structures.
- [ ] Handle cursor pagination where required.
- [ ] Add caching for repeated enrichment and search calls where appropriate.
- [ ] Add safe timeout, bounded retry/backoff for transient failures and 429 responses.
- [ ] Log status, latency, request ID, and credit metadata where available; never log secrets.

### 5. Company onboarding

- [ ] Build company name/domain input.
- [ ] Call Company Identify and display possible matches where ambiguous.
- [ ] Select and persist canonical Crustdata company ID.
- [ ] Call Company Enrich and show available company details.
- [ ] Link recruiter account to the resolved company.

### 6. Job creation and JD parsing

- [ ] Define and validate Pydantic `JobRequirements` schema.
- [ ] Build structured job creation form.
- [ ] Build JD paste/upload field.
- [ ] Implement Claude JD parser that emits structured JSON.
- [ ] Distinguish mandatory skills/qualifications from preferred criteria and explicit dealbreakers.
- [ ] Represent ambiguous requirements as `unknown_or_needs_confirmation`; do not silently hard-filter them.
- [ ] Add recruiter review/confirmation before discovery.
- [ ] Persist raw JD and normalized requirements.

### 7. Candidate discovery and normalization

- [ ] Query registered SwipeHire candidates from the local database.
- [ ] Build Person Search query/filters from confirmed job requirements.
- [ ] Retrieve a bounded first page of Crustdata candidates; paginate only as needed.
- [ ] Enrich the most relevant external candidates using Person Enrich.
- [ ] Normalize all sources into the same canonical Person representation.
- [ ] Merge/deduplicate by Crustdata person ID and normalized profile URL.
- [ ] Preserve candidate origin and membership status.
- [ ] Persist discovery run and candidate pool.

### 8. Matching engine

- [ ] Implement hard-filter evaluator for explicitly mandatory criteria.
- [ ] Ensure unknown mandatory fields fail with a specific exclusion reason.
- [ ] Ensure missing optional fields remain unknown and do not exclude candidates.
- [ ] Implement weighted scoring: skills 30%, experience 25%, role/domain 20%, trajectory 15%, contextual fit 10%.
- [ ] Store component scores, total score, evidence coverage, and scoring version.
- [ ] Implement direct-fit and adjacent-fit classification.
- [ ] Ensure adjacent candidates pass all hard filters and may miss preferred criteria only.
- [ ] Implement dynamic deck generation: up to 20 cards, adjacent candidates capped at 20% (maximum 4 for a 20-card deck), no forced filler.
- [ ] Generate an explanation grounded in stored score components and candidate evidence.
- [ ] Persist ranked deck and exclusions.

### 9. Recruiter deck — first complete demo path

- [ ] Build job list and job detail page.
- [ ] Build candidate card front: name, headline, current role/company, experience, score, fit label, skills, reason, and membership status.
- [ ] Build expanded candidate detail view with career timeline, resume highlights where available, education, preferences, and unknown fields.
- [ ] Clearly label `Registered` and `Not on platform` candidates.
- [ ] Add swipe-right / shortlist, swipe-left / pass, and save/maybe actions.
- [ ] Build shortlist and saved-candidate views.
- [ ] Complete the end-to-end path: create job → discover → match → deck → recruiter action.

---

## P1 — Complete the agreed two-sided MVP

### 10. Candidate onboarding PWA

- [ ] Build mobile-first candidate onboarding pages.
- [ ] Accept LinkedIn/profile URL and call Person Enrich through the backend.
- [ ] Display enriched fields for candidate confirmation/correction.
- [ ] Add PDF upload and DOCX upload.
- [ ] Extract PDF text with PyMuPDF and DOCX text with python-docx.
- [ ] Call Claude to structure resume skills, projects, achievements, and metrics.
- [ ] Validate structured resume output and preserve original extracted text.
- [ ] Collect target role, locations, remote preference, availability/notice period, and optional salary range.
- [ ] Persist registered User, link to canonical Person, and create CandidateProfile.
- [ ] Handle sourced Person registration by attaching the account to the existing Person record rather than duplicating it.

### 11. Mutual-match flow

- [ ] Implement recruiter interest request for registered candidates.
- [ ] Implement candidate incoming-interest screen.
- [ ] Implement accept/reject action.
- [ ] Create `Match` only on candidate acceptance.
- [ ] Ensure sourced non-members can only be saved/shortlisted and cannot receive interest notifications or mutual matches.
- [ ] Add local in-app notification state only; no external emails or LinkedIn messages.

### 12. Product polish and robustness

- [ ] Add loading, empty, error, and partial-result states.
- [ ] Handle invalid/malformed profile URLs.
- [ ] Handle company-identification ambiguity.
- [ ] Handle Crustdata 401/403/429/5xx responses cleanly.
- [ ] Handle LLM malformed JSON and resume extraction failures.
- [ ] Handle no candidates found and fewer than 20 candidates.
- [ ] Handle profiles missing experience, skills, or location.
- [ ] Make salary and other sensitive candidate preferences hidden from companies unless explicitly shared.
- [ ] Review file upload validation and prevent unsafe file types.

### 13. Tests

- [ ] Unit-test JD requirement classification.
- [ ] Unit-test hard filters (pass, fail, unknown-required, unknown-optional).
- [ ] Unit-test weighted scoring and score bounds.
- [ ] Unit-test adjacent candidate eligibility.
- [ ] Unit-test dynamic deck cap and no-forced-filler behavior.
- [ ] Unit-test person identity deduplication and registration linking.
- [ ] Unit-test non-member action restrictions.
- [ ] Unit-test mutual-match state transitions.
- [ ] Add integration test using sanitized Crustdata response fixtures.
- [ ] Run a full local end-to-end test.

---

## P2 — Only if time remains

- [ ] Add local Sentence Transformers embeddings for semantic skill similarity.
- [ ] Add optional GitHub/developer-platform context if the account and permitted APIs support it.
- [ ] Add Web Search/Fetch for supplementary public evidence.
- [ ] Add Company Search for dream-company suggestions.
- [ ] Add Job Search for additional market/hiring context.
- [ ] Add Watcher-based ongoing profile/job alerts.
- [ ] Add multi-role candidate profiles and multiple resumes.
- [ ] Add richer analytics for recruiter teams.

---

## Demo and submission checklist

- [ ] Choose a demo company and a previously unseen ML Engineer or software engineering JD.
- [ ] Confirm the JD parses into the intended hard and preferred criteria.
- [ ] Confirm the live Crustdata call returns real candidate records.
- [ ] Include both registered and non-member sourced records in the demo data/pool.
- [ ] Show at least one valid adjacent-fit candidate who passes all hard filters but misses a preferred criterion.
- [ ] Show a candidate excluded for a mandatory requirement with the exact reason.
- [ ] Show a candidate card with profile source and evidence-based explanation.
- [ ] Shortlist a sourced non-member and show that mutual matching is unavailable.
- [ ] Shortlist a registered candidate, switch to candidate PWA, accept interest, and show mutual match.
- [ ] Ensure no external real-person contact or outreach is triggered.
- [ ] Record a clear two-minute screen demo.
- [ ] Check repository README, `.env.example`, setup instructions, and absence of secrets.

---

## Suggested ownership (team of four)

| Workstream | Primary responsibility | Key deliverable |
|---|---|---|
| Backend + Crustdata | API client, company/person services, DB, normalization | Working canonical data pipeline |
| AI + matching | Claude JD/resume parsers, filters, score, adjacent allocation | Requirements → ranked deck data |
| Recruiter web | Company setup, job creation, candidate deck, shortlist | Usable recruiter workflow |
| Candidate PWA + integration | Onboarding, resume upload, interests, end-to-end integration/demo | Working registered-candidate loop |

All workstreams must agree on shared Pydantic/TypeScript schemas before parallel implementation. One person should own integration and merge decisions.
