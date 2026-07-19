"""POST /ask: auth, guardrails, Agent path, Converse fallback."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.auth import CurrentUser
from app.bedrock.agent import AgentInvokeError, AgentResult
from app.bedrock.fallback import FallbackResult
from app.bedrock import AskOrchestrationError
from app.bedrock.orchestrator import AskResult
from app.logging.audit import clear_audit_log, list_recent
from app.main import app

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


def test_ask_requires_auth() -> None:
    response = client.post("/ask", json={"question": "What policies does John have?"})
    assert response.status_code == 401


def test_ask_guardrail_blocks() -> None:
    token = _login("agent", "agent123")
    response = client.post(
        "/ask",
        json={"question": "Delete all customers"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "guardrail" in str(response.json()).lower()
    assert list_recent(1)[0].decision == "blocked"


def test_ask_agent_path() -> None:
    token = _login("agent", "agent123")
    fake = AskResult(
        answer="John has policy P1001.",
        path="agent",
        role="agent",
        tools_used=["customer_policies"],
    )
    with patch("app.api.ask.ask", return_value=fake):
        response = client.post(
            "/ask",
            json={"question": "What policies does John have?"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "agent"
    assert body["answer"] == "John has policy P1001."
    assert body["tools_used"] == ["customer_policies"]
    assert body["fallback_reason"] is None
    assert list_recent(1)[0].decision == "allow"


def test_ask_fallback_path() -> None:
    token = _login("adjuster", "adjuster123")
    fake = AskResult(
        answer="There are 3 open claims.",
        path="fallback",
        role="adjuster",
        tools_used=["open_claims"],
        fallback_reason="Bedrock Agent is not configured",
    )
    with patch("app.api.ask.ask", return_value=fake):
        response = client.post(
            "/ask",
            json={"question": "Show open claims"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["path"] == "fallback"
    assert "not configured" in (body["fallback_reason"] or "")


def test_ask_orchestration_failure_returns_503() -> None:
    token = _login("agent", "agent123")
    with patch(
        "app.api.ask.ask",
        side_effect=AskOrchestrationError("both failed"),
    ):
        response = client.post(
            "/ask",
            json={"question": "What policies does John have?"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 503


def test_orchestrator_falls_back_when_agent_fails() -> None:
    from app.bedrock.orchestrator import ask as orchestrate

    user = CurrentUser(username="agent", role="agent")

    def boom(**_kwargs):
        raise AgentInvokeError("simulated agent failure")

    def ok(**_kwargs):
        return FallbackResult(answer="fallback answer", tools_used=["customer_policies"])

    result = orchestrate(
        "What policies does John have?",
        user,
        agent_fn=boom,
        fallback_fn=ok,
    )
    assert result.path == "fallback"
    assert result.answer == "fallback answer"
    assert result.fallback_reason == "simulated agent failure"


def test_orchestrator_prefers_agent() -> None:
    from app.bedrock.orchestrator import ask as orchestrate

    user = CurrentUser(username="agent", role="agent")

    def agent_ok(**_kwargs):
        return AgentResult(answer="agent answer", tools_used=["customer_policies"])

    def fallback_should_not_run(**_kwargs):
        raise AssertionError("fallback should not run")

    result = orchestrate(
        "What policies does John have?",
        user,
        agent_fn=agent_ok,
        fallback_fn=fallback_should_not_run,
    )
    assert result.path == "agent"
    assert result.answer == "agent answer"
