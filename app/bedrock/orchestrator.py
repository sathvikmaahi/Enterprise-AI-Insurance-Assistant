"""Try Bedrock Agent first; on failure use Converse tool-use fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from app.auth import CurrentUser
from app.bedrock.agent import AgentInvokeError, AgentResult, invoke_agent
from app.bedrock.fallback import FallbackInvokeError, FallbackResult, invoke_fallback

logger = logging.getLogger(__name__)

PathName = Literal["agent", "fallback"]


@dataclass(frozen=True)
class AskResult:
    answer: str
    path: PathName
    role: str
    tools_used: list[str] = field(default_factory=list)
    fallback_reason: str | None = None


class AskOrchestrationError(Exception):
    """Neither Agent nor fallback could answer."""


AgentFn = Callable[..., AgentResult]
FallbackFn = Callable[..., FallbackResult]


def ask(
    question: str,
    user: CurrentUser,
    *,
    agent_fn: AgentFn | None = None,
    fallback_fn: FallbackFn | None = None,
    agent_client_factory: Callable[[], Any] | None = None,
    fallback_client_factory: Callable[[], Any] | None = None,
) -> AskResult:
    """Orchestrate Agent → fallback. Inject fns/clients in tests."""
    run_agent = agent_fn or invoke_agent
    run_fallback = fallback_fn or invoke_fallback

    fallback_reason: str | None = None
    try:
        agent_kwargs: dict[str, Any] = {"question": question, "user": user}
        if agent_client_factory is not None:
            agent_kwargs["client_factory"] = agent_client_factory
        agent_result = run_agent(**agent_kwargs)
        return AskResult(
            answer=agent_result.answer,
            path="agent",
            role=user.role,
            tools_used=list(agent_result.tools_used),
        )
    except AgentInvokeError as exc:
        fallback_reason = str(exc)
        logger.info("Agent path unavailable (%s); using Converse fallback", exc)

    try:
        fallback_kwargs: dict[str, Any] = {"question": question, "user": user}
        if fallback_client_factory is not None:
            fallback_kwargs["client_factory"] = fallback_client_factory
        fallback_result = run_fallback(**fallback_kwargs)
        return AskResult(
            answer=fallback_result.answer,
            path="fallback",
            role=user.role,
            tools_used=list(fallback_result.tools_used),
            fallback_reason=fallback_reason,
        )
    except FallbackInvokeError as exc:
        raise AskOrchestrationError(
            f"Agent failed ({fallback_reason}); fallback failed ({exc})"
        ) from exc
