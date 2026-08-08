"""Demo auth: login + HMAC tokens."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.auth.tokens import TokenError, issue_token, verify_token
from app.main import app

client = TestClient(app)


def test_issue_and_verify_token_roundtrip() -> None:
    token = issue_token("csr", "csr")
    payload = verify_token(token)
    assert payload.username == "csr"
    assert payload.role == "csr"
    assert payload.exp > int(time.time())


def test_verify_rejects_tampered_token() -> None:
    token = issue_token("csr", "csr")
    body, sig = token.split(".", 1)
    tampered = f"{body}x.{sig}"
    with pytest.raises(TokenError):
        verify_token(tampered)


def test_verify_rejects_expired_token() -> None:
    token = issue_token("csr", "csr", ttl_seconds=-1)
    with pytest.raises(TokenError, match="expired"):
        verify_token(token)


def test_login_success() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "csr", "password": "csr123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "csr"
    assert body["username"] == "csr"
    assert body["access_token"]


def test_login_invalid_credentials() -> None:
    response = client.post(
        "/auth/login",
        json={"username": "csr", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]
