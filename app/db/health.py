"""Database health checks for /health."""

from __future__ import annotations

from typing import Any

from app.db.connection import DatabaseConfigError, fetch_one


def check_db() -> dict[str, Any]:
    """
    Probe RDS connectivity and confirm demo seed is present.

    Returns a payload fragment:
      {"db": "ok"} on success
      {"db": "error", "db_detail": "..."} on failure
    """
    try:
        row = fetch_one("SELECT 1 AS ok")
        if row is None or row.get("ok") != 1:
            return {"db": "error", "db_detail": "unexpected SELECT 1 result"}

        john = fetch_one(
            "SELECT customer_id FROM customers WHERE full_name ILIKE %s LIMIT 1",
            ("%John%",),
        )
        if john is None:
            return {
                "db": "error",
                "db_detail": "connected but seed missing (John Smith not found)",
            }
        return {"db": "ok"}
    except DatabaseConfigError as exc:
        return {"db": "error", "db_detail": str(exc)}
    except Exception as exc:  # noqa: BLE001 — health must never raise
        return {"db": "error", "db_detail": str(exc)}
