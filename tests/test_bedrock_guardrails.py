"""Bedrock Guardrails apply_guardrail (mocked boto3)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.bedrock.config import guardrail_config_dict
from app.guardrails.bedrock import (
    check_input,
    check_text,
)


def test_guardrail_config_none_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("BEDROCK_GUARDRAIL_ID", raising=False)
    assert guardrail_config_dict() is None


def test_guardrail_config_when_set(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-abc123")
    monkeypatch.setenv("BEDROCK_GUARDRAIL_VERSION", "2")
    cfg = guardrail_config_dict()
    assert cfg == {
        "guardrailIdentifier": "gr-abc123",
        "guardrailVersion": "2",
    }


def test_check_input_skips_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("BEDROCK_GUARDRAIL_ID", raising=False)
    result = check_input("What policies does John have?")
    assert result.allowed is True


def test_check_input_allows_clean_question(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-abc123")
    monkeypatch.setenv("BEDROCK_GUARDRAIL_VERSION", "1")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    client = MagicMock()
    client.apply_guardrail.return_value = {"action": "NONE"}

    result = check_input(
        "What policies does John have?",
        client_factory=lambda: client,
    )
    assert result.allowed is True
    client.apply_guardrail.assert_called_once()
    call_kwargs = client.apply_guardrail.call_args.kwargs
    assert call_kwargs["guardrailIdentifier"] == "gr-abc123"
    assert call_kwargs["source"] == "INPUT"


def test_check_input_blocks_on_intervention(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-abc123")
    monkeypatch.setenv("BEDROCK_GUARDRAIL_VERSION", "1")

    client = MagicMock()
    client.apply_guardrail.return_value = {
        "action": "GUARDRAIL_INTERVENED",
        "outputs": [{"text": "Sorry, I cannot help with that request."}],
        "assessments": [
            {
                "topicPolicy": {
                    "topics": [
                        {
                            "name": "Financial advice",
                            "action": "BLOCKED",
                        }
                    ]
                }
            }
        ],
    }

    result = check_input(
        "What bitcoin stock should I buy?",
        client_factory=lambda: client,
    )
    assert result.allowed is False
    assert result.reason is not None
    assert "Financial advice" in result.reason


def test_check_input_fails_open_on_aws_error(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-abc123")
    monkeypatch.setenv("BEDROCK_GUARDRAIL_VERSION", "1")

    client = MagicMock()
    client.apply_guardrail.side_effect = OSError("network down")

    result = check_input("hello", client_factory=lambda: client)
    assert result.allowed is True


def test_check_text_empty_allowed(monkeypatch) -> None:
    monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-abc123")
    result = check_text("   ", source="OUTPUT")
    assert result.allowed is True
