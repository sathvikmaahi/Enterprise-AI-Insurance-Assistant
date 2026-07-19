"""Bedrock Converse + tool-use fallback when the Agent path fails."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.auth import CurrentUser
from app.bedrock import config
from app.bedrock.runner import (
    ToolAccessDenied,
    ToolConceptNotFound,
    ToolMissingParameter,
    ToolRunnerError,
    run_concept,
)
from app.bedrock.tool_payload import build_success_payload, enrich_answer_if_needed
from app.bedrock.tool_specs import converse_tool_config

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = (
    "You are an insurance assistant. Answer using only the provided tools. "
    "Never invent SQL or database credentials. If a tool returns Access denied, "
    "tell the user they are not allowed. Be concise and business-friendly."
)


class FallbackInvokeError(Exception):
    """Converse fallback failed."""


@dataclass
class FallbackResult:
    answer: str
    tools_used: list[str] = field(default_factory=list)


ClientFactory = Callable[[], Any]


def _default_client() -> Any:
    return boto3.client("bedrock-runtime", region_name=config.aws_region())


def _extract_text(message: dict[str, Any]) -> str:
    parts: list[str] = []
    for block in message.get("content") or []:
        if "text" in block and block["text"]:
            parts.append(block["text"])
    return "\n".join(parts).strip()


def _tool_result_block(
    tool_use_id: str,
    payload: dict[str, Any],
    *,
    status: str = "success",
) -> dict[str, Any]:
    return {
        "toolResult": {
            "toolUseId": tool_use_id,
            "content": [{"json": payload}],
            "status": status,
        }
    }


def invoke_fallback(
    question: str,
    user: CurrentUser,
    *,
    client_factory: ClientFactory | None = None,
) -> FallbackResult:
    """Answer via Converse tool-use against the shared semantic tool runner."""
    if not config.fallback_configured():
        raise FallbackInvokeError("BEDROCK_FALLBACK_MODEL_ID is not configured")

    factory = client_factory or _default_client
    client = factory()
    tools_used: list[str] = []
    last_success_payload: dict[str, Any] | None = None
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": [{"text": question}]},
    ]
    tool_config = converse_tool_config()

    try:
        for _ in range(MAX_TOOL_ROUNDS + 1):
            response = client.converse(
                modelId=config.fallback_model_id(),
                messages=messages,
                system=[{"text": SYSTEM_PROMPT}],
                toolConfig=tool_config,
            )
            output = response.get("output", {}).get("message")
            if not output:
                raise FallbackInvokeError("Converse response missing output message")

            messages.append(output)
            stop_reason = response.get("stopReason")

            if stop_reason in {"end_turn", "max_tokens", "stop_sequence"}:
                answer = _extract_text(output)
                if not answer:
                    raise FallbackInvokeError("Converse returned empty answer")
                enriched = enrich_answer_if_needed(answer, last_success_payload)
                return FallbackResult(answer=enriched, tools_used=tools_used)

            if stop_reason != "tool_use":
                raise FallbackInvokeError(f"Unexpected Converse stopReason: {stop_reason}")

            tool_result_content: list[dict[str, Any]] = []
            for block in output.get("content") or []:
                tool_use = block.get("toolUse")
                if not tool_use:
                    continue
                name = tool_use.get("name") or ""
                tool_use_id = tool_use.get("toolUseId") or ""
                params = tool_use.get("input") or {}
                if not isinstance(params, dict):
                    params = {}

                tools_used.append(name)
                try:
                    result = run_concept(concept=name, params=params, user=user)
                    payload = build_success_payload(result)
                    last_success_payload = payload
                    tool_result_content.append(
                        _tool_result_block(tool_use_id, payload, status="success")
                    )
                except ToolAccessDenied as exc:
                    tool_result_content.append(
                        _tool_result_block(
                            tool_use_id,
                            {
                                "error": "Access denied",
                                "concept": exc.concept,
                                "role": exc.role,
                            },
                            status="error",
                        )
                    )
                except ToolConceptNotFound as exc:
                    tool_result_content.append(
                        _tool_result_block(
                            tool_use_id,
                            {"error": "Unknown concept", "concept": exc.concept},
                            status="error",
                        )
                    )
                except ToolMissingParameter as exc:
                    tool_result_content.append(
                        _tool_result_block(
                            tool_use_id,
                            {"error": str(exc)},
                            status="error",
                        )
                    )
                except ToolRunnerError as exc:
                    tool_result_content.append(
                        _tool_result_block(
                            tool_use_id,
                            {"error": str(exc)},
                            status="error",
                        )
                    )

            if not tool_result_content:
                raise FallbackInvokeError("Converse requested tools but none were found")

            messages.append({"role": "user", "content": tool_result_content})

        raise FallbackInvokeError("Converse exceeded tool-use round limit")
    except FallbackInvokeError:
        raise
    except (ClientError, BotoCoreError, OSError) as exc:
        logger.warning("Bedrock Converse fallback failed: %s", exc)
        raise FallbackInvokeError(str(exc)) from exc
