"""Converse fallback tool-use loop (mocked boto3 client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.auth import CurrentUser
from app.bedrock.fallback import invoke_fallback
from app.bedrock.runner import ToolRunResult
from app.logging.audit import clear_audit_log


def setup_function() -> None:
    clear_audit_log()


def test_converse_tool_use_then_answer(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_FALLBACK_MODEL_ID", "amazon.nova-lite-v1:0")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    user = CurrentUser(username="agent", role="agent")
    client = MagicMock()

    tool_round = {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "t1",
                            "name": "customer_policies",
                            "input": {"customer_name": "John"},
                        }
                    }
                ],
            }
        },
    }
    final_round = {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"text": "John has policy P1001."}],
            }
        },
    }
    client.converse.side_effect = [tool_round, final_round]

    fake_run = ToolRunResult(
        concept="customer_policies",
        role="agent",
        rows=[{"policy_id": "P1001"}],
        row_count=1,
        sql="SELECT 1",
        params={"customer_name": "John"},
    )

    with patch("app.bedrock.fallback.run_concept", return_value=fake_run):
        result = invoke_fallback(
            "What policies does John have?",
            user,
            client_factory=lambda: client,
        )

    assert result.answer == "John has policy P1001."
    assert result.tools_used == ["customer_policies"]
    assert client.converse.call_count == 2
