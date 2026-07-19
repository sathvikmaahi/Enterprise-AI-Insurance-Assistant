"""Audit ring buffer."""

from __future__ import annotations

from app.logging.audit import clear_audit_log, list_recent, record


def setup_function() -> None:
    clear_audit_log()


def test_record_and_list_newest_first() -> None:
    record(
        username="agent",
        role="agent",
        concept="a",
        params={},
        sql=None,
        decision="allow",
        reason=None,
        latency_ms=1,
        row_count=1,
    )
    record(
        username="adjuster",
        role="adjuster",
        concept="b",
        params={},
        sql=None,
        decision="deny",
        reason="Access denied",
        latency_ms=2,
    )
    recent = list_recent(10)
    assert len(recent) == 2
    assert recent[0].concept == "b"
    assert recent[0].decision == "deny"
    assert recent[1].concept == "a"


def test_ring_buffer_evicts_oldest() -> None:
    from app.logging import audit as audit_mod

    original = audit_mod.CAPACITY
    audit_mod.CAPACITY = 3
    # rebuild deque with new maxlen by clearing and reassigning
    from collections import deque

    audit_mod._buffer = deque(maxlen=3)
    try:
        for i in range(5):
            record(
                username="u",
                role="agent",
                concept=str(i),
                params={},
                sql=None,
                decision="allow",
                reason=None,
                latency_ms=i,
            )
        names = [e.concept for e in list_recent(10)]
        assert names == ["4", "3", "2"]
    finally:
        audit_mod.CAPACITY = original
        clear_audit_log()
