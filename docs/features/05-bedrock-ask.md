# Feature: Bedrock Ask (Phase 4)

## Purpose
Answer natural-language insurance questions via Amazon Bedrock Agent (return-control) with a Converse tool-use fallback. Tools still enforce RBAC + audit.

## What this branch adds
- `POST /ask`
- Bedrock Agent + fallback orchestrator
- In-process tool runner (no raw SQL from the model)
- Infra notes under `infra/bedrock/`
- Tests for ask / agent / fallback / runner

## Depends on
`feat/04-security-envelope`

## Response contract
- `path: "agent" | "fallback"`
- Fallback includes `fallback_reason` when used

## CI/CD notes
- Mock Bedrock clients in unit tests (no AWS calls required)
- Optional integration job needs `AWS_REGION`, agent IDs, and IAM role/OIDC
- Never commit long-lived AWS keys
