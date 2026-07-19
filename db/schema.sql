-- Insurance sample schema for the Enterprise AI Insurance Assistant POC.
-- Safe to re-run: drops existing demo objects first (POC only — not for production).

BEGIN;

DROP TABLE IF EXISTS claims CASCADE;
DROP TABLE IF EXISTS coverages CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id   TEXT PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL,
    region        TEXT NOT NULL
);

CREATE TABLE policies (
    policy_id       TEXT PRIMARY KEY,
    customer_id     TEXT NOT NULL REFERENCES customers (customer_id),
    product_type    TEXT NOT NULL,
    status          TEXT NOT NULL,
    premium_amount  NUMERIC(12, 2) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL
);

CREATE TABLE coverages (
    coverage_id    TEXT PRIMARY KEY,
    policy_id      TEXT NOT NULL REFERENCES policies (policy_id),
    coverage_type  TEXT NOT NULL,
    limit_amount   NUMERIC(12, 2) NOT NULL,
    deductible     NUMERIC(12, 2) NOT NULL
);

CREATE TABLE claims (
    claim_id     TEXT PRIMARY KEY,
    policy_id    TEXT NOT NULL REFERENCES policies (policy_id),
    status       TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSED', 'IN_REVIEW')),
    description  TEXT NOT NULL,
    amount       NUMERIC(12, 2) NOT NULL,
    filed_date   DATE NOT NULL
);

CREATE INDEX idx_policies_customer_id ON policies (customer_id);
CREATE INDEX idx_coverages_policy_id ON coverages (policy_id);
CREATE INDEX idx_coverages_coverage_type ON coverages (coverage_type);
CREATE INDEX idx_claims_policy_id ON claims (policy_id);
CREATE INDEX idx_claims_status ON claims (status);

COMMIT;
