# Person 3 — Frontend: Candidate PWA & Recruiter Web Dashboard

> **Antigravity task file.** Use this file together with the shared `context.md`, `to-do.md`, and `README.md`. You own the entire frontend. Person 1 owns FastAPI routes and Crustdata/database integration. Person 2 owns JD/resume parsing and matching logic.

## 1. Mission

Build one Next.js application with two responsive experiences:

1. **Recruiter web dashboard (primary):** company onboarding, job creation, candidate discovery, swipeable candidate deck, shortlist/save/pass and mutual-match views.
2. **Candidate mobile-first PWA:** profile enrichment, resume upload, profile confirmation, preferences and accepting/rejecting recruiter interest.

The most important demo path is recruiter job submission → candidate deck → recruiter shortlist → registered candidate accepts → mutual match.

## 2. Files you own

Own the entire `frontend/` directory. Do not edit backend files or root shared documentation.

Suggested structure:

```text
frontend/
  app/
    page.tsx
    layout.tsx
    candidate/
      onboarding/page.tsx
      profile/page.tsx
      interests/page.tsx
    recruiter/
      company/page.tsx
      jobs/page.tsx
      jobs/new/page.tsx
      jobs/[jobId]/page.tsx
      jobs/[jobId]/deck/page.tsx
      shortlist/page.tsx
      matches/page.tsx
  components/
    CandidateCard.tsx
    CandidateDetailPanel.tsx
    SwipeControls.tsx
    MatchScore.tsx
    FitBadge.tsx
    MembershipBadge.tsx
    JobRequirementReview.tsx
    EmptyState.tsx
    LoadingState.tsx
    ErrorState.tsx
  lib/
    api.ts
    types.ts
    demo-data.ts
  public/
    manifest.json
    icons/
  package.json
```

You may adjust routing/layout if useful, but keep candidate and recruiter routes clearly separated. Use one shared Next.js app, not separate frontend repositories.

## 3. Technology and UI rules

- **Lovable is the frontend builder (web app + mobile app). Frontend only: do not enable Supabase or any Lovable-hosted backend; all calls go to the FastAPI backend via `API_BASE_URL`.** Lovable output is React + TypeScript + Tailwind (Vite), so Next.js-specific structure/env names in this file (`app/` routes, `NEXT_PUBLIC_API_BASE_URL`) map to Lovable equivalents (react-router routes, `VITE_API_BASE_URL`).
- React + TypeScript (Lovable-generated).
- Tailwind CSS.
- Mobile-first responsive layout for candidate PWA.
- Desktop-first recruiter dashboard.
- Use accessible buttons/keyboard controls as alternatives to swipe gestures.
- Do not require profile photographs. Candidate cards must look good with initials/avatar placeholders.
- Avoid overbuilding animations; clear candidate evidence and match reasons matter more.
- Store no Crustdata or Anthropic secret in frontend code or `NEXT_PUBLIC_*` variables.
- All data calls go to the SwipeHire FastAPI backend.

## 4. Shared backend API contract

Person 1 owns the backend. Use these routes and coordinate if their final schemas need small versioned adjustments. Do not make direct requests from the browser to Crustdata.

| Method | Route | Frontend use |
|---|---|---|
| `POST` | `/api/candidates/enrich` | Candidate pastes LinkedIn/profile URL |
| `POST` | `/api/candidates/register` | Candidate confirms profile and saves preferences |
| `POST` | `/api/candidates/{id}/resume` | Upload PDF/DOCX resume (multipart form) |
| `GET` | `/api/candidates/{id}` | Candidate profile page |
| `POST` | `/api/companies/resolve` | Recruiter enters company name/domain |
| `POST` | `/api/jobs` | Create job from structured form or raw JD |
| `GET` | `/api/jobs` | Company job list |
| `POST` | `/api/jobs/{id}/discover` | Trigger discovery and matching |
| `GET` | `/api/jobs/{id}/deck` | Load ranked candidate cards |
| `GET` | `/api/jobs/{id}/shortlist` | Shortlisted candidates |
| `POST` | `/api/jobs/{id}/actions` | Submit shortlist/pass/save action |
| `GET` | `/api/candidates/{id}/interests` | Candidate sees incoming company interest |
| `POST` | `/api/interests/{id}/respond` | Candidate accepts/rejects |
| `GET` | `/api/matches` | Mutual-match list |

Use configurable `NEXT_PUBLIC_API_BASE_URL` for the backend URL.

### Request examples

Enrich profile:
```json
{"profile_url":"https://www.linkedin.com/in/example/"}
```

Resolve company:
```json
{"company_name":"Example Inc","domain":"example.com"}
```

Create from JD:
```json
{"company_id":"...","input_type":"jd","raw_jd":"..."}
```

Create from structured fields:
```json
{"company_id":"...","input_type":"structured","requirements":{}}
```

Recruiter action:
```json
{"person_id":"...","action":"shortlist"}
```

Candidate response:
```json
{"response":"accept"}
```

### Deck response expected shape

Person 1's canonical response is `CandidateDeckResponse`, with:

```json
{
  "job_id":"...",
  "match_run_id":"...",
  "status":"completed",
  "total_candidates":20,
  "direct_count":17,
  "adjacent_count":3,
  "excluded_count":8,
  "cards":[
    {
      "person_id":"...",
      "name":"Example Candidate",
      "headline":"ML Engineer",
      "current_title":"Machine Learning Engineer",
      "current_company":"Example Labs",
      "origin":"crustdata_sourced",
      "membership_status":"not_registered",
      "fit_score":88.5,
      "fit_type":"adjacent",
      "evidence_coverage":0.72,
      "component_scores":{
        "skills":94,
        "experience":85,
        "role_domain":90,
        "trajectory":80,
        "context":75
      },
      "match_explanation":"Strong transferable ML and Python experience; Kubernetes is preferred but not shown.",
      "reasons":["Python and PyTorch evidence","Relevant production project"],
      "exclusion_reasons":[],
      "location":"Bengaluru",
      "skills":["Python","PyTorch","ML Systems"],
      "experience_years":3.5,
      "employment_history":[],
      "resume_highlights":[],
      "source_metadata":[]
    }
  ]
}
```

This is an illustrative frontend contract. Treat the backend's actual shared Pydantic schema as authoritative; keep `frontend/lib/types.ts` aligned with Person 1's final version. Unknown fields must display as `Not available` or `Needs confirmation`, never as fabricated values.

## 5. Recruiter flow — implement first

### Screen 1: company onboarding

- Company name/domain input.
- Resolve company button.
- Display returned company name, domain, industry, headcount and location where available.
- If multiple company matches are returned, show choices. Do not silently choose an ambiguous entity.

### Screen 2: create job

Offer two modes:

**Structured mode:**
- Role title.
- Seniority.
- Minimum/maximum experience.
- Locations and work modes.
- Must-have skills.
- Preferred skills.
- Mandatory qualifications.
- Preferred qualifications.
- Explicit required fields/dealbreakers.

**JD mode:**
- Large paste/upload text area.
- Submit to backend JD parser.
- Show normalized requirements for recruiter confirmation before discovery.
- Visually distinguish mandatory vs preferred vs ambiguous/needs confirmation.

### Screen 3: candidate discovery

- “Find candidates” button calls `POST /api/jobs/{id}/discover`.
- Show clear progress/loading state.
- When complete, show total discovered, eligible, excluded, direct and adjacent counts.
- Fetch `GET /api/jobs/{id}/deck` and render the cards.
- If zero candidates are available, show a helpful empty state rather than a blank page.

### Screen 4: candidate deck

Build the card UI before adding polish. The first visible card should show:

- Name and headline.
- Current role/company.
- Experience where calculable.
- Location if available.
- Match score.
- Direct-fit / Adjacent-fit badge.
- Registered / Not on platform badge.
- 3–5 skills.
- One-line match explanation.

Expanded detail should show:

- Career timeline.
- Relevant work experience.
- Resume projects/metrics only when a resume exists.
- Education.
- Available location/preferences.
- Evidence/source labels.
- Missing/unknown fields.
- Component scores and why the person was shown.

Actions:
- Right swipe / Shortlist.
- Left swipe / Pass.
- Save / Maybe.
- Buttons and keyboard controls must provide the same actions as touch swipes.

### Membership-state UI rules

**Registered candidate:** right swipe/shortlist shows that an interest request was sent; it can later become a mutual match after candidate acceptance.

**Crustdata-sourced non-member:** always show `Not on platform`. Recruiter can shortlist/save internally, but do not show “message”, “notify”, “request interview”, or mutual-match actions for that person. Do not imply that the person was contacted.

Adjacent-fit cards must be labelled and explain their transferable skills. Do not hide their missing preferred criteria.

## 6. Candidate PWA flow

### Onboarding

1. Enter LinkedIn/profile URL.
2. Call backend `/api/candidates/enrich`.
3. Display enriched profile for confirmation/editing.
4. Upload a PDF/DOCX resume using `/api/candidates/{id}/resume`.
5. Display parsed skills, projects and achievements for confirmation where the API returns them.
6. Collect target role, preferred locations, remote preference, availability/notice period and optional salary range/visibility.
7. Submit `/api/candidates/register`.

Use a short multi-step form with progress. Do not force candidates to retype profile data that was enriched successfully.

### Interests

- Candidate sees pending interest requests from `/api/candidates/{id}/interests`.
- Candidate can accept/reject through `/api/interests/{id}/respond`.
- On acceptance, show confirmation and mutual match.
- The demo flow stays local/in-app. Do not send external emails, LinkedIn messages, calls or interview invitations.

## 7. PWA requirements

- Add `manifest.json` with application name, short name, start URL, display mode and icons.
- Ensure the candidate flow works at phone widths and can be installed as a PWA where supported.
- Provide a clear “Add to Home Screen” experience only where the browser supports it; do not build native Android code.
- Keep recruiter dashboard usable on desktop and tablet.

## 8. API client and frontend state

Implement a single typed API client in `frontend/lib/api.ts`:

- Reads base URL from `NEXT_PUBLIC_API_BASE_URL`.
- Has typed functions for each route.
- Handles non-2xx responses and displays useful errors.
- Supports multipart resume upload.
- Does not store or send Crustdata/Anthropic API keys.

Keep reusable DTO definitions in `frontend/lib/types.ts`. Do not define API response structures separately inside every page.

If backend is not yet available on your device:

- Build the UI against `frontend/lib/demo-data.ts` fixtures that follow the same contract.
- Put mock mode behind one explicit development flag.
- Make it easy to switch to the real API client without rewriting screens.
- Do not let demo fixtures masquerade as live Crustdata data; label demo/mock mode clearly.

## 9. Design system guidance

- Product name: SwipeHire.
- Positioning: “Discover talent beyond keywords.”
- Use a clean, modern, professional hiring product aesthetic.
- Recruiter cards should emphasize match reasoning, not just large percentages.
- Use visually distinct but restrained badges: `Direct fit`, `Adjacent fit`, `Registered`, `Not on platform`.
- Use a neutral background, strong typography, compact skill tags and clear action buttons.
- Provide loading, empty, error and partial-data states.
- Do not add public candidate contact details or sensitive personal information to cards.
- Salary is private unless the candidate explicitly allows visibility.

## 10. Tests and acceptance criteria

- [ ] Candidate onboarding is mobile-optimized and works with a profile URL.
- [ ] Enriched profile confirmation prevents unnecessary retyping.
- [ ] Resume upload supports PDF/DOCX and shows parse result.
- [ ] Preferences and optional salary visibility are represented correctly.
- [ ] Company resolution shows returned data and ambiguity choices.
- [ ] Both structured job creation and JD paste modes work.
- [ ] Recruiter can confirm parsed requirements before discovery.
- [ ] Candidate deck displays scores, reasons, fit type and membership status.
- [ ] Expanded card shows career history and available resume highlights.
- [ ] Direct and adjacent cards are clearly distinguished.
- [ ] Non-members cannot access mutual-match controls.
- [ ] Recruiter actions are sent to backend and persist after reload.
- [ ] Registered candidate can accept/reject interest in candidate PWA.
- [ ] Acceptance creates and displays a mutual match.
- [ ] Frontend works with real backend base URL and with clearly labelled local mock mode.
- [ ] No third-party secret is present in frontend bundle or Git.

## 11. Git / merge rules

- Work on branch: `work/person-3-frontend`.
- Commit only `frontend/`.
- Do not modify backend code, requirements, root env example, `context.md`, `to-do.md`, or `README.md`.
- Send Person 1 any mismatch you find in API contracts rather than silently changing backend assumptions.
- Use small commits: `frontend: add recruiter shell`, `frontend: add job creation`, `frontend: add candidate deck`, `frontend: add candidate PWA onboarding`, etc.
- Keep mock fixtures in `frontend/lib/demo-data.ts`; remove or disable mock mode for final live demo.

## 12. Antigravity instruction

Read shared `context.md`, `to-do.md`, and `README.md` completely before editing. Implement a usable, polished two-sided frontend, but prioritize the recruiter job-to-deck path. Use the exact backend contract above, keep API calls centralized, and make the registered vs non-member distinction impossible to miss in the UI.
