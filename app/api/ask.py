"""Natural-language ask endpoint (Bedrock Agent + Converse fallback)."""

from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.bedrock import AskOrchestrationError, ask
from app.guardrails import check_question
from app.logging.audit import record

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class AskResponse(BaseModel):
    answer: str
    path: Literal["agent", "fallback"]
    role: str
    tools_used: list[str] = Field(default_factory=list)
    fallback_reason: str | None = None


@router.post("/ask", response_model=AskResponse)
def ask_question(
    body: AskRequest,
    user: CurrentUser = Depends(get_current_user),
) -> AskResponse:
    started = time.perf_counter()
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question must not be empty",
        )

    def latency_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    guard = check_question(question)
    if not guard.allowed:
        record(
            username=user.username,
            role=user.role,
            concept=None,
            params={"question": question},
            sql=None,
            decision="blocked",
            reason=guard.reason,
            latency_ms=latency_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Blocked by guardrail", "reason": guard.reason},
        )

    try:
        result = ask(question, user)
    except AskOrchestrationError as exc:
        record(
            username=user.username,
            role=user.role,
            concept=None,
            params={"question": question},
            sql=None,
            decision="deny",
            reason=str(exc),
            latency_ms=latency_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Unable to answer question",
                "reason": str(exc),
            },
        ) from exc

    record(
        username=user.username,
        role=user.role,
        concept=result.tools_used[0] if result.tools_used else None,
        params={"question": question, "path": result.path},
        sql=None,
        decision="allow",
        reason=result.fallback_reason,
        latency_ms=latency_ms(),
        row_count=0,
    )
    return AskResponse(
        answer=result.answer,
        path=result.path,
        role=result.role,
        tools_used=result.tools_used,
        fallback_reason=result.fallback_reason,
    )
