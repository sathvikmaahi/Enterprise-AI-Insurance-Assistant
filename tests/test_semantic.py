"""Semantic layer: YAML concepts → parameterized SQL → rows."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest

from app.semantic.loader import ConceptLoadError, load_concepts
from app.semantic.resolver import (
    ConceptNotFoundError,
    MissingParameterError,
    resolve,
)


CONCEPTS_DIR = Path(__file__).resolve().parents[1] / "app" / "semantic" / "concepts"


def test_load_concepts_finds_five_demo_concepts() -> None:
    concepts = load_concepts(CONCEPTS_DIR)
    names = set(concepts)
    assert names == {
        "customer_policies",
        "policy_premium",
        "open_claims",
        "coverage_by_type",
        "claim_summary",
    }


def test_load_concepts_rejects_missing_sql(tmp_path: Path) -> None:
    bad = tmp_path / "broken.yaml"
    bad.write_text(
        "name: broken\ndescription: x\nparams: []\nallowed_roles: [agent]\nresponse_fields: []\n",
        encoding="utf-8",
    )
    with pytest.raises(ConceptLoadError, match="sql"):
        load_concepts(tmp_path)


def test_resolve_unknown_concept_raises() -> None:
    with pytest.raises(ConceptNotFoundError, match="unknown_thing"):
        resolve("unknown_thing", {})


def test_resolve_missing_required_param_raises() -> None:
    with pytest.raises(MissingParameterError, match="customer_name"):
        resolve("customer_policies", {})


def test_resolve_uses_parameterized_execute_not_string_concat() -> None:
    """Resolver must pass params separately — never interpolate into SQL text."""
    fake_rows = [
        {
            "policy_id": "P1001",
            "product_type": "auto",
            "status": "ACTIVE",
            "premium_amount": Decimal("1280.00"),
            "full_name": "John Smith",
            "customer_id": "C001",
        }
    ]
    with patch("app.semantic.resolver.fetch_all", return_value=fake_rows) as mock_fetch:
        result = resolve("customer_policies", {"customer_name": "John"})

    assert result.concept == "customer_policies"
    assert result.rows == fake_rows
    sql, params = mock_fetch.call_args.args
    assert "%(customer_name)s" in sql or "%s" in sql
    assert "John" not in sql  # value must not be concatenated into SQL
    assert params == {"customer_name": "John"} or params == ("John",)


def test_resolve_open_claims_calls_fetch_with_no_user_params() -> None:
    fake_rows = [{"claim_id": "CLM-001", "status": "OPEN", "policy_id": "P1001"}]
    with patch("app.semantic.resolver.fetch_all", return_value=fake_rows) as mock_fetch:
        result = resolve("open_claims", {})

    assert len(result.rows) == 1
    sql, params = mock_fetch.call_args.args
    assert "OPEN" in sql  # status filter is part of approved template
    assert params == {}


def test_resolve_policy_premium_shapes_single_row_mode() -> None:
    fake_row = {"policy_id": "P1001", "premium_amount": Decimal("1280.00")}
    with patch("app.semantic.resolver.fetch_one", return_value=fake_row):
        result = resolve("policy_premium", {"policy_id": "P1001"})

    assert result.rows[0]["policy_id"] == "P1001"
    assert result.rows[0]["premium_amount"] == Decimal("1280.00")


def test_claim_summary_requires_policy_id_or_customer_name() -> None:
    with pytest.raises(MissingParameterError, match="policy_id|customer_name"):
        resolve("claim_summary", {})


def test_allowed_roles_metadata_and_resolve_stays_role_agnostic() -> None:
    """YAML carries roles; resolve() itself does not enforce (API/RBAC does)."""
    concepts = load_concepts(CONCEPTS_DIR)
    assert "agent" not in concepts["open_claims"].allowed_roles
    assert "adjuster" in concepts["open_claims"].allowed_roles
    fake_rows = [{"claim_id": "CLM-001", "status": "OPEN"}]
    with patch("app.semantic.resolver.fetch_all", return_value=fake_rows):
        result = resolve("open_claims", {})
    assert result.rows


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="Live RDS not configured")
def test_live_customer_policies_john_returns_p1001() -> None:
    from app.db.connection import close_pool

    close_pool()
    result = resolve("customer_policies", {"customer_name": "John"})
    close_pool()
    policy_ids = {row["policy_id"] for row in result.rows}
    assert "P1001" in policy_ids


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="Live RDS not configured")
def test_live_policy_premium_p1001() -> None:
    from app.db.connection import close_pool

    close_pool()
    result = resolve("policy_premium", {"policy_id": "P1001"})
    close_pool()
    assert len(result.rows) == 1
    assert Decimal(str(result.rows[0]["premium_amount"])) == Decimal("1280.00")


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="Live RDS not configured")
def test_live_open_claims_nonempty() -> None:
    from app.db.connection import close_pool

    close_pool()
    result = resolve("open_claims", {})
    close_pool()
    assert len(result.rows) >= 1
    assert all(row["status"] == "OPEN" for row in result.rows)


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="Live RDS not configured")
def test_live_coverage_by_type_windshield_includes_p1001() -> None:
    from app.db.connection import close_pool

    close_pool()
    result = resolve("coverage_by_type", {"coverage_type": "windshield"})
    close_pool()
    policy_ids = {row["policy_id"] for row in result.rows}
    assert "P1001" in policy_ids
