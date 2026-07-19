"""Role-based access control for semantic concepts."""

from app.rbac.check import AccessDeniedError, assert_allowed

__all__ = ["AccessDeniedError", "assert_allowed"]
