# Feature: Security Envelope (Phase 3)

## Purpose
Wrap the semantic layer with demo authentication, role-based concept access, question guardrails, and audit logging — before Bedrock is added.

## What this branch adds
- `POST /auth/login` + bearer session tokens
- RBAC via concept `allowed_roles`
- Guardrails for destructive / out-of-scope questions
- In-memory audit logs (`GET /logs`)
- Tool API `POST /tools/{concept}`
- Design spec under `docs/superpowers/specs/`

## Depends on
`feat/03-semantic-layer`

## Demo moments
1. Login as agent / adjuster / manager
2. Agent denied on restricted concepts; adjuster allowed
3. Guardrail blocks `"Delete all customers"`
4. `/logs` shows allow / deny / blocked

## CI/CD notes
- `uv run pytest tests/test_auth.py tests/test_rbac.py tests/test_guardrails.py tests/test_tools.py tests/test_logs.py`
- Set `DEMO_AUTH_SECRET` in CI secrets for non-default token signing
