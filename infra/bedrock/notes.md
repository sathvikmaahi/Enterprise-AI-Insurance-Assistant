# Bedrock Agent setup (Phase 4)

POC path: **Agent first (return-control)** → on failure **Converse + tool use**.

Both paths execute semantic concepts in-process via `app/bedrock/runner.py` (RBAC → `resolve` → audit). The model never receives DB credentials.

## Live resources (this account)

Created in **us-east-1** for the Semantic Layer POC:

| Resource | Value |
|---|---|
| Agent name | `insurance-semantic-assistant` |
| Agent ID | `S8UUWCCNNG` |
| Alias name | `live` |
| Alias ID | `XDYGKRSAEH` |
| Foundation model | `amazon.nova-lite-v1:0` |
| Action group | `SemanticTools` (`RETURN_CONTROL`) |
| IAM role | `AmazonBedrockExecutionRoleForAgents_SemanticLayer` |

Put these in `.env`:

```bash
AWS_REGION=us-east-1
BEDROCK_AGENT_ID=S8UUWCCNNG
BEDROCK_AGENT_ALIAS_ID=XDYGKRSAEH
BEDROCK_FALLBACK_MODEL_ID=amazon.nova-lite-v1:0
BEDROCK_FORCE_FALLBACK=false
```

Credentials: standard AWS chain (`AWS_PROFILE`, env keys, or instance role). Your local CLI user must be allowed to call `bedrock:InvokeAgent` / `bedrock:InvokeModel`.

## Env vars

| Variable | Purpose |
|---|---|
| `AWS_REGION` | e.g. `us-east-1` |
| `BEDROCK_AGENT_ID` | Agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | Published alias |
| `BEDROCK_FALLBACK_MODEL_ID` | e.g. `amazon.nova-lite-v1:0` |
| `BEDROCK_FORCE_FALLBACK` | `true` to skip Agent and demo the fallback story |

## Action group functions

| Function | Params |
|---|---|
| `customer_policies` | `customer_name` (required) |
| `policy_premium` | `policy_id` (required) |
| `coverage_by_type` | `coverage_type` (required) |
| `open_claims` | (none) |
| `claim_summary` | `policy_id` and/or `customer_name` |

FastAPI handles results locally; the Agent does **not** need a public URL to call `/tools/*`.

## Smoke test

```bash
# restart uvicorn so it picks up .env
TOKEN=$(curl -s localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"agent","password":"agent123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -s localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What policies does customer John have?"}' | python3 -m json.tool
```

Expect `"path": "agent"` when Agent works. Set `BEDROCK_FORCE_FALLBACK=true` and restart to demo `"path": "fallback"`.

## Recreate (if needed)

```bash
# high-level: IAM role → create-agent → create-agent-action-group (RETURN_CONTROL)
# → prepare-agent → create-agent-alias
aws bedrock-agent list-agents --region us-east-1
aws bedrock-agent list-agent-aliases --agent-id S8UUWCCNNG --region us-east-1
```

## Local without AWS

Unit/API tests mock boto3. Live `/ask` needs the env vars above and model/agent access in the account.
