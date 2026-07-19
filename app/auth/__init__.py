"""Demo authentication (Cognito-compatible stand-in)."""

from app.auth.deps import CurrentUser, get_current_user
from app.auth.tokens import TokenError, issue_token, verify_token
from app.auth.users import DemoUser, authenticate

__all__ = [
    "CurrentUser",
    "DemoUser",
    "TokenError",
    "authenticate",
    "get_current_user",
    "issue_token",
    "verify_token",
]
