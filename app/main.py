"""FastAPI entrypoint for the Enterprise AI Insurance Assistant POC."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ask_router, auth_router, logs_router, tools_router
from app.db import check_db

app = FastAPI(
    title="Enterprise AI Insurance Assistant",
    description="POC: React · FastAPI · Bedrock Agent · Semantic Layer · PostgreSQL",
    version="0.1.0",
)

# Local Vite dev server talks to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ask_router)
app.include_router(tools_router)
app.include_router(logs_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness + DB connectivity for local demos."""
    payload: dict[str, str] = {"status": "ok"}
    payload.update(check_db())
    return payload
