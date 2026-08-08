# Feature: Bedrock Guardrails (Phase 7)

## Purpose
Add **Amazon Bedrock Guardrails** for managed content safety on `/ask`, complementing the existing app-level regex guardrails.

## What this branch adds
- `app/guardrails/bedrock.py` — `apply_guardrail` input screening + Converse config
- `BEDROCK_GUARDRAIL_ID` / `BEDROCK_GUARDRAIL_VERSION` env support
- Input check on `POST /ask` before Agent / fallback
- `guardrailConfig` on Converse fallback + handling for `guardrail_intervened`
- Infra notes: `infra/bedrock/guardrails.md`
- Tests: `tests/test_bedrock_guardrails.py`

## Depends on
`feat/05-bedrock-ask` (merged on `main`)

## Layering

| Layer | When | Block response |
|---|---|---|
| App guardrails (`check_question`) | Always | 400 `Blocked by guardrail` |
| Bedrock input (`apply_guardrail`) | When env configured | 400 `Blocked by Bedrock Guardrails` |
| Bedrock inline (Converse) | Fallback path | Guardrail message in answer or 400 on input |

## CI/CD notes
- Unit tests mock `bedrock-runtime.apply_guardrail` — no AWS required
- Live guardrail needs `bedrock:ApplyGuardrail` on the runtime role/user
