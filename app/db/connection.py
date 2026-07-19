"""PostgreSQL connection helpers (Amazon RDS). Parameterized SQL only."""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from typing import Any

Params = Sequence[Any] | Mapping[str, Any] | None

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

_pool: ConnectionPool | None = None


class DatabaseConfigError(RuntimeError):
    """Raised when DATABASE_URL is missing or unusable."""


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise DatabaseConfigError(
            "DATABASE_URL is not set. Copy .env.example to .env and configure RDS."
        )
    return url


def get_pool() -> ConnectionPool:
    """Return a process-wide connection pool (created on first use)."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=get_database_url(),
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


def close_pool() -> None:
    """Close the pool if it was opened (tests / shutdown)."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def fetch_all(sql: str, params: Params = None) -> list[dict[str, Any]]:
    """Execute a parameterized query and return all rows as dicts."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params if params is not None else ())
            return list(cur.fetchall())


def fetch_one(sql: str, params: Params = None) -> dict[str, Any] | None:
    """Execute a parameterized query and return one row (or None)."""
    with get_pool().connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params if params is not None else ())
            return cur.fetchone()
