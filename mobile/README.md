# SwipeHire mobile (Expo / React Native)

```bash
cd mobile
cp .env.example .env
npm install
npx expo start        # scan QR with Expo Go, or press i / a
```

| Env var | Meaning |
|---|---|
| `EXPO_PUBLIC_USE_MOCKS` | `true` = fictional demo data. `false` = live FastAPI backend (never falls back to mocks). |
| `EXPO_PUBLIC_API_BASE_URL` | iOS sim `http://localhost:8000` · Android emulator `http://10.0.2.2:8000` · real phone `http://<LAN-IP>:8000` |

Live mode uses: `GET /api/jobs`, `GET|POST /api/jobs/{id}/deck|discover`, `POST /api/jobs/{id}/actions`, `GET /api/jobs/{id}/shortlist`, `GET /api/candidates/{id}`, `GET /api/candidates/{id}/interests`, `POST /api/interests/{id}/respond`, `GET /api/matches`.

Recruiter flow: pick a job (created on the web dashboard) → swipe the deck → shortlist. Candidate flow: enter candidate ID → accept/decline interest → matches.
Not in the app yet: company/job creation, candidate onboarding and resume upload (use the web app). Scores are displayed only, never computed here.
