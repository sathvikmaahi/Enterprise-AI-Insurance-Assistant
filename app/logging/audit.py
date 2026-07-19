"""In-memory audit ring buffer for demo observability."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Literal

Decision = Literal["allow", "deny", "blocked"]

CAPACITY = 200


@dataclass(frozen=True)
class AuditEntry:
    timestamp: str
    username: str
    role: str
    concept: str | None
    params: dict[str, Any]
    sql: str | None
    decision: Decision
    reason: str | None
    latency_ms: int
    row_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_lock = Lock()
_buffer: deque[AuditEntry] = deque(maxlen=CAPACITY)


def clear_audit_log() -> None:
    """Reset buffer (tests)."""
    with _lock:
        _buffer.clear()


def record(
    *,
    username: str,
    role: str,
    concept: str | None,
    params: dict[str, Any] | None,
    sql: str | None,
    decision: Decision,
    reason: str | None,
    latency_ms: int,
    row_count: int = 0,
) -> AuditEntry:
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        username=username,
        role=role,
        concept=concept,
        params=dict(params or {}),
        sql=sql,
        decision=decision,
        reason=reason,
        latency_ms=latency_ms,
        row_count=row_count,
    )
    with _lock:
        _buffer.append(entry)
    return entry


def list_recent(limit: int = 50) -> list[AuditEntry]:
    """Return newest-first audit entries (up to limit)."""
    if limit < 1:
        return []
    with _lock:
        items = list(_buffer)
    items.reverse()
    return items[:limit]
