# SwipeHire frontend

Vite + React + TypeScript + Tailwind v4. One app: desktop-first recruiter dashboard (`/recruiter/*`) and mobile-first installable candidate PWA (`/candidate/*`). FastAPI (`backend/`) is the only product backend.

## Run
```bash
cd frontend
cp .env.example .env     # VITE_USE_MOCKS=true for demo data
npm install
npm run dev              # http://localhost:5173
npm run build            # type-check + production build
```

## Environment
| Var | Meaning |
|---|---|
| `VITE_USE_MOCKS` | `true` = fictional in-browser demo data (banner shown). Anything else = live backend. **Live mode never falls back to mocks.** |
| `VITE_API_BASE_URL` | FastAPI base URL, default `http://localhost:8000` |

No API keys belong in the frontend; Crustdata/Anthropic are only called by the backend.

## Layout
- `src/api/client.ts` – the only module UI code uses (typed, mock/live switch)
- `src/api/http.ts` – fetch wrapper, normalised `ApiError` (network / validation / unauthorized / not_found / server)
- `src/api/mapping.ts` – maps backend responses to frontend types (deck `cards` = `{person, evaluation}`; flat dicts tolerated)
- `src/api/mock.ts` – fictional demo fixtures (direct, adjacent, non-member, unknown fields)
- `src/components/SwipeDeck.tsx` – drag threshold 140px, ← pass, → shortlist/interest, ↓ save, visible buttons, reduced-motion aware

## Backend assumptions / gaps
- Types mirror `backend/app/database/schemas.py`. Scores are only displayed, never computed.
- `POST /api/jobs/{id}/actions` is used for shortlist/pass/save. No undo (backend has no contract for it).
- No "list saved" endpoint → Saved page uses a browser-local list (`src/state/saved.ts`).
- No recruiter-side "interests" endpoint → Interests page derives from `/shortlist` (registered only) + `/api/matches`. Declined interests are not visible to recruiters.
- Job requirements are confirmed via `PATCH /api/jobs/{id}`.
- Candidate onboarding: `enrich` → `register` (with preferences) → `resume` upload. Demo entry = enter a candidate ID (live) or "demo candidate" (mock).
- Non-members: labelled "Not on platform"; shortlist is internal-only, no interest/match UI.
- Registered candidates have to be seeded by the backend for deck/interests to show them.
