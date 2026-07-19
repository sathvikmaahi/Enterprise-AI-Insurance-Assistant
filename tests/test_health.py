from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok_when_db_ok() -> None:
    with patch("app.main.check_db", return_value={"db": "ok"}):
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_returns_ok_status_when_db_error() -> None:
    with patch(
        "app.main.check_db",
        return_value={"db": "error", "db_detail": "DATABASE_URL is not set"},
    ):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "error"
    assert "DATABASE_URL" in body["db_detail"]
