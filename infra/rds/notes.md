# Amazon RDS PostgreSQL — POC setup checklist

One-time console setup for the Enterprise AI Insurance Assistant demo.
**Not using Docker for the database.** App runs locally; data lives in RDS.

## 1. Create the instance (AWS Console)

1. Open **RDS → Databases → Create database**.
2. **Engine:** PostgreSQL (recent 15/16 is fine).
3. **Templates:** Free tier (if eligible) or **Dev/Test**.
4. **Instance:** `db.t4g.micro` (or Free Tier equivalent).
5. **Credentials:** set a strong master username/password (store only in local `.env`).
6. **Storage:** default gp2/gp3 is enough for the POC.
7. **Connectivity:**
   - **Public access:** Yes (demo only).
   - **VPC security group:** create/select one that will allow your IP.
8. Create the database. Wait until status is **Available**.
9. Copy the **Endpoint** (hostname) from the Connectivity panel.

## 2. Security group (required)

Inbound rule:

| Type       | Port | Source                          |
|------------|------|---------------------------------|
| PostgreSQL | 5432 | *Your current public IP* `/32`  |

- Do **not** leave `0.0.0.0/0` open longer than necessary.
- If your home/office IP changes, update the SG rule.

## 3. Create the `insurance` database

RDS creates a default DB named like the master user. Create the app DB:

```bash
# Connect to the default DB first (often "postgres")
psql "postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/postgres" -c 'CREATE DATABASE insurance;'
```

If the password has special characters (`@`, `#`, `/`, etc.), **URL-encode** them in the connection string (e.g. `@` → `%40`).

## 4. Local `.env`

```bash
cp .env.example .env
```

Set:

```bash
DATABASE_URL=postgresql://USER:PASSWORD@RDS_ENDPOINT:5432/insurance
```

Never commit `.env`.

## 5. Load schema + seed

From the repo root:

```bash
psql "$DATABASE_URL" -f db/schema.sql
psql "$DATABASE_URL" -f db/seed.sql
```

Quick verify:

```bash
psql "$DATABASE_URL" -c "SELECT customer_id, full_name FROM customers WHERE full_name ILIKE '%John%';"
psql "$DATABASE_URL" -c "SELECT policy_id, premium_amount FROM policies WHERE policy_id = 'P1001';"
psql "$DATABASE_URL" -c "SELECT coverage_type FROM coverages WHERE policy_id = 'P1001';"
psql "$DATABASE_URL" -c "SELECT claim_id, status FROM claims WHERE status = 'OPEN';"
```

Expected: John Smith / `C001`, policy `P1001`, a `windshield` coverage, and at least one `OPEN` claim.

## 6. App health check

```bash
uv run uvicorn app.main:app --reload --port 8000
curl -s http://localhost:8000/health
# {"status":"ok","db":"ok"}
```

If `"db":"error"`, check `DATABASE_URL`, security group IP, and that schema/seed loaded.

## 7. Tear down after the interview

- Stop or **delete** the RDS instance if you no longer need it.
- Remove the public `5432` rule (or the whole SG) when done.
- Rotate/discard the demo password.

## Security reminders (demo)

- Strong master password; only in `.env`
- SG: inbound `5432` from your IP only
- Bedrock / the Agent never receive `DATABASE_URL`
- No writes via the assistant in this POC (read-only demo path)
