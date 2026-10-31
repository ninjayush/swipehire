# SwipeHire — Three-Person Parallel Build & Merge Guide

This guide is shared coordination material for the three workstreams. Each person must also read the corresponding individual assignment file.

## Workstream ownership

| Person | Branch | Owns | Must not modify |
|---|---|---|---|
| 1 — Backend + Crustdata | `work/person-1-backend` | `backend/app/api/`, `integrations/`, `models/`, `database/`, core services, backend root, `.env.example` | `frontend/`, `backend/app/ai/`, `backend/app/matching/` |
| 2 — AI + Matching | `work/person-2-ai-matching` | `backend/app/ai/`, `backend/app/matching/`, matching tests | API routes, shared schemas/models, integrations, frontend, requirements |
| 3 — Frontend | `work/person-3-frontend` | `frontend/` | All backend files and root shared docs |

All three branches start from the same base commit containing `context.md`, `to-do.md`, and `README.md`.

## Interface freeze

1. Person 1 owns the canonical Pydantic schemas in `backend/app/database/schemas.py`.
2. Person 2 imports those schemas and implements the declared parser/matching functions; Person 2 does not copy or redefine them.
3. Person 1 owns the REST routes and calls Person 2's public functions.
4. Person 3 mirrors the same backend contracts in `frontend/lib/types.ts` and calls only FastAPI routes.
5. If a contract must change, Person 1 updates the canonical backend schema, then sends the new version to Person 2 and Person 3. Do not make silent unilateral changes.

## Public AI service interfaces

The agreed initial interfaces are:

```python
parse_job_description(raw_jd: str) -> JobRequirements
parse_resume_text(resume_text: str) -> dict
build_candidate_deck(
    requirements: JobRequirements,
    candidates: list[PersonRecord],
    deck_size: int = 20,
) -> tuple[list[CandidateEvaluation], list[CandidateEvaluation]]
```

Tuple result: `(displayed_evaluations, excluded_evaluations)`.

Person 2 must tell Person 1 before changing these to async functions or changing the argument/return semantics.

## Frontend/backend REST interfaces

The route list and request examples are in `person-1-backend-crustdata.md` and `person-3-frontend.md`. The backend contract is authoritative. Person 3 should use local fixtures until Person 1's backend is running.

## Merge order

1. **Person 1 first:** merge the backend skeleton, shared Pydantic schemas, database models, Crustdata client and route stubs. Share the commit hash and schemas with the team early.
2. **Person 2 second:** merge isolated `ai/` and `matching/` packages plus tests. Person 1 resolves only import/integration wiring in their owned files.
3. **Person 3 third:** merge the isolated `frontend/` directory. Connect its API client to the backend routes and fix only frontend-owned code for UI/API binding issues.
4. Person 1 (integration owner) runs the full app and makes final backend wiring fixes. Any changes in another person's owned folder should be sent to that owner or agreed explicitly.

## Git workflow

Example shared repository workflow:

```bash
# Each person clones the same repository and creates their own branch.
git checkout -b work/person-1-backend
# or work/person-2-ai-matching
# or work/person-3-frontend

# Commit only owned directories.
git add backend/app/api backend/app/integrations backend/app/models backend/app/database
# Use the paths appropriate to your assignment.
git commit -m "backend: implement Crustdata and API foundation"
git push -u origin HEAD
```

Integration owner merges in the order above, preferably through PRs. Rebase or merge the latest base branch before final integration. Do not copy entire project folders between devices; use Git branches.

## Integration smoke test

The final integration is not complete until this exact path succeeds:

1. Start FastAPI and Next.js.
2. Resolve a company through Crustdata.
3. Create a job from an unseen pasted JD.
4. Confirm structured mandatory/preferred requirements.
5. Run discovery against registered local candidates and Crustdata Person Search.
6. Confirm normalization/deduplication.
7. Confirm failed mandatory candidates are excluded with reasons.
8. Confirm direct and adjacent candidates are ranked and the adjacent cap is respected.
9. Render the candidate deck in recruiter dashboard.
10. Shortlist a sourced non-member; verify it is internal-only with no mutual-match route.
11. Shortlist a registered candidate; switch to candidate PWA and accept; verify a mutual match is created.

## Shared conventions

- Python package root: `backend/app/`; import paths should consistently use `app...` when launched from `backend/`.
- Frontend uses one `NEXT_PUBLIC_API_BASE_URL`; no direct Crustdata calls from browser.
- JSON fields use `snake_case` in backend responses and types reflect this exactly. UI can display human-readable labels.
- IDs are strings in frontend DTOs; preserve numeric `crustdata_person_id` separately when returned.
- `origin`: `registered` or `crustdata_sourced`.
- `membership_status`: `registered` or `not_registered`.
- `fit_type`: `direct` or `adjacent`.
- Recruiter actions: `shortlist`, `pass`, `save`.
- Interest response: `accept`, `reject`.
- No external outreach or contact with real people during hackathon demo.
- Never commit `.env`, API keys, actual resumes, or unnecessary personal information.
