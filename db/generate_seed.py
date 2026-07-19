#!/usr/bin/env python3
"""Generate db/seed.sql with demo rows + Faker data (200 rows per table)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from faker import Faker

ROWS = 200
SEED = 42
OUT = Path(__file__).with_name("seed.sql")

REGIONS = ("EAST", "WEST", "CENTRAL", "SOUTH")
PRODUCT_TYPES = ("auto", "home", "renters", "umbrella")
POLICY_STATUSES = ("ACTIVE", "ACTIVE", "ACTIVE", "LAPSED", "CANCELLED")
AUTO_COVERAGES = (
    ("auto_liability", 100_000, 500),
    ("collision", 50_000, 1_000),
    ("comprehensive", 50_000, 500),
    ("windshield", 1_500, 0),
    ("uninsured_motorist", 25_000, 250),
)
HOME_COVERAGES = (
    ("dwelling", 350_000, 2_500),
    ("personal_property", 75_000, 1_000),
    ("liability", 300_000, 500),
    ("loss_of_use", 30_000, 0),
)
CLAIM_STATUSES = ("OPEN", "CLOSED", "IN_REVIEW")
CLAIM_TEMPLATES = (
    "Windshield crack after highway debris",
    "Minor bumper scratch repaired",
    "Roof leak after storm",
    "Side mirror damage in parking lot",
    "Hail damage to vehicle body panels",
    "Water damage from burst pipe",
    "Theft of personal property from vehicle",
    "Rear-end collision at intersection",
    "Fallen tree damaged roof section",
    "Glass breakage from rock chip",
)

fake = Faker()
Faker.seed(SEED)
fake.seed_instance(SEED)


def sql_str(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql_date(value: date) -> str:
    return sql_str(value.isoformat())


def sql_money(value: float) -> str:
    return f"{value:.2f}"


def demo_customers() -> list[tuple]:
    return [
        ("C001", "John Smith", "john.smith@example.com", "EAST"),
        ("C002", "Maria Garcia", "maria.garcia@example.com", "WEST"),
        ("C003", "Alex Chen", "alex.chen@example.com", "EAST"),
    ]


def demo_policies() -> list[tuple]:
    return [
        ("P1001", "C001", "auto", "ACTIVE", 1280.00, date(2025, 1, 1), date(2026, 1, 1)),
        ("P1002", "C002", "home", "ACTIVE", 2100.50, date(2025, 3, 15), date(2026, 3, 15)),
        ("P1003", "C003", "auto", "ACTIVE", 980.00, date(2025, 6, 1), date(2026, 6, 1)),
    ]


def demo_coverages() -> list[tuple]:
    return [
        ("COV-LIAB-1", "P1001", "auto_liability", 100000.00, 500.00),
        ("COV-COLL-1", "P1001", "collision", 50000.00, 1000.00),
        ("COV-COMP-1", "P1001", "comprehensive", 50000.00, 500.00),
        ("COV-WIND-1", "P1001", "windshield", 1500.00, 0.00),
        ("COV-DWELL-2", "P1002", "dwelling", 350000.00, 2500.00),
        ("COV-LIAB-3", "P1003", "auto_liability", 100000.00, 500.00),
    ]


def demo_claims() -> list[tuple]:
    return [
        (
            "CLM-001",
            "P1001",
            "OPEN",
            "Windshield crack after highway debris",
            420.00,
            date(2026, 5, 10),
        ),
        (
            "CLM-002",
            "P1001",
            "CLOSED",
            "Minor bumper scratch repaired",
            650.00,
            date(2025, 11, 2),
        ),
        (
            "CLM-003",
            "P1002",
            "IN_REVIEW",
            "Roof leak after storm",
            4800.00,
            date(2026, 6, 20),
        ),
        (
            "CLM-004",
            "P1003",
            "OPEN",
            "Side mirror damage in parking lot",
            310.00,
            date(2026, 7, 1),
        ),
    ]


def gen_customers(n: int) -> list[tuple]:
    rows = list(demo_customers())
    used_emails = {r[2] for r in rows}
    i = 4
    while len(rows) < n:
        name = fake.name()
        email = fake.unique.email()
        if email in used_emails:
            continue
        used_emails.add(email)
        rows.append((f"C{i:03d}", name, email, fake.random_element(REGIONS)))
        i += 1
    return rows


def gen_policies(n: int, customer_ids: list[str]) -> list[tuple]:
    rows = list(demo_policies())
    i = 1004
    while len(rows) < n:
        start = fake.date_between(start_date=date(2023, 1, 1), end_date=date(2026, 6, 1))
        end = start + timedelta(days=365)
        premium = round(fake.pyfloat(min_value=450, max_value=4500, right_digits=2), 2)
        rows.append(
            (
                f"P{i}",
                fake.random_element(customer_ids),
                fake.random_element(PRODUCT_TYPES),
                fake.random_element(POLICY_STATUSES),
                premium,
                start,
                end,
            )
        )
        i += 1
    return rows


def gen_coverages(n: int, policies: list[tuple]) -> list[tuple]:
    rows = list(demo_coverages())
    policy_by_id = {p[0]: p for p in policies}
    i = 1
    while len(rows) < n:
        policy_id = fake.random_element([p[0] for p in policies])
        product = policy_by_id[policy_id][2]
        catalog = AUTO_COVERAGES if product in {"auto", "umbrella"} else HOME_COVERAGES
        cov_type, limit_base, ded_base = fake.random_element(catalog)
        limit_amount = round(limit_base * fake.pyfloat(min_value=0.8, max_value=1.4, right_digits=2), 2)
        deductible = round(ded_base * fake.pyfloat(min_value=0.5, max_value=1.5, right_digits=2), 2)
        rows.append(
            (
                f"COV-{i:04d}",
                policy_id,
                cov_type,
                limit_amount,
                deductible,
            )
        )
        i += 1
    return rows


def gen_claims(n: int, policy_ids: list[str]) -> list[tuple]:
    rows = list(demo_claims())
    i = 5
    while len(rows) < n:
        filed = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2026, 7, 15))
        amount = round(fake.pyfloat(min_value=150, max_value=12000, right_digits=2), 2)
        rows.append(
            (
                f"CLM-{i:03d}",
                fake.random_element(policy_ids),
                fake.random_element(CLAIM_STATUSES),
                fake.random_element(CLAIM_TEMPLATES),
                amount,
                filed,
            )
        )
        i += 1
    return rows


def format_customers(rows: list[tuple]) -> str:
    values = ",\n".join(
        f"    ({sql_str(cid)}, {sql_str(name)}, {sql_str(email)}, {sql_str(region)})"
        for cid, name, email, region in rows
    )
    return (
        "INSERT INTO customers (customer_id, full_name, email, region) VALUES\n"
        f"{values};\n"
    )


def format_policies(rows: list[tuple]) -> str:
    values = ",\n".join(
        "    ({}, {}, {}, {}, {}, {}, {})".format(
            sql_str(pid),
            sql_str(cid),
            sql_str(product),
            sql_str(status),
            sql_money(premium),
            sql_date(start),
            sql_date(end),
        )
        for pid, cid, product, status, premium, start, end in rows
    )
    return (
        "INSERT INTO policies (\n"
        "    policy_id, customer_id, product_type, status, premium_amount, start_date, end_date\n"
        f") VALUES\n{values};\n"
    )


def format_coverages(rows: list[tuple]) -> str:
    values = ",\n".join(
        "    ({}, {}, {}, {}, {})".format(
            sql_str(cid),
            sql_str(pid),
            sql_str(ctype),
            sql_money(limit_amount),
            sql_money(deductible),
        )
        for cid, pid, ctype, limit_amount, deductible in rows
    )
    return (
        "INSERT INTO coverages (\n"
        "    coverage_id, policy_id, coverage_type, limit_amount, deductible\n"
        f") VALUES\n{values};\n"
    )


def format_claims(rows: list[tuple]) -> str:
    values = ",\n".join(
        "    ({}, {}, {}, {}, {}, {})".format(
            sql_str(cid),
            sql_str(pid),
            sql_str(status),
            sql_str(desc),
            sql_money(amount),
            sql_date(filed),
        )
        for cid, pid, status, desc, amount, filed in rows
    )
    return (
        "INSERT INTO claims (\n"
        "    claim_id, policy_id, status, description, amount, filed_date\n"
        f") VALUES\n{values};\n"
    )


def main() -> None:
    customers = gen_customers(ROWS)
    customer_ids = [c[0] for c in customers]
    policies = gen_policies(ROWS, customer_ids)
    policy_ids = [p[0] for p in policies]
    coverages = gen_coverages(ROWS, policies)
    claims = gen_claims(ROWS, policy_ids)

    body = "\n".join(
        [
            "-- Demo seed data for the insurance POC.",
            "-- Stable demo IDs (C001/P1001/...) plus Faker-generated rows.",
            "-- Regenerate with: uv run python db/generate_seed.py",
            "-- Re-run after schema.sql (schema drops tables).",
            "",
            "BEGIN;",
            "",
            format_customers(customers),
            format_policies(policies),
            format_coverages(coverages),
            format_claims(claims),
            "COMMIT;",
            "",
        ]
    )
    OUT.write_text(body)
    print(
        f"Wrote {OUT} "
        f"({len(customers)} customers, {len(policies)} policies, "
        f"{len(coverages)} coverages, {len(claims)} claims)"
    )


if __name__ == "__main__":
    main()
