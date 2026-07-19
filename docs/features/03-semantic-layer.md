# Feature: Semantic Layer (Phase 2)

## Purpose
Map business concepts (e.g. open claims, policy premium) to approved parameterized SQL templates so AI/tools never invent free-form SQL.

## What this branch adds
- YAML concept definitions under `app/semantic/concepts/`
- Loader, models, and `resolve()` path
- Tests for concept loading and resolution

## Depends on
`feat/02-database-rds`

## Key idea for stakeholders
The model (or API caller) asks for a **business concept**; engineering controls the SQL. Definitions stay consistent across teams.

## CI/CD notes
- `uv run pytest tests/test_semantic.py`
- Treat concept YAML changes as reviewable policy/code
