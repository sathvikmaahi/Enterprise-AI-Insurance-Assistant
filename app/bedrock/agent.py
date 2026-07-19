"""Bedrock Agent invoke with return-control tool execution."""

from __future__ import annotations

import json
import logging
import uuid
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

logger = logging.getLogger(__name__)

MAX_RETURN_CONTROL_ROUNDS = 5
ACTION_GROUP_NAME = "SemanticTools"


class AgentInvokeError(Exception):
    """Agent path failed; orchestrator should try fallback."""


@dataclass
class AgentResult:
    answer: str
    tools_used: list[str] = field(default_factory=list)


ClientFactory = Callable[[], Any]


def _default_client() -> Any:
    return boto3.client("bedrock-agent-runtime", region_name=config.aws_region())


def _decode_chunk(chunk: dict[str, Any]) -> str:
    raw = chunk.get("bytes")
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def _params_from_invocation(function_input: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for item in function_input.get("parameters") or []:
        name = item.get("name")
        if not name:
            continue
        params[name] = item.get("value")
    return params


def _execute_return_control(
    return_control: dict[str, Any],
    user: CurrentUser,
    tools_used: list[str],
) -> dict[str, Any]:
    """Build sessionState with function results for the next invoke_agent call."""
    invocation_id = return_control.get("invocationId")
    results: list[dict[str, Any]] = []

    for item in return_control.get("invocationInputs") or []:
        function_input = item.get("functionInvocationInput") or {}
        function_name = function_input.get("function") or ""
        action_group = function_input.get("actionGroup") or ACTION_GROUP_NAME
        params = _params_from_invocation(function_input)

        if not function_name:
            body = {"error": "Missing function name in return control"}
        else:
            tools_used.append(function_name)
            try:
                result = run_concept(concept=function_name, params=params, user=user)
                body = {
                    "concept": result.concept,
                    "row_count": result.row_count,
                    "rows": result.rows,
                }
            except ToolAccessDenied as exc:
                body = {
                    "error": "Access denied",
                    "concept": exc.concept,
                    "role": exc.role,
                }
            except ToolConceptNotFound as exc:
                body = {"error": "Unknown concept", "concept": exc.concept}
            except ToolMissingParameter as exc:
                body = {"error": str(exc)}
            except ToolRunnerError as exc:
                body = {"error": str(exc)}

        results.append(
            {
                "functionResult": {
                    "actionGroup": action_group,
                    "function": function_name or "unknown",
                    "responseBody": {
                        "TEXT": {"body": json.dumps(body, default=str)},
                    },
                }
            }
        )

    session_state: dict[str, Any] = {
        "returnControlInvocationResults": results,
    }
    if invocation_id:
        session_state["invocationId"] = invocation_id
    return session_state


def _consume_completion(
    completion: Any,
) -> tuple[str, dict[str, Any] | None]:
    """Parse invoke_agent event stream into answer text and optional returnControl."""
    answer_parts: list[str] = []
    return_control: dict[str, Any] | None = None

    for event in completion:
        if "chunk" in event:
            answer_parts.append(_decode_chunk(event["chunk"]))
        if "returnControl" in event:
            return_control = event["returnControl"]

    return "".join(answer_parts).strip(), return_control


def invoke_agent(
    question: str,
    user: CurrentUser,
    *,
    session_id: str | None = None,
    client_factory: ClientFactory | None = None,
) -> AgentResult:
    """Invoke Bedrock Agent; handle return-control by running tools in-process."""
    if config.force_fallback():
        raise AgentInvokeError("BEDROCK_FORCE_FALLBACK is enabled")
    if not config.agent_configured():
        raise AgentInvokeError("Bedrock Agent is not configured")

    factory = client_factory or _default_client
    client = factory()
    sid = session_id or str(uuid.uuid4())
    tools_used: list[str] = []
    session_state: dict[str, Any] | None = {
        "promptSessionAttributes": {
            "username": user.username,
            "role": user.role,
        }
    }
    input_text = question
    final_answer = ""

    try:
        for _ in range(MAX_RETURN_CONTROL_ROUNDS + 1):
            kwargs: dict[str, Any] = {
                "agentId": config.agent_id(),
                "agentAliasId": config.agent_alias_id(),
                "sessionId": sid,
                "inputText": input_text,
            }
            if session_state is not None:
                kwargs["sessionState"] = session_state

            response = client.invoke_agent(**kwargs)
            completion = response.get("completion")
            if completion is None:
                raise AgentInvokeError("Agent response missing completion stream")

            answer, return_control = _consume_completion(completion)
            if answer:
                final_answer = answer

            if return_control is None:
                if not final_answer:
                    raise AgentInvokeError("Agent returned empty answer")
                return AgentResult(answer=final_answer, tools_used=tools_used)

            session_state = _execute_return_control(return_control, user, tools_used)
            # Continuation uses empty input; results are in sessionState.
            input_text = ""

        raise AgentInvokeError("Agent exceeded return-control round limit")
    except AgentInvokeError:
        raise
    except (ClientError, BotoCoreError, OSError) as exc:
        logger.warning("Bedrock Agent invoke failed: %s", exc)
        raise AgentInvokeError(str(exc)) from exc
