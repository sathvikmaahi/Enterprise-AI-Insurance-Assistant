# Feature: Security Envelope (Phase 3)

## Purpose
Wrap the semantic layer with demo authentication, role-based concept access, question guardrails, and audit logging — before Bedrock is added.

Identity is **application-context propagation**: login yields `{username, role}` used for RBAC and audit. Queries still use the shared app DB credential — **not** database-level user impersonation.

Demo roles: **Customer Service Representative** (`csr`), adjuster, manager.

## What this branch adds
- `POST /auth/login` + bearer session tokens (app identity context)
- RBAC via concept `allowed_roles` (enforced in FastAPI before SQL)
- **Application** guardrails for destructive / out-of-scope / raw-SQL questions (`app/guardrails`) — distinct from Bedrock Guardrails
- In-memory audit logs (`GET /logs`)
- Tool API `POST /tools/{concept}`
- Design spec under `docs/superpowers/specs/`

## Depends on
`feat/03-semantic-layer`

## Demo moments
1. Login as `csr` / adjuster / manager
2. CSR denied on restricted claim concepts; adjuster allowed
3. Application guardrail blocks `"Delete all customers"`
4. `/logs` shows allow / deny / blocked

## CI/CD notes
- `uv run pytest tests/test_auth.py tests/test_rbac.py tests/test_guardrails.py tests/test_tools.py tests/test_logs.py`
- Set `DEMO_AUTH_SECRET` in CI secrets for non-default token signing
