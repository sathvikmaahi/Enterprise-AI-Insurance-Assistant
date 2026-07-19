"""Concept-level RBAC."""

from __future__ import annotations

import pytest

from app.rbac import AccessDeniedError, assert_allowed
from app.semantic import ConceptNotFoundError, clear_concepts_cache


@pytest.fixture(autouse=True)
def _reload_concepts() -> None:
    clear_concepts_cache()
    yield
    clear_concepts_cache()


def test_agent_denied_open_claims() -> None:
    with pytest.raises(AccessDeniedError) as exc:
        assert_allowed("open_claims", "agent")
    assert exc.value.concept == "open_claims"
    assert exc.value.role == "agent"


def test_adjuster_allowed_open_claims() -> None:
    assert_allowed("open_claims", "adjuster")


def test_manager_allowed_claim_summary() -> None:
    assert_allowed("claim_summary", "manager")


def test_agent_allowed_customer_policies() -> None:
    assert_allowed("customer_policies", "agent")


def test_unknown_concept_raises() -> None:
    with pytest.raises(ConceptNotFoundError):
        assert_allowed("not_a_real_concept", "manager")
