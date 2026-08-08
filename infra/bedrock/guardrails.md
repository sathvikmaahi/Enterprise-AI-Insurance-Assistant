# Bedrock Guardrails (Phase 7)

POC adds **Amazon Bedrock Guardrails** alongside the existing app-level regex guardrails in `app/guardrails/rules.py`.

## Flow

```text
POST /ask
  → app guardrails (check_question)
  → Bedrock Guardrails input (apply_guardrail, if configured)
  → Agent path OR Converse fallback
       fallback: guardrailConfig on converse (input + output)
```

App guardrails run first (fast, offline). Bedrock Guardrails add managed topic/content/word/PII policies from AWS.

## Env vars

| Variable | Purpose |
|---|---|
| `BEDROCK_GUARDRAIL_ID` | Guardrail ID or ARN |
| `BEDROCK_GUARDRAIL_VERSION` | Version number or `DRAFT` (default) |

When unset, Bedrock Guardrails are skipped and the app behaves as before.

Example (after creating the resource):

```bash
BEDROCK_GUARDRAIL_ID=abc123xyz
BEDROCK_GUARDRAIL_VERSION=1
```

## Create guardrail (AWS CLI)

Run from repo root (requires `bedrock:CreateGuardrail` and related IAM):

```bash
aws bedrock create-guardrail \
  --region us-east-1 \
  --name insurance-assistant-guardrails \
  --description "Insurance POC — block destructive, off-domain, and over-broad PII asks" \
  --blocked-input-messaging "Sorry, I can only help with insurance policy and claims questions." \
  --blocked-outputs-messaging "Sorry, I cannot provide that information." \
  --content-policy-config '{
    "filtersConfig": [
      {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "VIOLENCE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "HIGH"}
    ]
  }' \
  --topic-policy-config '{
    "topicsConfig": [
      {
        "name": "Financial advice",
        "definition": "Investment, stock, crypto, or trading recommendations outside insurance products.",
        "examples": ["What bitcoin should I buy?", "Best stock tip for today"],
        "type": "DENY"
      },
      {
        "name": "Medical advice",
        "definition": "Diagnosis, treatment, or prescription guidance unrelated to insurance claims.",
        "examples": ["What medicine should I take?", "Diagnose my symptoms"],
        "type": "DENY"
      },
      {
        "name": "Off-domain general",
        "definition": "Recipes, weather, or other topics unrelated to insurance policies and claims.",
        "examples": ["Give me a pasta recipe", "Will it rain tomorrow?"],
        "type": "DENY"
      }
    ]
  }' \
  --word-policy-config '{
    "wordsConfig": [
      {"text": "drop table"},
      {"text": "truncate"},
      {"text": "delete all customers"}
    ],
    "managedWordListsConfig": [{"type": "PROFANITY"}]
  }'
```

Note the `guardrailId` from the response, then create version 1:

```bash
aws bedrock create-guardrail-version \
  --region us-east-1 \
  --guardrail-identifier <GUARDRAIL_ID> \
  --description "Initial published version"
```

## Attach to Bedrock Agent (optional)

For output filtering on the Agent path, attach the same guardrail to the agent in console or CLI:

```bash
aws bedrock-agent update-agent \
  --region us-east-1 \
  --agent-id S8UUWCCNNG \
  --guardrail-configuration guardrailIdentifier=<GUARDRAIL_ID>,guardrailVersion=1 \
  ... # include other required agent fields from get-agent
```

Input is already screened in FastAPI via `apply_guardrail` before `invoke_agent`.

## Attach to existing Agent alias

After updating the agent, re-prepare and use the published alias as today (`BEDROCK_AGENT_ALIAS_ID`).

## Smoke test

```bash
# With guardrail env set and API restarted
TOKEN=$(curl -s localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"agent","password":"agent123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# Should pass app + Bedrock guardrails
curl -s localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What policies does customer John have?"}' | python3 -m json.tool

# Off-domain — blocked by app guardrails and/or Bedrock
curl -s localhost:8000/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"question":"What bitcoin stock should I buy?"}' | python3 -m json.tool
```

## Code map

| File | Role |
|---|---|
| `app/guardrails/bedrock.py` | `apply_guardrail` input check + Converse config helper |
| `app/api/ask.py` | Runs Bedrock input check after app guardrails |
| `app/bedrock/fallback.py` | Passes `guardrailConfig`; handles `guardrail_intervened` |
| `app/bedrock/config.py` | `BEDROCK_GUARDRAIL_*` env |

## Tests

```bash
uv run pytest tests/test_bedrock_guardrails.py tests/test_ask.py tests/test_fallback.py -q
```
