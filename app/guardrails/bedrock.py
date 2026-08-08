"""Amazon Bedrock Guardrails — input screening and Converse config."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Literal

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.bedrock.config import (
    aws_region,
    guardrail_configured,
    guardrail_id,
    guardrail_version,
)

logger = logging.getLogger(__name__)

Source = Literal["INPUT", "OUTPUT"]


@dataclass(frozen=True)
class BedrockGuardrailResult:
    allowed: bool
    reason: str | None = None
    source: Source = "INPUT"


ClientFactory = Callable[[], Any]


def _default_client() -> Any:
    return boto3.client("bedrock-runtime", region_name=aws_region())


def _blocked_message(response: dict[str, Any]) -> str:
    outputs = response.get("outputs") or response.get("output") or []
    for item in outputs:
        text = item.get("text")
        if text:
            return str(text).strip()
    action_reason = response.get("actionReason")
    if action_reason:
        return str(action_reason).strip()
    return "Blocked by Bedrock Guardrails"


def _assessment_summary(response: dict[str, Any]) -> str | None:
    assessments = response.get("assessments") or []
    for assessment in assessments:
        topic_policy = assessment.get("topicPolicy") or {}
        for topic in topic_policy.get("topics") or []:
            if topic.get("action") == "BLOCKED":
                name = topic.get("name") or "denied topic"
                return f"Denied topic: {name}"
        content_policy = assessment.get("contentPolicy") or {}
        for filt in content_policy.get("filters") or []:
            if filt.get("action") == "BLOCKED":
                kind = filt.get("type") or "content policy"
                return f"Content policy: {kind}"
        word_policy = assessment.get("wordPolicy") or {}
        for word in word_policy.get("customWords") or []:
            if word.get("action") == "BLOCKED":
                match = word.get("match") or "blocked term"
                return f"Blocked term: {match}"
    return None


def check_text(
    text: str,
    *,
    source: Source = "INPUT",
    client_factory: ClientFactory | None = None,
) -> BedrockGuardrailResult:
    """Apply Bedrock Guardrails to text. No-op when guardrail env is unset."""
    if not guardrail_configured():
        return BedrockGuardrailResult(allowed=True)

    stripped = (text or "").strip()
    if not stripped:
        return BedrockGuardrailResult(allowed=True)

    factory = client_factory or _default_client
    client = factory()
    try:
        response = client.apply_guardrail(
            guardrailIdentifier=guardrail_id(),
            guardrailVersion=guardrail_version(),
            source=source,
            content=[{"text": {"text": stripped}}],
        )
    except (ClientError, BotoCoreError, OSError) as exc:
        logger.warning("Bedrock Guardrails check failed (%s); allowing request", exc)
        return BedrockGuardrailResult(allowed=True)

    if response.get("action") == "GUARDRAIL_INTERVENED":
        summary = _assessment_summary(response) or _blocked_message(response)
        return BedrockGuardrailResult(
            allowed=False,
            reason=summary,
            source=source,
        )

    return BedrockGuardrailResult(allowed=True)


def check_input(
    text: str,
    *,
    client_factory: ClientFactory | None = None,
) -> BedrockGuardrailResult:
    """Screen user input before Agent / Converse invocation."""
    return check_text(text, source="INPUT", client_factory=client_factory)
