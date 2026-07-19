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
| Secure database access | App/DB credentials; model never gets a DB password |
| RBAC | Agent / Adjuster / Manager see different data |
| Guardrails | Blocks destructive, out-of-scope, or over-broad asks |
| Logging & observability | Every request: user, role, question, SQL, allow/deny, latency |

---

## 3. Solution Overview

```text
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  React UI   │────▶│  FastAPI Backend     │────▶│  Amazon Bedrock     │
│  (Vite)     │     │  Auth · RBAC · Logs  │     │  Agent + Guardrails │
└─────────────┘     └──────────┬───────────┘     └──────────┬──────────┘
                               │                            │
                               │                   Action Group (tools)
                               │                            │
                               ▼                            ▼
                    ┌──────────────────────┐     ┌─────────────────────┐
                    │  Semantic Layer      │◀────│  Agent invokes API  │
                    │  Concepts → SQL      │     │  /tools/* endpoints │
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

### Request lifecycle (demo narrative)

1. User signs in (demo auth simulating Cognito roles).
2. User asks a natural-language question.
3. FastAPI checks auth, basic guardrails, and forwards to the **Bedrock Agent**.
4. Agent selects an action (e.g. lookup policy, list open claims).
5. FastAPI **semantic layer** resolves the business concept and builds **parameterized SQL**.
6. RBAC filters rows/columns the role is allowed to see.
7. PostgreSQL returns data; Agent/API formats a business-friendly answer.
8. Request is logged for audit and demo observability.

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
| Auth (POC) | Demo users + roles (Cognito-compatible design) | Simulates enterprise SSO/RBAC |
| Future warehouse | Databricks connector (stub / roadmap) | Same semantic API, different backend |

### Why React (Vite)

- Clean separation: UI owns presentation; FastAPI owns API / Agent / semantic / DB
- Easy to show login, chat, RBAC role badge, and audit-log panel in the demo
- Vite keeps setup fast for a 2-day POC (no heavy UI framework)
- Strong interview signal: full-stack (React + FastAPI + AWS)

**POC UI scope (keep small):** login screen, chat thread, role indicator, recent logs panel. No design-system sprawl.

### Why FastAPI

- Clean REST endpoints for the React app and Bedrock Agent action groups
- Fast to build for a 2-day POC
- Easy to show RBAC middleware, logging, and tool APIs clearly in an interview
- CORS-enabled API that React calls during local dev (`localhost:5173` → `localhost:8000`)

### Why Bedrock Agent (not raw model-only)

- Matches enterprise “agent + tools” storytelling
- Separates orchestration (Agent) from data access (your APIs)
- Supports attaching guardrails and action groups managers recognize from AWS docs

### Why a semantic layer (critical)

The LLM must **not** invent arbitrary SQL against production-like schemas.

The semantic layer owns:

- Approved business concepts (`open_claim`, `policy_premium`, `windshield_coverage`, …)
- Join paths and filters
- Parameter binding
- Role-aware field visibility

Bedrock asks for **concepts**; the semantic layer returns **safe SQL results**.

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
| Agent/action-group misconfiguration | Keep action contracts tiny (3–5 tools max); document each OpenAPI schema |
| Hard to debug mid-demo | Structured logs on every tool call; `/health` and `/tools/ping` endpoints |
| Live Agent failure | **Fallback path**: FastAPI can call the same semantic tools via Bedrock Converse + tool use if Agent invoke fails |
| Agent invents unsafe SQL | Agent **never** receives DB credentials; only semantic tool endpoints; SQL only generated in semantic layer |
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
| Claim | claim_id, policy_id, status, description, amount, filed_date |

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

Each concept definition includes:

- Name + description (for Agent instructions)
- Required parameters
- SQL template (parameterized)
- Allowed roles
- Response shape for the UI/Agent

---

## 8. RBAC (Demo Roles)

| Role | Can do | Cannot do |
|---|---|---|
| **Agent** | Lookup assigned/sample customers, policies, premiums, coverages | Broad “all customers” dumps; other regions if scoped |
| **Adjuster** | Open/in-review claims + related policy context | Customer PII beyond what claim handling needs |
| **Manager** | Cross-customer read of policies/claims summaries | Destructive operations (none allowed for any role) |

Unauthorized asks return a clear **Access denied** message (good live demo moment).

---

## 9. Guardrails (Basic)

Examples enforced in app and/or Bedrock Guardrails:

- **Allow:** policy lookup, premiums, open claims, coverage questions  
- **Deny:** `DELETE` / `UPDATE` / schema changes  
- **Deny:** “show all customers with SSN/email dump” style over-broad PII asks  
- **Deny:** off-domain questions (stocks, medical advice, etc.)  
- **Deny:** direct raw SQL from the user

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
| `POST` | `/ask` | Send NL question; invokes Bedrock Agent |
| `GET` | `/logs` | Recent audit entries for demo panel |
| `GET` | `/health` | App + DB health |
| `POST` | `/tools/*` | Action-group endpoints called by Bedrock Agent |
| `GET` | `/tools/ping` | Agent connectivity check |

Exact tool names will match semantic concepts (e.g. `/tools/customer_policies`).

---

## 12. Demo Script (Tuesday)

1. **Architecture slide** — Auth → Bedrock Agent → Semantic Layer → Postgres; Databricks as Phase 2.  
2. Login as **Agent** → “What policy does customer John have?” → answer.  
3. Login as restricted role → same/broad question → **Access denied**.  
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






---