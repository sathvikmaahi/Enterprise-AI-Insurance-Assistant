# Feature: React Chat UI (Phase 5)

## Purpose
Interview-polished Vite + React demo UI: full-screen login, chat via `/ask`, role badge, suggested prompts, path/fallback meta, and always-visible audit logs.

## What this branch adds
- Auth-gated SPA (`LoginScreen` → three-zone `AppShell`)
- `api.js`: `login`, `ask`, `getLogs` (+ health)
- Session in `localStorage` with explicit logout
- UI README and `VITE_API_BASE_URL` via `.env.example`

## Depends on
`feat/05-bedrock-ask` (Phase 4 `/ask` + Phase 3 auth/logs)

## How to run
```bash
# API
uv run uvicorn app.main:app --reload --port 8000

# UI
cd frontend && npm install && npm run dev
```

## CI/CD notes
- Frontend job: `npm ci` + `npm run build` (and lint if configured)
- Backend job unchanged
- Deploy UI and API as separate artifacts; inject API base URL at build/runtime
