"""Audit log listing for the demo panel."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth import CurrentUser, get_current_user
from app.logging.audit import list_recent

router = APIRouter(tags=["logs"])


@router.get("/logs")
def get_logs(
    limit: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
) -> dict[str, Any]:
    _ = user  # auth required; any demo role may read
    entries = [e.to_dict() for e in list_recent(limit)]
    return {"count": len(entries), "entries": entries}
