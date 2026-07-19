"""FastAPI entrypoint for the Enterprise AI Insurance Assistant POC."""

from fastapi import FastAPI

app = FastAPI(
    title="Enterprise AI Insurance Assistant",
    description="POC: React · FastAPI · Bedrock Agent · Semantic Layer · PostgreSQL",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check for local demos."""
    return {"status": "ok"}
