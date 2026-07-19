"""Bedrock Agent return-control path (mocked boto3 client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.auth import CurrentUser
from app.bedrock.agent import AgentInvokeError, invoke_agent
from app.bedrock.runner import ToolRunResult
from app.logging.audit import clear_audit_log


def setup_function() -> None:
    clear_audit_log()


def test_agent_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("BEDROCK_AGENT_ID", raising=False)
    monkeypatch.delenv("BEDROCK_AGENT_ALIAS_ID", raising=False)
    monkeypatch.setenv("BEDROCK_FORCE_FALLBACK", "false")
    user = CurrentUser(username="agent", role="agent")
    with pytest.raises(AgentInvokeError, match="not configured"):
        invoke_agent("hello", user)


def test_agent_force_fallback(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_AGENT_ID", "A")
    monkeypatch.setenv("BEDROCK_AGENT_ALIAS_ID", "B")
    monkeypatch.setenv("BEDROCK_FORCE_FALLBACK", "true")
    user = CurrentUser(username="agent", role="agent")
    with pytest.raises(AgentInvokeError, match="FORCE_FALLBACK"):
        invoke_agent("hello", user)


def test_agent_return_control_then_answer(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_AGENT_ID", "AGENT")
    monkeypatch.setenv("BEDROCK_AGENT_ALIAS_ID", "ALIAS")
    monkeypatch.setenv("BEDROCK_FORCE_FALLBACK", "false")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    user = CurrentUser(username="agent", role="agent")
    client = MagicMock()

    return_control_events = [
        {
            "returnControl": {
                "invocationId": "inv-1",
                "invocationInputs": [
                    {
                        "functionInvocationInput": {
                            "actionGroup": "SemanticTools",
                            "function": "customer_policies",
                            "parameters": [
                                {
                                    "name": "customer_name",
                                    "type": "string",
                                    "value": "John",
                                }
                            ],
                        }
                    }
                ],
            }
        }
    ]
    final_events = [
        {"chunk": {"bytes": b"John has policy P1001."}},
    ]
    client.invoke_agent.side_effect = [
        {"completion": iter(return_control_events)},
        {"completion": iter(final_events)},
    ]

    fake_run = ToolRunResult(
        concept="customer_policies",
        role="agent",
        rows=[{"policy_id": "P1001"}],
        row_count=1,
        sql="SELECT 1",
        params={"customer_name": "John"},
    )

    with patch("app.bedrock.agent.run_concept", return_value=fake_run):
        result = invoke_agent(
            "What policies does John have?",
            user,
            client_factory=lambda: client,
        )

    assert result.answer == "John has policy P1001."
    assert result.tools_used == ["customer_policies"]
    assert client.invoke_agent.call_count == 2
    second_kwargs = client.invoke_agent.call_args_list[1].kwargs
    assert "returnControlInvocationResults" in second_kwargs["sessionState"]
