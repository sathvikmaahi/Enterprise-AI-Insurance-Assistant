"""Shared in-process tool runner: RBAC → resolve → audit."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from fastapi.encoders import jsonable_encoder

from app.auth import CurrentUser
from app.logging.audit import record
from app.rbac import AccessDeniedError, assert_allowed
from app.semantic import (
    ConceptNotFoundError,
    MissingParameterError,
    resolve,
)


class ToolRunnerError(Exception):
    """Base error for in-process tool execution."""


class ToolAccessDenied(ToolRunnerError):
    def __init__(self, concept: str, role: str) -> None:
        self.concept = concept
        self.role = role
        super().__init__(f"Access denied for role {role!r} on concept {concept!r}")


class ToolConceptNotFound(ToolRunnerError):
    def __init__(self, concept: str) -> None:
        self.concept = concept
        super().__init__(f"Unknown concept: {concept}")


class ToolMissingParameter(ToolRunnerError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class ToolRunResult:
    concept: str
    role: str
    rows: list[dict[str, Any]]
    row_count: int
    sql: str
    params: dict[str, Any]


def run_concept(
    *,
    concept: str,
    params: dict[str, Any] | None,
    user: CurrentUser,
) -> ToolRunResult:
    """Execute a semantic concept with RBAC + audit (no HTTP hop)."""
    started = time.perf_counter()
    bound_params = dict(params or {})

    def latency_ms() -> int:
        return int((time.perf_counter() - started) * 1000)

    try:
        assert_allowed(concept, user.role)
    except ConceptNotFoundError as exc:
        raise ToolConceptNotFound(concept) from exc
    except AccessDeniedError as exc:
        record(
            username=user.username,
            role=user.role,
            concept=concept,
            params=bound_params,
            sql=None,
            decision="deny",
            reason="Access denied",
            latency_ms=latency_ms(),
        )
        raise ToolAccessDenied(exc.concept, exc.role) from exc

    try:
        result = resolve(concept, bound_params)
    except ConceptNotFoundError as exc:
        raise ToolConceptNotFound(concept) from exc
    except MissingParameterError as exc:
        raise ToolMissingParameter(str(exc)) from exc

    rows = jsonable_encoder(result.rows)
    ms = latency_ms()
    record(
        username=user.username,
        role=user.role,
        concept=result.concept,
        params=result.params,
        sql=result.sql,
        decision="allow",
        reason=None,
        latency_ms=ms,
        row_count=len(rows),
    )
    return ToolRunResult(
        concept=result.concept,
        role=user.role,
        rows=rows,
        row_count=len(rows),
        sql=result.sql,
        params=result.params,
    )
