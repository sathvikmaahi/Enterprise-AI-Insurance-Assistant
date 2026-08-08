# Enterprise AI Insurance Assistant

**React · FastAPI · AWS Bedrock Agent · Semantic Layer · PostgreSQL**

A lightweight Proof of Concept (POC) that shows how AWS Bedrock can securely answer natural-language questions about insurance data — without giving the model raw SQL access to the database.

---

## 1. Problem Statement

Insurance employees often need answers like:

- What policy does customer John have?
- Show all open claims.
- Which policy covers windshield damage?
- What is the premium amount for policy P1001?

Today those questions usually require:

- SQL knowledge
- Familiarity with internal schemas
- Access across multiple systems

**Business pain:** slow answers, inconsistent definitions (“open claim” means different things to different teams), and security risk when people run ad-hoc SQL.

**POC goal:** provide a natural-language assistant that:

1. Authenticates the user and applies **role-based access**
2. Uses an **AWS Bedrock Agent** to orchestrate the request
3. Translates business language through a **semantic layer** into safe SQL
4. Queries a sample **PostgreSQL** insurance database
5. Enforces **guardrails** and writes **audit logs**

This is intentionally scoped to **one database** and a **small set of insurance concepts**. Databricks / Snowflake are shown as **future** warehouse targets behind the same semantic layer — not part of the live POC.

---

## 2. What This POC Demonstrates

| Capability | How it shows up in the demo |
|---|---|
| Natural language understanding | User asks business questions in plain English |
| Bedrock Agent orchestration | Agent decides which tools/actions to call |
| Semantic mapping | Business terms → approved SQL (not free-form SQL from the LLM) |
| Ontology / relationships | Customer → Policy → Coverage → Claim |
| Secure database access | Single app DB credential; model never gets a DB password |
| Identity & RBAC | App propagates `{username, role}`; concept allow/deny (not DB user impersonation) |
| Guardrails | Blocks destructive, out-of-scope, or over-broad asks |
| Logging & observability | Every request: user, role, question, SQL, allow/deny, latency |

---

## 3. Solution Overview

```text
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  React UI   │────▶│  FastAPI Backend     │────▶│  Amazon Bedrock     │
│  (Vite)     │     │  Auth · App guardrails│    │  Agent (+ optional  │
│             │     │  · RBAC · Logs       │     │   Bedrock Guardrails)│
└─────────────┘     └──────────┬───────────┘     └──────────┬──────────┘
                               │                            │
                               │              Action group (return control
                               │              or Lambda — not localhost HTTP)
                               │                            │
                               ▼                            ▼
                    ┌──────────────────────┐     ┌─────────────────────┐
                    │  Semantic Layer      │◀────│  FastAPI runs tools │
                    │  Concepts → SQL      │     │  in-process (POC)   │
                    └──────────┬───────────┘     └─────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Amazon RDS          │
                    │  PostgreSQL (sample) │
                    └──────────────────────┘

Future (Phase 2):
  Semantic Layer ──▶ Databricks SQL Warehouse
                 ──▶ Snowflake (optional)
```

A managed Bedrock Agent **cannot** call your laptop’s FastAPI URLs. This POC uses **return control**: the Agent requests a tool; FastAPI executes it locally and sends the result back. Production alternatives are **Lambda** (or another publicly reachable executor) wired to the action group — not direct HTTP to `localhost`.

### Request lifecycle (demo narrative)

1. User signs in (demo auth simulating Cognito roles) → FastAPI issues a session with `{username, role}`.
2. User asks a natural-language question.
3. FastAPI checks auth, basic guardrails, and forwards to the **Bedrock Agent**, attaching that **application identity context** (e.g. session attributes) — not a per-user Postgres login.
4. Agent selects a tool (e.g. lookup policy, list open claims) and **returns control** to FastAPI (or would invoke **Lambda** in a hosted setup).
5. FastAPI enforces **concept-level RBAC** from the propagated role, then the **semantic layer** builds **parameterized SQL**.
6. Queries run with the **shared application DB credential** (connection pool). This is **not** database-level user impersonation (`SET ROLE` / per-user DB roles / RLS-as-that-user).
7. PostgreSQL returns data; FastAPI resumes the Agent session with tool results and formats a business-friendly answer.
8. Request is logged for audit (`who` = app username/role, plus concept/SQL/decision).

---

## 4. Tech Stack

| Layer | Technology | Role in POC |
|---|---|---|
| Frontend | **React (Vite)** | Login, chat UI, logs panel |
| Backend | **Python · FastAPI** (managed with **uv**) | Auth, RBAC, guardrails, semantic tools, logging |
| AI orchestration | **Amazon Bedrock Agents** | NL understanding + tool/action orchestration |
| Foundation model | Amazon Bedrock (e.g. Claude / Nova) | Reasoning inside the Agent |
| Semantic layer | YAML/JSON concept definitions + Python resolver | Business terms → validated SQL |
| Database | **Amazon RDS for PostgreSQL** (cloud-hosted) | Sample insurance data — no local Docker DB |
| Cloud | **AWS** (Bedrock, RDS, IAM; optional CloudWatch) | Model access, managed DB, observability |
| Auth (POC) | Demo users + roles (Cognito-compatible design) | Application identity context for RBAC/audit (not DB impersonation) |
| Future warehouse | Databricks connector (stub / roadmap) | Same semantic API, different backend |

### Why React (Vite)

- Clean separation: UI owns presentation; FastAPI owns API / Agent / semantic / DB
- Easy to show login, chat, RBAC role badge, and audit-log panel in the demo
- Vite keeps setup fast for a 2-day POC (no heavy UI framework)
- Strong interview signal: full-stack (React + FastAPI + AWS)

**POC UI scope (keep small):** login screen, chat thread, role indicator, recent logs panel. No design-system sprawl.

### Why FastAPI

- Clean REST for the React app; semantic tools run in-process under Bedrock **return control**
- Fast to build for a 2-day POC
- Easy to show RBAC middleware, logging, and tool APIs clearly in an interview
- CORS-enabled API that React calls during local dev (`localhost:5173` → `localhost:8000`)

### Why Bedrock Agent (not raw model-only)

- Matches enterprise “agent + tools” storytelling
- Separates orchestration (Agent) from data access (your semantic tools)
- Action groups use **return control** (this POC) or **Lambda**; not direct calls to local FastAPI

### Why a semantic layer (critical)

The LLM must **not** invent arbitrary SQL against production-like schemas.

The semantic layer owns:

- Approved business concepts (`open_claim`, `policy_premium`, `windshield_coverage`, …)
- Join paths and filters
- Parameter binding
- Which concepts each **app role** may call (`allowed_roles` in YAML)

Bedrock asks for **concepts**; the semantic layer returns **safe SQL results**. Role checks happen in the API/tool runner using propagated app identity — not by switching the database user.

### Why Amazon RDS (not local Docker)

- Avoids heavy local Docker usage that can hang / slow down a Mac
- Fits the enterprise AWS story for the manager demo
- Same SQL / semantic layer code as a local Postgres — only the connection string changes
- POC sizing: single instance (e.g. `db.t4g.micro` or Free Tier if eligible), publicly accessible **only for the demo** with a strong password + security group limited to your IP

**Not using Docker for the database in this POC.** App runs locally (React + FastAPI); data lives in RDS.

---

## 5. Mitigating Bedrock Agent Risks (POC Reliability)

Managed Bedrock Agents can be slow to configure and brittle in live demos. This project addresses that explicitly:

| Risk | Mitigation |
|---|---|
| Agent/action-group misconfiguration | Keep action contracts tiny (3–5 tools max); document return-control function schemas (or Lambda/OpenAPI if hosted) |
| Hard to debug mid-demo | Structured logs on every tool call; `/health` and `/tools/ping` endpoints |
| Live Agent failure | **Fallback path**: FastAPI can call the same semantic tools via Bedrock Converse + tool use if Agent invoke fails |
| Agent invents unsafe SQL | Agent **never** receives DB credentials; only named semantic tools (return control / Lambda); SQL only in the semantic layer |
| Time pressure | Seed data + fixed demo script; rehearse the 5 questions before presentation |

**Design rule:** Semantic layer is the source of truth. The Agent is the orchestrator, not the database engineer.

---

## 6. Domain Model (Insurance Sample)

Minimal ontology for the POC:

```text
Customer 1──* Policy 1──* Coverage
                │
                └──* Claim
```

Suggested entities:

| Entity | Example fields |
|---|---|
| Customer | customer_id, full_name, email, region |
| Policy | policy_id, customer_id, product_type, status, premium_amount, start_date, end_date |
| Coverage | coverage_id, policy_id, coverage_type, limit_amount, deductible |
| Claim | claim_id, policy_id, status, description, amount, filed_date, **claim_details (JSONB)** |

Example demo IDs (illustrative):

- Customer: John Smith  
- Policy: `P1001`  
- Coverage types: auto liability, collision, comprehensive, windshield  
- Claim statuses: `OPEN`, `CLOSED`, `IN_REVIEW`

---

## 7. Semantic Layer Concepts (Examples)

| Business concept | Meaning | Maps to |
|---|---|---|
| `customer_policies` | Policies owned by a named customer | `customers` ⋈ `policies` |
| `policy_premium` | Premium for a policy ID | `policies.premium_amount` |
| `open_claims` | Claims with status OPEN | `claims` where `status = 'OPEN'` |
| `coverage_by_type` | Policies that include a coverage type (e.g. windshield) | `policies` ⋈ `coverages` |
| `claim_summary` | Claim details for a policy/customer | `claims` ⋈ `policies` |
| `claims_by_damage_type` | Claims filtered by JSON field | `claim_details->>'damage_type'` |

Each concept definition includes:

- Name + description (for Agent instructions)
- Required parameters
- SQL template (parameterized)
- Allowed roles
- Response shape for the UI/Agent

---

## 8. Identity & RBAC (Demo Roles)

**How identity works in this POC:** login produces an application session (`username` + `role`). That context is **propagated** through `/ask`, tool execution, Bedrock session attributes, and audit logs. Postgres is accessed with one service `DATABASE_URL` user.

**What this is not:** full database-level user impersonation (no per-employee DB accounts, no `SET ROLE` / `SET SESSION AUTHORIZATION`, no Postgres RLS keyed to the end user).

| Role (display) | Role id | Can do | Cannot do |
|---|---|---|---|
| **Customer Service Representative** | `csr` | Policies, premiums, coverages | Claim concepts reserved for adjuster/manager |
| **Adjuster** | `adjuster` | Claim concepts + related policy lookups | Concepts outside `allowed_roles` |
| **Manager** | `manager` | Broader read concepts (policies/claims summaries) | Destructive operations (none allowed for any role) |

Demo login: `csr` / `csr123` (role id `csr`). Unauthorized concept calls return **Access denied**. Enforcement is **concept-level** (`allowed_roles` in YAML) before SQL runs.

---

## 9. Two control layers (do not conflate)

These are **different** layers. Bedrock Guardrails are **not** responsible for SQL validation or database permissions.

### Bedrock Guardrails (optional / planned association with the Agent)

Use Amazon Bedrock Guardrails for model I/O safety:

- Harmful content  
- Denied topics  
- Sensitive-information detection  
- Input and output filtering  

Bedrock Guardrails can be associated with agents and can evaluate user inputs and model responses. They do **not** validate SQL execution or enforce DB permissions.

### Application guardrails & controls (this POC — Python / FastAPI)

Use application code for data-path and tool safety:

| Control | Where it lives (conceptually) |
|---|---|
| Role authorization | `app/rbac` + concept `allowed_roles` |
| Tool allowlists | Semantic concepts only (YAML catalog) |
| Parameter validation | Semantic layer (`params` / `require_one_of`) |
| Maximum returned records | Application / query policy (keep LIMIT in SQL templates as needed) |
| Read-only query enforcement | Semantic templates are SELECT-only; no write tools |
| Direct SQL rejection | `app/guardrails` (blocks raw SQL / destructive phrasing) |
| Maximum tool calls | Bedrock return-control / Converse loops (`MAX_*` rounds) |
| Timeout handling | HTTP / client / AWS SDK timeouts around invoke |

Demo question checks in `app/guardrails` also block over-broad PII dumps and off-domain asks before the Agent runs.

---

## 10. Project Structure

```text
Semantic-layer/
├── README.md
├── .env.example
├── pyproject.toml / uv.lock
├── docs/
│   ├── README.md                   # doc index
│   ├── techstack.md
│   ├── features/                   # phase feature notes (01–06)
│   └── superpowers/specs/          # design specs
├── frontend/                       # React (Vite) UI
│   ├── src/
│   │   ├── App.jsx                 # auth gate
│   │   ├── api.js
│   │   ├── auth/session.js
│   │   └── components/             # Login, Chat, LogsPanel, …
│   └── README.md
├── app/                            # FastAPI backend
│   ├── main.py
│   ├── api/                        # /auth, /ask, /tools, /logs
│   ├── auth/ · rbac/ · guardrails/
│   ├── bedrock/                    # Agent + Converse fallback
│   ├── semantic/                   # concepts YAML + SQL resolver
│   ├── db/ · logging/
├── db/                             # schema.sql · seed.sql
├── infra/
│   ├── rds/notes.md
│   └── bedrock/notes.md
└── tests/
```

---

## 11. API Surface (Planned)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Demo login; returns session/token + role |
| `POST` | `/ask` | Send NL question; invokes Bedrock Agent (return control) + Converse fallback |
| `GET` | `/logs` | Recent audit entries for demo panel |
| `GET` | `/health` | App + DB health |
| `POST` | `/tools/*` | Same semantic tools for demos/tests; **not** called by the managed Agent over HTTP |
| `GET` | `/tools/ping` | Tool connectivity check |

Exact tool names match semantic concepts (e.g. `/tools/customer_policies`). The Bedrock Agent action group uses **return control** (or **Lambda** if you host an executor); it does not HTTP-call these local paths.

---

## 12. Demo Script (Tuesday)

1. **Architecture slide** — Auth → Bedrock Agent → Semantic Layer → Postgres; Databricks as Phase 2.  
2. Login as **Customer Service Representative** (`csr`) → “What policy does customer John have?” → answer.  
3. Login as CSR → ask open claims → **Access denied**; switch to adjuster → allowed.  
4. Ask “Delete all customers” → **blocked by guardrail**.  
5. “Show all open claims.” → semantic concept → SQL → answer.  
6. Open **logs** panel → show user, role, concept, SQL, latency.  
7. Close with roadmap: Cognito, private networking, Databricks connector, CloudWatch dashboards.

---

## 13. Out of Scope (This POC)

- Live Databricks / Snowflake querying  
- Full Cognito + API Gateway production hardening  
- Multi-region HA, complex CI/CD  
- Training custom models  
- Writing data (insert/update/delete) via the assistant  

These can be called out as **next steps** in the presentation.

---

## 14. Success Criteria

The POC is successful if, in a live demo, you can:

- [ ] Answer at least 4 natural-language insurance questions correctly  
- [ ] Show RBAC deny behavior  
- [ ] Show a guardrail block  
- [ ] Show an audit log for a request  
- [ ] Explain why the semantic layer prevents unsafe SQL  
- [ ] Point to Databricks as the next warehouse behind the same layer  

---

## 15. Prerequisites

- Python 3.11+  
- **[uv](https://docs.astral.sh/uv/)** (Python package/runner — use instead of pip/venv)  
- Node.js 20+ (for React / Vite)  
- AWS account with **Bedrock** + ability to create **RDS PostgreSQL**  
- AWS credentials configured locally (`aws sts get-caller-identity`)  
- Bedrock invoke verified (e.g. Converse / Agent runtime)  
- `psql` client locally (or use RDS Query Editor) — **no Docker required**

Install uv (if needed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 16. Quick Start (After Implementation)

```bash
# 1) Create RDS PostgreSQL in AWS Console (one-time)
#    - Engine: PostgreSQL
#    - Template: Free tier (if eligible) or burstable micro
#    - Public access: Yes (demo only)
#    - Security group: allow port 5432 from YOUR IP only
#    - Copy endpoint → build DATABASE_URL

# 2) Backend deps (uv creates .venv + installs from pyproject.toml / uv.lock)
uv sync

# 3) Configure env
cp .env.example .env
# set DATABASE_URL=postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/insurance
# set AWS_REGION, BEDROCK_AGENT_ID, BEDROCK_AGENT_ALIAS_ID,
# VITE_API_BASE_URL=http://localhost:8000, etc.

# 4) Load schema + seed into RDS
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed.sql

# 5) Run FastAPI backend (local — talks to RDS in AWS)
uv run uvicorn app.main:app --reload --port 8000

# 6) Run React frontend (separate terminal)
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

> Commands will be finalized when the code lands. This section is the intended operator path.
>
> **Package manager:** backend uses **uv only** (`uv sync`, `uv add`, `uv run`) — not pip.

### RDS security checklist (demo)

- Strong master password (store only in `.env`, never commit)
- Security group: inbound `5432` from your current public IP only
- Delete or stop the RDS instance after the interview if you do not need it
- Do not leave `0.0.0.0/0` open longer than necessary

---

## 17. Configuration (Expected)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `AWS_REGION` | e.g. `us-east-1` |
| `BEDROCK_AGENT_ID` | Bedrock Agent ID |
| `BEDROCK_AGENT_ALIAS_ID` | Agent alias used for invoke |
| `BEDROCK_FALLBACK_MODEL_ID` | Model for Converse fallback path |
| `LOG_LEVEL` | `INFO` / `DEBUG` |
| `DEMO_AUTH_SECRET` | Signing secret for demo sessions |
| `VITE_API_BASE_URL` | React → FastAPI base URL (e.g. `http://localhost:8000`) |

Never commit real secrets. Use `.env` (gitignored).

---

## 18. Security Notes

- Bedrock / the Agent never receives database credentials.  
- Only parameterized SQL from the semantic layer is executed.  
- Identity is **application-context propagation** (`username` / `role` on the request and into tool/Agent paths); the DB connection stays the app service user.  
- RBAC is **concept-level** allow/deny in the API/tool runner before `resolve()` — not DB user impersonation.  
- Guardrails block unsafe intents.  
- Audit logs support “who asked what, and what ran” using that app identity.  

---

## 19. Roadmap

| Phase | Focus |
|---|---|
| **Phase 1 (this POC)** | React + FastAPI + Bedrock Agent + semantic layer + RDS Postgres + RBAC + logs |
| **Phase 2** | Databricks connector behind the same semantic interface |
| **Phase 3** | Cognito, private networking (no public RDS), CloudWatch dashboards, stronger Guardrails |

---

## 20. Presentation Talking Points

- “Employees ask business questions; they don’t write SQL.”  
- “Bedrock Agent orchestrates via return control (or Lambda); the semantic layer governs meaning and SQL.”  
- “Same pattern scales to Databricks later without rewriting the assistant.”  
- “Security is layered: app identity context → guardrails → concept RBAC → parameterized queries → audit logs (not DB user impersonation).”  

---

## License / Status

**Status:** POC / interview demo  
**Audience:** Hiring manager / architecture walkthrough  
**Not production-ready** — intentionally scoped for clarity and reliability.
