# Feature: Database / Amazon RDS (Phase 1)

## Purpose
Connect the API to Amazon RDS PostgreSQL with a pooled client, schema/seed for insurance demo data, and a health check that reports DB connectivity.

## What this branch adds
- `app/db` connection pool + `check_db()`
- `db/schema.sql`, `db/seed.sql`, `db/generate_seed.py`
- `infra/rds/notes.md` setup notes
- `/health` returns `db` status
- DB-focused tests

## Depends on
`feat/01-project-scaffold`

## How to verify
```bash
# Set DATABASE_URL in .env (never commit .env)
uv run uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
```

## CI/CD notes
- Provide `DATABASE_URL` as a secret/variable for integration jobs
- Unit tests mock DB where possible; optional job against a Postgres service container
