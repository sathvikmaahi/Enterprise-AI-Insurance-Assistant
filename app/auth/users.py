"""Hardcoded demo users for the POC (Cognito stand-in)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoUser:
    username: str
    password: str
    role: str


DEMO_USERS: dict[str, DemoUser] = {
    "agent": DemoUser(username="agent", password="agent123", role="agent"),
    "adjuster": DemoUser(username="adjuster", password="adjuster123", role="adjuster"),
    "manager": DemoUser(username="manager", password="manager123", role="manager"),
}


def authenticate(username: str, password: str) -> DemoUser | None:
    """Return the demo user if credentials match, else None."""
    user = DEMO_USERS.get(username)
    if user is None or user.password != password:
        return None
    return user
