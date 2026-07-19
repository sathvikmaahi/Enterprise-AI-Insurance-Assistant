"""Shared Bedrock tool runner."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.auth import CurrentUser
from app.bedrock.runner import (
    ToolAccessDenied,
    ToolMissingParameter,
    run_concept,
)
from app.logging.audit import clear_audit_log, list_recent
from app.semantic.models import ResolveResult


def setup_function() -> None:
    clear_audit_log()


def test_runner_denies_agent_open_claims() -> None:
    user = CurrentUser(username="agent", role="agent")
    with pytest.raises(ToolAccessDenied):
        run_concept(concept="open_claims", params={}, user=user)
    assert list_recent(1)[0].decision == "deny"


def test_runner_allows_adjuster_mocked() -> None:
    user = CurrentUser(username="adjuster", role="adjuster")
    fake = ResolveResult(
        concept="open_claims",
        rows=[{"claim_id": "CLM-001"}],
        sql="SELECT 1",
        params={},
    )
    with patch("app.bedrock.runner.resolve", return_value=fake):
        result = run_concept(concept="open_claims", params={}, user=user)
    assert result.row_count == 1
    assert result.rows[0]["claim_id"] == "CLM-001"
    assert list_recent(1)[0].decision == "allow"


def test_runner_missing_param() -> None:
    user = CurrentUser(username="agent", role="agent")
    with pytest.raises(ToolMissingParameter):
        run_concept(concept="customer_policies", params={}, user=user)
