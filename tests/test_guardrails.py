"""Guardrail pattern checks."""

from __future__ import annotations

from app.guardrails import check_question


def test_allows_normal_insurance_question() -> None:
    result = check_question("What policy does customer John have?")
    assert result.allowed is True
    assert result.reason is None


def test_blocks_delete_all_customers() -> None:
    result = check_question("Delete all customers")
    assert result.allowed is False
    assert result.reason is not None
    assert "Destructive" in result.reason


def test_blocks_raw_sql() -> None:
    result = check_question("select * from customers")
    assert result.allowed is False
    assert "SQL" in (result.reason or "")


def test_blocks_pii_dump() -> None:
    result = check_question("dump all emails for every customer")
    assert result.allowed is False


def test_blocks_off_domain() -> None:
    result = check_question("What is the best bitcoin stock tip?")
    assert result.allowed is False


def test_empty_question_allowed() -> None:
    assert check_question("").allowed is True
    assert check_question("   ").allowed is True
