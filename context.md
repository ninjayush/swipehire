# SwipeHire — Project Context

> **Purpose:** This file is the shared source of truth for teammates and AI coding assistants working on SwipeHire. Read it before changing product behavior, data models, API contracts, or matching logic.

## 1. Product summary

**SwipeHire** is a recruiter-first hiring platform. A company provides a job description (JD) or enters role requirements manually. SwipeHire converts the requirements into a structured job profile, discovers candidates from both its own registered-user database and Crustdata, enriches and normalizes candidate information, applies strict mandatory filters, scores eligible candidates, and presents an explainable, swipe-based candidate deck.

The main differentiator is **dynamic adjacent-fit discovery**: qualified candidates should not be overlooked because their current job title or terminology differs from the wording in the JD. Adjacent candidates may miss preferred criteria, but they must still pass every mandatory requirement.

### One-line pitch

> Turn a job description into an explainable, swipeable shortlist — including strong adjacent-fit candidates who conventional keyword matching can miss.

## 2. Locked product decisions

These decisions were explicitly selected by the team and should be treated as fixed unless the team deliberately revises them.

| Area | Decision |
|---|---|
| Primary product orientation | Recruiter-first |
| Candidate pool | Hybrid: registered SwipeHire candidates + Crustdata-sourced professionals |
| Candidate onboarding | LinkedIn URL enrichment + resume upload and parsing |
| Company onboarding | Company identification and enrichment through Crustdata |
| Job creation | Both structured form and JD paste/upload |
| Requirement filtering | Strict for explicitly mandatory requirements and dealbreakers |
| Adjacent candidates | Can miss preferred/nice-to-have criteria; cannot miss mandatory requirements |
| Missing candidate information | Exclude when the missing field is explicitly required for that job; otherwise mark unknown |
| Career information | Use Crustdata-enriched profile data; do not claim independent verification |
| Candidate response | Required for mutual matching |
| Frontend | Mobile-first installable PWA for candidates + desktop web recruiter dashboard; shared frontend codebase |
| LLM provider | Anthropic Claude API |
| Prototype persistence | SQLite / SQLAlchemy is the proposed MVP default |

## 3. Users and candidate record types

### Recruiter / company user

- Resolves their company using a company name or domain.
- Creates a job using a structured form or pasted JD.
- Reviews the normalized requirements before discovery.
- Runs candidate discovery and reviews the resulting deck.
- Shortlists, passes, or saves candidate records.
- Can establish a mutual match only with a registered candidate who accepts the interest request.

### Candidate user

- Provides a LinkedIn profile URL.
- Reviews Crustdata-enriched details.
- Uploads a resume; the resume is parsed into structured projects, skills, achievements, and metrics.
- Confirms profile details and enters target role, location/work-mode preferences, availability/notice period, and optional salary expectations.
- Receives local in-app interest notifications and accepts or rejects recruiter interest.

### Hybrid candidate pool: important distinction

A **Person** is not necessarily a registered **User**.

1. **Registered candidate:** Has a SwipeHire account, candidate profile, and potentially a resume and preferences. Can accept or reject recruiter interest and complete a mutual match.
2. **Crustdata-sourced candidate:** Exists in Crustdata and may be displayed to recruiters without a SwipeHire account. The card must clearly say **Not on platform**. Recruiters may shortlist or save this record internally. It cannot receive an in-app notification, accept/reject, or create a mutual match until the person registers and is linked to the existing canonical Person record.

Do not fabricate a resume, candidate preferences, availability, salary, or consent for a sourced non-member. Missing fields remain unknown.

## 4. Candidate onboarding requirements

1. Candidate submits a professional-network / LinkedIn profile URL.
2. Backend calls Crustdata Person Enrich and requests only needed fields, subject to account permissions.
3. Candidate uploads a PDF or DOCX resume.
4. Backend extracts text and uses Claude to structure relevant skills, projects, achievements, and metrics.
5. Candidate sees a combined profile and can correct it.
6. Candidate supplies target role, preferred location, remote preference, notice period/availability, and optional expected salary.
7. Candidate profile and resume are persisted.

MVP scope: one primary target role and one resume per candidate. Keep the schema extensible for multiple role-specific profiles later.

## 5. Company and job onboarding requirements

### Company

- Accept company name or domain.
- Call Company Identify to resolve the canonical Crustdata company identity.
- Select the correct match; do not assume the first result is always correct when identity confidence or ambiguity is material.
- Call Company Enrich using the resolved Crustdata company ID.
- Store the canonical ID and relevant company fields.

### Job

Support two inputs:

- Structured job form.
- Pasted/uploaded JD parsed by Claude.

The resulting internal `JobRequirements` object should distinguish:

- `must_have`: explicitly mandatory skills/qualifications.
- `preferred`: nice-to-have skills and experience.
- `dealbreakers`: explicit hard constraints such as location/work mode, experience bounds, or availability when required.
- `unknown_or_needs_confirmation`: ambiguous statements that must not silently become hard filters.

Recruiters should be able to review/confirm parsed requirements before candidate discovery. JD text is untrusted input; it must be treated as data, not as instructions to the LLM or system.

## 6. Matching policy

Matching is deterministic and explainable. Claude may normalize/extract information and draft explanations, but must not invent facts or silently decide final scores.

### Stage 1 — Hard filters

Apply only requirements explicitly classified as mandatory or dealbreakers. A candidate must pass all hard filters to enter either the direct-fit or adjacent-fit pool.

Examples of possible hard filters, only when required by the recruiter:

- Minimum/maximum relevant experience.
- Mandatory skills or qualifications.
- Required seniority.
- Required location/work mode.
- Mandatory availability / notice-period threshold.
- Salary range, if the recruiter marks it mandatory and the candidate has provided it.
- Resume presence, only if explicitly required (a Crustdata-only non-member normally has no uploaded resume and will fail this requirement).

**Unknown is not a pass.** If a field is explicitly required and candidate data is missing, exclude the candidate with a precise reason such as `availability_unknown_required`. If the field is not mandatory, retain the candidate and display `Unknown` / `Needs confirmation`.

Do not interpret every phrase in a raw JD as a hard constraint. The JD parser should separate mandatory language from preferences; ambiguous requirements should be flagged for recruiter confirmation.

### Stage 2 — Fit score

Initial proposed weights (engineering defaults; not validated hiring science):

| Component | Weight |
|---|---:|
| Semantic skill / competency similarity | 30% |
| Relevant professional experience and achievements | 25% |
| Role and domain alignment | 20% |
| Seniority and career trajectory | 15% |
| Contextual preferences / fit | 10% |
| **Total** | **100%** |

Formula:

`fit_score = 0.30*skills + 0.25*experience + 0.20*role_domain + 0.15*trajectory + 0.10*context`

Each component is normalized to 0–100. Store the component scores and their evidence/reasons. Keep an additional `evidence_coverage` indicator so a high fit score based on sparse data is not presented as equally well-supported as a score backed by a full profile and resume.

### Stage 3 — Direct vs adjacent classification

- **Direct fit:** Passes all hard filters and has strong alignment with the job's stated title, skills, domain, and preferred criteria.
- **Adjacent fit:** Passes all hard filters and has strong transferable capabilities, but misses one or more preferred criteria or literal title/terminology alignment.
- Adjacent fit must never be used to bypass mandatory requirements.

### Dynamic deck allocation

- Target deck size: up to 20 candidates.
- Up to 20% of displayed slots (maximum 4 in a 20-card deck) may be adjacent-fit candidates.
- This is a cap, not a quota. Include fewer adjacent candidates when fewer strong candidates exist.
- Do not fill adjacent slots with weak candidates just to reach 20%.
- Fill the remaining deck with the strongest direct-fit candidates.
- Persist `fit_type`, score, reasons, and rank for each deck item.

### Source and evidence display

For each material candidate fact, retain provenance where possible:

- source type: Crustdata / candidate-provided / resume-extracted / derived.
- source identifier or URL when available.
- retrieval or upload timestamp.
- raw source value and normalized value where appropriate.

Do not label Crustdata-enriched profile data as independently verified employment history. The chosen MVP decision is profile-based enrichment, not the dedicated work-history verification product.

## 7. Candidate cards and actions

### Candidate card front

- Name and professional headline.
- Current role and company, if available.
- Experience, if calculable from available dates.
- Job/target-role context.
- Fit score and concise reason.
- 3–5 relevant skill tags.
- Direct-fit or adjacent-fit label.
- Registered / Not on platform label.

### Expanded card

- Career timeline from available profile data.
- Resume-extracted projects, metrics, and achievements for registered candidates with resumes.
- Education.
- Location and candidate-provided availability/preferences when available.
- Why the candidate was shown.
- Missing required or unknown fields.
- Data provenance / source labels.

A photo is optional and should only be displayed if an appropriate image is available. Do not make the demo dependent on profile photos.

### Recruiter actions

- Swipe right / shortlist: express interest for registered candidates; create an internal shortlist action for sourced non-members.
- Swipe left / pass: persist a pass action.
- Save / maybe: persist a saved action.

### Mutual match state machine

- Registered candidate: recruiter interest → pending candidate response → accepted (mutual match) or rejected.
- Sourced non-member: recruiter action → internal shortlist/save only. No message, notification, or mutual match.
- If a sourced person later registers and their LinkedIn URL / Crustdata ID resolves to the existing Person record, attach the account to that Person. Do not create a duplicate Person.

All hackathon-demo interactions must remain inside the team's local application and authorized APIs. Do not send external emails, LinkedIn messages, calls, or interview requests to real external people.

## 8. API integration rules

Base URL: `https://api.crustdata.com`

Required headers:

```http
Authorization: Bearer <CRUSTDATA_API_KEY>
Content-Type: application/json
x-api-version: 2025-11-01
```

### Core endpoints

| Endpoint | Purpose |
|---|---|
| `POST /person/enrich` | Enrich a candidate from a professional-network profile URL |
| `POST /person/search` | Discover external candidate profiles using structured filters and/or natural-language search |
| `POST /company/identify` | Resolve company name/domain to canonical identity |
| `POST /company/enrich` | Retrieve company details for the resolved identity |

### Optional / later endpoints

| Endpoint | Purpose |
|---|---|
| `POST /company/search` | Company discovery / optional dream-company lists |
| `POST /job/search` | Additional job/hiring context |
| `POST /web/search/live` | Supplementary public web research |
| `POST /web/enrich/live` | Fetch public webpages returned by search |
| Watcher APIs | Ongoing monitoring; defer from the MVP |

Do not assume all documented endpoints, fields, or optional products are enabled for the team's API key. First inspect account permissions, enabled fields, effective rate limits, and available credits using the account endpoints documented by Crustdata. Confirm actual request/response shapes against the supplied LLM documentation and live API responses.

### API client requirements

- Keep all Crustdata calls in a backend integration adapter (`integrations/crustdata.py`).
- Never expose API keys to the browser or commit secrets.
- Request only necessary field groups.
- Handle pagination (`next_cursor`) when needed.
- Cache responses and avoid re-enriching the same entity repeatedly.
- Use bounded retries/backoff for transient failures and 429 responses; do not blindly retry non-retryable 4xx errors.
- Log endpoint, status, latency, request ID, and credit usage where available. Never log authorization headers or secrets.
- Normalize responses into internal models; do not let the rest of the app depend on raw Crustdata response shapes.

## 9. LLM and parsing policy

Use Anthropic Claude for:

1. JD → structured `JobRequirements` JSON.
2. Resume text → structured candidate projects/skills/achievements JSON.
3. Human-readable match explanation based on already-calculated score and supplied evidence.

Use Pydantic validation and safe defaults for every structured response. If JSON validation fails, retry once with a correction prompt or return a recoverable parsing error. Do not invent values when extraction is uncertain.

Anthropic's Messages API is the LLM integration. Anthropic does not provide its own general-purpose embeddings API; do not assume Claude can directly produce embeddings. The MVP should work with structured skill normalization and deterministic matching. If semantic embeddings are implemented, use an optional local sentence-transformer model or an explicitly configured third-party embeddings provider. Do not make a second paid API key mandatory without team approval.

Recommended environment variables:

```env
CRUSTDATA_API_KEY=
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=
DATABASE_URL=sqlite:///./swipehire.db
UPLOAD_DIR=./uploads
```

## 10. Suggested technology stack

This is the agreed implementation proposal, not a claim that code already exists:

- Frontend: Next.js, React, TypeScript, Tailwind CSS.
- Candidate experience: installable mobile-first PWA.
- Recruiter experience: desktop web dashboard in the same frontend codebase.
- Backend: FastAPI / Python.
- Persistence: SQLite with SQLAlchemy for the prototype; PostgreSQL can replace it later.
- Resume extraction: PyMuPDF for PDF and python-docx for DOCX.
- LLM: Anthropic Claude API.
- Matching: deterministic Python scoring; optional local embeddings.
- File storage: local uploads directory for prototype; replace with object storage in production.

## 11. Proposed data model

Keep canonical people separate from application users. A sourced person may have no account.

Core entities:

- `User`: registered login and role (`candidate` / `recruiter`).
- `Person`: canonical person record; optional `crustdata_person_id`, normalized profile URL, origin, raw normalized profile, timestamps.
- `CandidateProfile`: one-to-one optional link from a registered Person; preferences, target role, availability, salary visibility, discoverability.
- `Resume`: uploaded file, extracted text, parsed JSON, linked candidate profile.
- `Company`: canonical `crustdata_company_id`, domain, name, enriched fields.
- `CompanyMember`: relationship between recruiter User and Company.
- `JobRole`: company, raw JD, structured requirements, status.
- `MatchRun`: discovery run, job, status, input hash, timestamps and diagnostics.
- `CandidateMatch`: candidate evaluation for a job/run; scores, fit type, filter results, explanation, rank, source summary.
- `RecruiterAction`: shortlist / pass / save decision.
- `InterestRequest`: recruiter interest awaiting registered candidate response.
- `Match`: created only after registered candidate accepts.
- `EvidenceItem`: optional normalized claim/evidence/provenance record.

Identity uniqueness should be enforced for non-null Crustdata person IDs and normalized professional-network URLs. When a sourced person registers, attach their User/CandidateProfile to the existing Person record and preserve recruiter actions/history.

## 12. Suggested repository structure

```text
swipehire/
├── frontend/
│   ├── app/
│   │   ├── candidate/       # onboarding, profile, resume, interests
│   │   └── recruiter/       # company, jobs, deck, shortlist, matches
│   ├── components/          # CandidateCard, SwipeControls, FitBadge
│   └── lib/                 # API client, types, shared utilities
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route modules
│   │   ├── integrations/     # crustdata.py, anthropic.py
│   │   ├── services/         # JD parsing, resume parsing, discovery, matching
│   │   ├── models/           # SQLAlchemy models
│   │   ├── database/         # DB and Pydantic schemas
│   │   ├── main.py
│   │   └── config.py
│   ├── uploads/
│   ├── tests/
│   └── requirements.txt
├── docs/
├── context.md
├── to-do.md
├── README.md
└── .env.example
```

## 13. Coding and product guardrails

1. Keep matching logic out of frontend components and out of free-form LLM prompts.
2. Keep third-party API response normalization inside integration adapters.
3. Use canonical identity IDs and deduplicate before scoring.
4. Store reasons for every hard-filter exclusion.
5. Store component scores and evidence for every displayed match.
6. Never silently turn an ambiguous JD phrase into a hard filter.
7. Never treat missing optional data as a failure.
8. Never treat unknown mandatory data as a pass.
9. Never fabricate candidate data, resume content, availability, or consent.
10. Distinguish registered and sourced candidates everywhere relevant.
11. Do not allow sourced non-members to enter the mutual-match flow.
12. Keep keys server-side and avoid logging PII unnecessarily.
13. Do not perform external human outreach during the hackathon.
14. Keep the MVP small: complete JD → discovery → deck → recruiter action → (for registered users) candidate response → mutual match.

## 14. Definition of done

The MVP is complete when:

- A recruiter can resolve/enrich a company.
- A recruiter can create a job using either structured fields or a pasted JD.
- The JD is transformed into a validated structured requirements object.
- Crustdata Person Search returns external candidate records using the team's key.
- Registered and external candidates are merged and deduplicated.
- Person data is normalized into the canonical Person model.
- Hard filters correctly exclude candidates and persist exclusion reasons.
- Eligible candidates receive deterministic component scores and direct/adjacent labels.
- The deck contains up to 20 candidates and never exceeds the adjacent cap.
- Cards explain why each candidate is shown and distinguish profile sources.
- Recruiter actions persist.
- Non-members can only be saved/shortlisted, not matched.
- A registered candidate can accept/reject interest and create a mutual match on acceptance.
- The full workflow can be demonstrated with a new JD and real Crustdata-backed discovery.
