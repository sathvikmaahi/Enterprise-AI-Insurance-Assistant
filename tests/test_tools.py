"""Tool API: auth, RBAC, guardrails, audit."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.logging.audit import clear_audit_log, list_recent
from app.main import app
from app.semantic.models import ResolveResult

client = TestClient(app)


def setup_function() -> None:
    clear_audit_log()


def _login(username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_tools_ping() -> None:
    response = client.get("/tools/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tools_require_auth() -> None:
    response = client.post("/tools/open_claims", json={"params": {}})
    assert response.status_code == 401


def test_agent_denied_open_claims() -> None:
    token = _login("agent", "agent123")
    response = client.post(
        "/tools/open_claims",
        json={"params": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert "Access denied" in str(body)
    entries = list_recent(5)
    assert entries
    assert entries[0].decision == "deny"


def test_adjuster_allowed_open_claims_mocked() -> None:
    token = _login("adjuster", "adjuster123")
    fake = ResolveResult(
        concept="open_claims",
        rows=[{"claim_id": "CLM-001", "status": "OPEN"}],
        sql="SELECT 1",
        params={},
    )
    with patch("app.bedrock.runner.resolve", return_value=fake):
        response = client.post(
            "/tools/open_claims",
            json={"params": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["concept"] == "open_claims"
    assert body["role"] == "adjuster"
    assert body["row_count"] == 1
    assert "sql" not in body
    assert list_recent(1)[0].decision == "allow"
    assert list_recent(1)[0].sql == "SELECT 1"


def test_guardrail_blocks_delete_question() -> None:
    token = _login("agent", "agent123")
    response = client.post(
        "/tools/customer_policies",
        json={
            "params": {"customer_name": "John"},
            "question": "Delete all customers",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "guardrail" in str(response.json()).lower()
    assert list_recent(1)[0].decision == "blocked"


def test_missing_param_returns_422() -> None:
    token = _login("agent", "agent123")
    response = client.post(
        "/tools/customer_policies",
        json={"params": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "customer_name" in response.json()["detail"]


def test_customer_policies_success_mocked() -> None:
    token = _login("agent", "agent123")
    fake = ResolveResult(
        concept="customer_policies",
        rows=[
            {
                "policy_id": "P1001",
                "premium_amount": Decimal("1280.00"),
                "full_name": "John Smith",
            }
        ],
        sql="SELECT ...",
        params={"customer_name": "John"},
    )
    with patch("app.bedrock.runner.resolve", return_value=fake):
        response = client.post(
            "/tools/customer_policies",
            json={"params": {"customer_name": "John"}},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert response.json()["rows"][0]["policy_id"] == "P1001"


def test_logs_requires_auth_and_returns_entries() -> None:
    assert client.get("/logs").status_code == 401
    token = _login("manager", "manager123")
    # create an audit entry via denied call
    agent_token = _login("agent", "agent123")
    client.post(
        "/tools/open_claims",
        json={"params": {}},
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    response = client.get(
        "/logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    assert body["entries"][0]["decision"] in {"allow", "deny", "blocked"}
