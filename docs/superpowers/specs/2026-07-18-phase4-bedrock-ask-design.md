# Phase 4 — Bedrock Ask (Agent + Fallback) Design

**Date:** 2026-07-18  
**Status:** Implemented (Approach 1)  
**Depends on:** Phase 3 security envelope  
**Does not include:** React chat UI (Phase 5)

---

## 1. Goal

Add `POST /ask` that answers natural-language insurance questions via Amazon Bedrock:

1. Try **Bedrock Agent** with **return-control** (tools run in-process)
2. On Agent failure / missing config / `BEDROCK_FORCE_FALLBACK` → **Converse + tool use**
3. Response includes `path: "agent" | "fallback"` so the fallback is a demoable feature

**Success criteria:**

1. Auth required on `/ask`  
2. Guardrail blocks destructive questions before Bedrock  
3. Agent success → `path: "agent"`  
4. Agent failure → `path: "fallback"` + `fallback_reason`  
5. Tool calls still enforce Phase 3 RBAC + audit  

---

## 2. Architecture

Shared in-process tool runner; no Agent → HTTP callback to `/tools/*` in this phase.

| Package | Responsibility |
|---|---|
| `app/bedrock/runner.py` | RBAC → resolve → audit |
| `app/bedrock/agent.py` | `invoke_agent` + return-control loop |
| `app/bedrock/fallback.py` | Converse tool-use loop |
| `app/bedrock/orchestrator.py` | Agent then fallback |
| `app/api/ask.py` | HTTP `POST /ask` |

---

## 3. API

`POST /ask` (auth required)

```json
{ "question": "What policies does customer John have?" }
```

```json
{
  "answer": "...",
  "path": "agent",
  "role": "agent",
  "tools_used": ["customer_policies"],
  "fallback_reason": null
}
```

---

## 4. Out of scope

- React chat UI  
- Bedrock Guardrails product (app guardrails remain)  
- Cognito / private networking  
- OpenAPI action-group HTTP callbacks (documented for later; return-control used now)  
