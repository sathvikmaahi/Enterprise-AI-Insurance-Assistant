# Feature: Project Scaffold (Phase 0)

## Purpose
Bootstrap the Enterprise AI Insurance Assistant backend so the team can run a FastAPI app locally with a health endpoint and a reproducible Python toolchain (`uv`).

## What this branch adds
- FastAPI app entrypoint with `GET /health`
- `pyproject.toml` / `uv.lock` dependency management
- Root `README.md` and `docs/techstack.md`
- Baseline `.gitignore` and `.env.example`
- Smoke test for `/health`

## How to run
```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
```

## CI/CD notes
- Install with `uv sync --frozen`
- Run `uv run pytest tests/test_health.py`
- No secrets required for this phase
