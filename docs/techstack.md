# Tech Stack — Enterprise AI Insurance Assistant

POC that answers insurance questions in natural language via a **semantic layer**, without giving the LLM raw SQL or database credentials.

---

## Architecture (high level)

```text
React (Vite)  →  FastAPI  →  Amazon Bedrock Agent
                    │                │
                    │         Action Group (tools)
                    ▼                ▼
              Semantic Layer  ←──────┘
                    │
                    ▼
         Amazon RDS (PostgreSQL)
```

---

## Stack by layer

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | **React 19** + **Vite 8** | Login, chat UI, role badge, logs panel |
| Frontend lint | **Oxlint** | Fast linting for the UI |
| Backend | **Python 3.11+** · **FastAPI** · **Uvicorn** | API, auth/RBAC, guardrails, semantic tools, logging |
| Package manager | **uv** | Python deps + lockfile (`pyproject.toml` / `uv.lock`) |
| Database | **Amazon RDS for PostgreSQL** | Cloud-hosted insurance sample data |
| DB driver | **psycopg 3** + **psycopg-pool** | Sync Postgres client from FastAPI |
| Config | **python-dotenv** | Local `.env` (`DATABASE_URL`, AWS/Bedrock vars) |
| AI orchestration | **Amazon Bedrock Agents** | NL understanding + tool/action selection |
| Foundation model | **Amazon Bedrock** (e.g. Claude / Nova) | Reasoning inside the Agent |
| Semantic layer | YAML/JSON concepts + Python resolver | Business terms → parameterized SQL |
| Auth (POC) | Demo users + roles (Cognito-compatible design) | Simulates enterprise SSO/RBAC |
| Cloud | **AWS** (RDS, Bedrock, IAM; optional CloudWatch) | Managed DB, models, observability |
| Testing | **pytest** · **httpx** | API / DB unit and smoke tests |
| Seed data | **Faker** (`db/generate_seed.py`) | Realistic demo data (200 rows/table) |
| Local DB tools | **psql** · **DBeaver** | Inspect / load schema and seed |

---

## Runtime versions (local)

| Component | Target |
|---|---|
| Python | ≥ 3.11 |
| Node.js | 20+ (for Vite frontend) |
| PostgreSQL | Amazon RDS (15/16) |

---

## Key dependencies

### Backend (`pyproject.toml`)

- `fastapi` — HTTP API
- `uvicorn[standard]` — ASGI server
- `python-dotenv` — env loading
- `psycopg[binary]` / `psycopg-pool` — Postgres
- Dev: `pytest`, `httpx`, `faker`

### Frontend (`frontend/package.json`)

- `react` / `react-dom`
- `vite` / `@vitejs/plugin-react`
- `oxlint`

---

## Data & infra (current)

| Item | Detail |
|---|---|
| Database name | `insurance` |
| Schema | `db/schema.sql` — customers, policies, coverages, claims |
| Seed | `db/seed.sql` (generated via `db/generate_seed.py`) |
| Setup notes | `infra/rds/notes.md` |
| Secrets | Local `.env` only (never commit) |

---

## Planned / not in live POC yet

| Item | Notes |
|---|---|
| Amazon Cognito | Real SSO; demo auth stands in for now |
| Bedrock Guardrails | Policy + content safety around Agent replies |
| Databricks / Snowflake | Future warehouses behind the same semantic API |
| CloudWatch | Optional request/audit metrics and logs |

---

## Why this stack (short)

- **React + Vite** — fast UI for a 2-day POC; clear split from API/Agent work  
- **FastAPI** — clean REST for the UI and Bedrock action groups  
- **Bedrock Agents** — orchestration without building a custom agent runtime  
- **Semantic layer** — business concepts map to approved SQL; model never gets DB credentials  
- **RDS PostgreSQL** — real managed DB for the demo (no local Docker DB)
