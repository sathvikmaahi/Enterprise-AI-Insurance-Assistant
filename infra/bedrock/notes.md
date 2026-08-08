# Bedrock Agent setup (Phase 4)

POC path: **Agent first (return-control)** → on failure **Converse + tool use**.

Both paths execute semantic concepts in-process via `app/bedrock/runner.py` (RBAC → `resolve` → audit). The model never receives DB credentials.

Identity: FastAPI propagates the demo session’s `{username, role}` (including Bedrock `promptSessionAttributes`). That is **application-context propagation** for concept RBAC and audit — not database-level user impersonation. SQL still runs on the shared app connection pool.

## Env vars

| Variable | Purpose |
|---|---|
| `AWS_REGION` | e.g. `us-east-1` |
| `BEDROCK_AGENT_ID` | Agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | Published alias |
| `BEDROCK_FALLBACK_MODEL_ID` | e.g. `amazon.nova-lite-v1:0` or a Claude model ID |
| `BEDROCK_FORCE_FALLBACK` | `true` to skip Agent and demo the fallback story |

Credentials: standard AWS chain (`AWS_PROFILE`, env keys, or instance role).

## Agent action group (return control)

Create an action group named **`SemanticTools`** with **Return control** (functions), one function per concept:

- `customer_policies` — param `customer_name` (string, required)
- `policy_premium` — param `policy_id` (string, required)
- `coverage_by_type` — param `coverage_type` (string, required)
- `open_claims` — no params
- `claim_summary` — params `policy_id`, `customer_name` (at least one)
- `claims_by_damage_type` — param `damage_type` (string, required; JSONB `claim_details->>'damage_type'`)

FastAPI handles function results locally; the Agent does **not** need a public URL to call `/tools/*` for this POC.

## Demo tip

1. With Agent configured → `POST /ask` returns `"path": "agent"`.
2. Set `BEDROCK_FORCE_FALLBACK=true` (or clear Agent IDs) → `"path": "fallback"` and `fallback_reason` explains why — interview talking point.

## Local without AWS

Unit/API tests mock boto3. Live `/ask` needs at least `BEDROCK_FALLBACK_MODEL_ID` (and model access in the account) if the Agent is not configured.
