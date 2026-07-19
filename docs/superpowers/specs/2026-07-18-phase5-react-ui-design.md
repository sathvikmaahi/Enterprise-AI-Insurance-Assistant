# Phase 5 — React Chat UI Design

**Date:** 2026-07-18  
**Status:** Implemented (Approach 1 — auth-gated SPA)  
**Depends on:** Phase 4 Bedrock Ask  
**Does not include:** Cognito, design-system library, chat history persistence

---

## 1. Goal

Interview-polished Vite + React UI that demonstrates:

1. Full-screen demo login  
2. Natural-language ask via `POST /ask`  
3. Role badge + logout  
4. Always-visible audit logs  
5. Demo prompts, path/fallback meta, guardrail/RBAC errors  

**Success criteria:** Live demo can login as each role, ask questions, show deny/block moments, and point at the logs rail.

---

## 2. Architecture

Auth-gated SPA (no router). Session in `localStorage`. Three-zone shell after login.

| Piece | Responsibility |
|---|---|
| `LoginScreen` | Full-screen brand + credentials |
| `AppShell` | Header · Chat · LogsPanel |
| `api.js` | `login` / `ask` / `getLogs` + `ApiError` |
| `auth/session.js` | load / save / clear |

Backend unchanged (CORS already allows Vite).

---

## 3. Out of scope

- React Router / UI kits  
- Cognito  
- Persisted chat history  
- Bedrock Guardrails product UI  
---

## 4. Visual direction

“Claims desk”: mist ground, ink text, teal accent, Fraunces + Source Sans 3 + IBM Plex Mono. Role badge is the signature element.
