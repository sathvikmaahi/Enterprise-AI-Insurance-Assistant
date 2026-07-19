import os
from unittest.mock import MagicMock, patch

import pytest

from app.db.connection import DatabaseConfigError, close_pool, fetch_all, fetch_one, get_database_url
from app.db.health import check_db


def test_get_database_url_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DatabaseConfigError, match="DATABASE_URL"):
        get_database_url()


def test_get_database_url_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host:5432/insurance")
    assert get_database_url() == "postgresql://u:p@host:5432/insurance"


def test_fetch_all_uses_parameterized_execute() -> None:
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"policy_id": "P1001"}]
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    pool = MagicMock()
    pool.connection.return_value.__enter__.return_value = conn

    with patch("app.db.connection.get_pool", return_value=pool):
        rows = fetch_all(
            "SELECT policy_id FROM policies WHERE customer_id = %s",
            ("C001",),
        )

    cursor.execute.assert_called_once_with(
        "SELECT policy_id FROM policies WHERE customer_id = %s",
        ("C001",),
    )
    assert rows == [{"policy_id": "P1001"}]


def test_fetch_one_returns_none_when_empty() -> None:
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    pool = MagicMock()
    pool.connection.return_value.__enter__.return_value = conn

    with patch("app.db.connection.get_pool", return_value=pool):
        row = fetch_one("SELECT 1 AS ok WHERE false")

    assert row is None


def test_check_db_ok_when_select_and_john_present() -> None:
    with patch(
        "app.db.health.fetch_one",
        side_effect=[{"ok": 1}, {"customer_id": "C001"}],
    ):
        assert check_db() == {"db": "ok"}


def test_check_db_error_when_url_missing() -> None:
    with patch(
        "app.db.health.fetch_one",
        side_effect=DatabaseConfigError("DATABASE_URL is not set"),
    ):
        result = check_db()
    assert result["db"] == "error"
    assert "DATABASE_URL" in result["db_detail"]


def test_check_db_error_when_seed_missing() -> None:
    with patch(
        "app.db.health.fetch_one",
        side_effect=[{"ok": 1}, None],
    ):
        result = check_db()
    assert result["db"] == "error"
    assert "seed missing" in result["db_detail"]


def test_close_pool_resets_singleton() -> None:
    mock_pool = MagicMock()
    with patch("app.db.connection._pool", mock_pool):
        close_pool()
        mock_pool.close.assert_called_once()
    # ensure module-level pool is cleared for other tests
    close_pool()


@pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="Live RDS not configured")
def test_live_select_one() -> None:
    """Optional smoke against real RDS when DATABASE_URL is set."""
    close_pool()
    row = fetch_one("SELECT 1 AS ok")
    assert row is not None
    assert row["ok"] == 1
    close_pool()
