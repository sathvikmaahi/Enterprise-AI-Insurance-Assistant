# Feature: React Chat UI (Phase 5)

## Purpose
Provide a Vite + React demo UI for login, natural-language ask, role visibility, and recent audit logs against the FastAPI backend.

## What this branch adds
- `frontend/` React (Vite) app
- API client pointed at `VITE_API_BASE_URL`
- UI README and frontend env example

## Depends on
`feat/05-bedrock-ask`

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
