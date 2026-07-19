"""Semantic tool endpoints for agents and (later) Bedrock action groups."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import CurrentUser, get_current_user
from app.bedrock.runner import (
    ToolAccessDenied,
    ToolConceptNotFound,
    ToolMissingParameter,
    run_concept,
)
from app.guardrails import check_question
from app.logging.audit import record

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    question: str | None = None


class ToolResponse(BaseModel):
    concept: str
    role: str
    row_count: int
    rows: list[dict[str, Any]]


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"status": "ok", "service": "tools"}


@router.post("/{concept}", response_model=ToolResponse)
def run_tool(
    concept: str,
    body: ToolRequest,
    user: CurrentUser = Depends(get_current_user),
) -> ToolResponse:
    started = time.perf_counter()
    params = body.params or {}

    def latency_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    question = (body.question or "").strip()
    if question:
        guard = check_question(question)
        if not guard.allowed:
            record(
                username=user.username,
                role=user.role,
                concept=concept,
                params=params,
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
        result = run_concept(concept=concept, params=params, user=user)
    except ToolConceptNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ToolAccessDenied as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "detail": "Access denied",
                "concept": exc.concept,
                "role": exc.role,
            },
        ) from exc
    except ToolMissingParameter as exc:
        raise HTTPException(
            status_code=getattr(
                status, "HTTP_422_UNPROCESSABLE_CONTENT", 422
            ),
            detail=exc.message,
        ) from exc

    return ToolResponse(
        concept=result.concept,
        role=result.role,
        row_count=result.row_count,
        rows=result.rows,
    )
