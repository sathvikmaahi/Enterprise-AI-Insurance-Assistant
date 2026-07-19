"""HMAC-signed demo session tokens (stdlib only — no JWT dependency)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

TOKEN_TTL_SECONDS = 8 * 60 * 60  # 8 hours


class TokenError(ValueError):
    """Raised when a token is missing, malformed, forged, or expired."""


@dataclass(frozen=True)
class TokenPayload:
    username: str
    role: str
    exp: int


def _secret() -> bytes:
    secret = os.getenv("DEMO_AUTH_SECRET", "").strip()
    if not secret:
        secret = "change-me-in-local-dev"
    return secret.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def issue_token(username: str, role: str, *, ttl_seconds: int = TOKEN_TTL_SECONDS) -> str:
    """Create a signed token: base64url(payload).base64url(signature)."""
    payload = {
        "username": username,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(signature)}"


def verify_token(token: str) -> TokenPayload:
    """Verify signature and expiry; return payload or raise TokenError."""
    try:
        body, sig = token.split(".", 1)
    except ValueError as exc:
        raise TokenError("Malformed token") from exc

    expected = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
    try:
        provided = _b64url_decode(sig)
    except Exception as exc:  # noqa: BLE001 — treat any decode failure as invalid
        raise TokenError("Malformed token signature") from exc

    if not hmac.compare_digest(expected, provided):
        raise TokenError("Invalid token signature")

    try:
        data = json.loads(_b64url_decode(body))
        payload = TokenPayload(
            username=str(data["username"]),
            role=str(data["role"]),
            exp=int(data["exp"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise TokenError("Malformed token payload") from exc

    if payload.exp < int(time.time()):
        raise TokenError("Token expired")

    return payload
