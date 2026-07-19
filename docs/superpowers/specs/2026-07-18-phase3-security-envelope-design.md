# Phase 3 — Security Envelope Design

**Date:** 2026-07-18  
**Status:** Implemented (Approach 1, RBAC Option A)  
**Depends on:** Phase 0 scaffold, Phase 1 RDS/DB client, Phase 2 semantic layer  
**Does not include:** Bedrock / `POST /ask` (Phase 4), React chat UI (Phase 5)

---

## 1. Goal

Add the demo security moments — login, role-based concept access, guardrail blocks, and audit logs — as stable HTTP APIs that wrap the existing semantic layer. No Bedrock yet.

**Success criteria (curl-demoable):**

1. Login as Agent / Adjuster / Manager and receive a bearer token + role  
2. Agent calling `open_claims` → **403 Access denied**  
3. Adjuster calling `open_claims` → **200** with rows  
4. Question `"Delete all customers"` → **400** blocked by guardrail  
5. `GET /logs` shows allow / deny / blocked entries with latency  

---

## 2. Architecture

```text
Client (curl / later React)
        │
        ▼
┌───────────────────────────────────────────┐
│  FastAPI                                  │
│  POST /auth/login                         │
│  POST /tools/{concept}                    │
│       ├─ require session (Bearer)         │
│       ├─ guardrails (if question present) │
│       ├─ rbac.assert_allowed(concept,role)│
│       ├─ semantic.resolve(concept, params)│
│       └─ audit.record(...)                │
│  GET /logs                                │
│  GET /tools/ping · GET /health            │
└───────────────────────────────────────────┘
        │
        ▼
   app/semantic (Phase 2) → Amazon RDS
```

### Package boundaries

| Package | Responsibility |
|---|---|
| `app/auth` | Demo users, HMAC session tokens, FastAPI dependency for current user |
| `app/rbac` | Concept-level allow/deny from YAML `allowed_roles` |
| `app/guardrails` | Pattern checks on free-text questions |
| `app/logging` | In-memory audit ring buffer |
| `app/api` | HTTP routers: login, tools, logs, ping |
| `app/semantic` | Unchanged resolve path (no role argument) |

### Design rules

- SQL is generated only by the semantic layer from approved YAML templates  
- RBAC is enforced at the API boundary **before** `resolve()`  
- Concept availability depends on the caller's role (not all concepts for everyone)  
- Bedrock Agent / `POST /ask` are out of scope  
- No row-level or column-level filters in this phase  

---

## 3. Auth

### Demo users (hardcoded)

| Username | Password | Role |
|---|---|---|
| `agent` | `agent123` | `agent` |
| `adjuster` | `adjuster123` | `adjuster` |
| `manager` | `manager123` | `manager` |

### Login

- `POST /auth/login`  
- Body: `{ "username": "...", "password": "..." }`  
- Success: `{ "access_token": "...", "token_type": "bearer", "role": "...", "username": "..." }`  
- Failure: **401** invalid credentials  

### Session token

- HMAC-SHA256 signed payload (`username`, `role`, `exp`) using `DEMO_AUTH_SECRET`  
- Stdlib only (`hmac`, `hashlib`, `base64`, `json`) — no JWT dependency  
- Clients send `Authorization: Bearer <token>`  
- Missing / invalid / expired token → **401**  
- Token TTL: 8 hours (demo-friendly)  

### Current-user dependency

- FastAPI `Depends(get_current_user)` returns `{ username, role }`  
- Used by `/tools/*` and `/logs`  

---

## 4. RBAC (Option A — concept-level only)

### Role matrix

| Concept | agent | adjuster | manager |
|---|---|---|---|
| `customer_policies` | allow | allow | allow |
| `policy_premium` | allow | allow | allow |
| `coverage_by_type` | allow | allow | allow |
| `open_claims` | **deny** | allow | allow |
| `claim_summary` | **deny** | allow | allow |

### YAML changes

- `open_claims.yaml` / `claim_summary.yaml`: `allowed_roles` = `[adjuster, manager]` (remove `agent`)  
- Other concepts keep `[agent, adjuster, manager]`  

### Enforcement

- `assert_allowed(concept_name: str, role: str) -> None`  
- Loads concept via existing `get_concepts()`; if `role` not in `allowed_roles`, raise `AccessDeniedError`  
- Tool handler maps that to **403** `{ "detail": "Access denied", "concept": "...", "role": "..." }`  
- `resolve()` remains role-agnostic  

---

## 5. Guardrails

Pure function: `check_question(text: str) -> GuardrailResult(allowed: bool, reason: str | None)`.

| Category | Examples blocked |
|---|---|
| Destructive intent | `delete`, `drop table`, `truncate`, `update ... set` |
| Raw SQL | `select * from`, SQL comment injections, obvious SQL shape |
| Over-broad PII dump | “all customers with email/ssn”, “dump all emails” |
| Off-domain | stocks, medical advice, unrelated non-insurance asks |

### When they run

- If tool body includes non-empty `question`, run guardrails first  
- If only structured `params` (no question), skip NL guardrails; RBAC still applies  
- Block → **400** `{ "detail": "Blocked by guardrail", "reason": "..." }` + audit entry with `decision=blocked`  

---

## 6. Audit logging

### Store

- In-memory ring buffer, capacity **200** entries  
- Process restart clears logs (acceptable for POC)  

### Entry fields

| Field | Meaning |
|---|---|
| `timestamp` | ISO-8601 UTC |
| `username` | Caller |
| `role` | Caller role |
| `concept` | Tool / concept name (or null for pure guardrail pre-check) |
| `params` | Bound params (safe; no secrets) |
| `sql` | Approved SQL template text when resolve ran (or null) |
| `decision` | `allow` \| `deny` \| `blocked` |
| `reason` | Optional deny/block reason |
| `latency_ms` | End-to-end tool handler time |
| `row_count` | Rows returned on allow (else 0) |

### API

- `record(...)` appends (evicts oldest when over capacity)  
- `list_recent(limit: int = 50) -> list[AuditEntry]` newest-first  
- `GET /logs?limit=50` requires auth; any logged-in demo role may read  

---

## 7. API surface

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/auth/login` | no | Demo login |
| `GET` | `/tools/ping` | no | Connectivity check |
| `POST` | `/tools/{concept}` | yes | Guardrails → RBAC → resolve → audit |
| `GET` | `/logs` | yes | Recent audit entries |
| `GET` | `/health` | no | Unchanged |

### Tool request

```json
{
  "params": { "customer_name": "John" },
  "question": "optional free text for guardrails"
}
```

### Tool success response

```json
{
  "concept": "customer_policies",
  "role": "agent",
  "row_count": 1,
  "rows": []
}
```

- **Never** include `sql` in the HTTP tool response in Phase 3  
- Always store `sql` on the audit entry when resolve runs (visible via `GET /logs`)  

### Error mapping

| Case | Status | Signal |
|---|---|---|
| Bad login | 401 | Invalid credentials |
| Missing/bad/expired token | 401 | Not authenticated |
| RBAC deny | 403 | Access denied |
| Guardrail block | 400 | Blocked by guardrail |
| Unknown concept | 404 | Unknown concept |
| Missing concept params | 422 | Missing parameter / validation |

### Tool handler order

1. Authenticate  
2. Start timer  
3. If `question` present → guardrails (on fail: audit blocked, return 400)  
4. RBAC `assert_allowed` (on fail: audit deny, return 403)  
5. `resolve(concept, params)` (map ConceptNotFound → 404, MissingParameter → 422)  
6. Audit allow + latency + row_count  
7. Return rows  

---

## 8. Files

| Path | Action |
|---|---|
| `app/auth/users.py` | Create — demo user table |
| `app/auth/tokens.py` | Create — issue/verify HMAC token |
| `app/auth/deps.py` | Create — `get_current_user` |
| `app/rbac/check.py` | Create — `assert_allowed` |
| `app/guardrails/rules.py` | Create — `check_question` |
| `app/logging/audit.py` | Create — ring buffer |
| `app/api/auth.py` | Create — login router |
| `app/api/tools.py` | Create — ping + concept tools |
| `app/api/logs.py` | Create — logs router |
| `app/main.py` | Modify — include routers |
| `app/semantic/concepts/open_claims.yaml` | Modify — drop `agent` from roles |
| `app/semantic/concepts/claim_summary.yaml` | Modify — drop `agent` from roles |
| `tests/test_auth.py` | Create |
| `tests/test_rbac.py` | Create |
| `tests/test_guardrails.py` | Create |
| `tests/test_tools.py` | Create |
| `tests/test_logs.py` | Create |
| `.env.example` | Confirm `DEMO_AUTH_SECRET` present |

---

## 9. Testing strategy

- Unit: token issue/verify, RBAC allow/deny, guardrail patterns, audit ring buffer  
- API (httpx + FastAPI TestClient): login, tools with mocked `resolve` where needed, logs  
- Live optional: Adjuster `open_claims` against RDS when `DATABASE_URL` set  
- Regression: existing `tests/test_semantic.py`, `test_db.py`, `test_health.py` still pass  
- Update `test_allowed_roles_present_but_not_enforced` — enforcement now lives in RBAC/tools tests  

---

## 10. Out of scope

- Amazon Cognito / real SSO  
- Private networking / non-public RDS  
- CloudWatch dashboards  
- Bedrock Guardrails resource / Agent wiring  
- `POST /ask`  
- React login / chat / logs panel UI  
- Row-level or column-level RBAC  
- Persistent audit database  

---

## 11. Demo script (Phase 3 checkpoint)

```bash
# 1) Login as agent
curl -s -X POST localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"agent","password":"agent123"}'

# 2) Agent denied on open_claims (use token from step 1)
curl -s -X POST localhost:8000/tools/open_claims \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"params":{}}'

# 3) Login as adjuster → same tool succeeds
# 4) Guardrail block
curl -s -X POST localhost:8000/tools/customer_policies \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"params":{"customer_name":"John"},"question":"Delete all customers"}'

# 5) GET /logs → see deny / allow / blocked
```
