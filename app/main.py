"""FastAPI entrypoint for the Enterprise AI Insurance Assistant POC."""

from fastapi import FastAPI

from app.db import check_db

app = FastAPI(
    title="Enterprise AI Insurance Assistant",
    description="POC: React · FastAPI · Bedrock Agent · Semantic Layer · PostgreSQL",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness + DB connectivity for local demos."""
    payload: dict[str, str] = {"status": "ok"}
    payload.update(check_db())
    return payload
