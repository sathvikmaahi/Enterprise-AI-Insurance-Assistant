"""Bedrock-related environment configuration."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def aws_region() -> str:
    return os.getenv("AWS_REGION", "us-east-1").strip() or "us-east-1"


def agent_id() -> str:
    return os.getenv("BEDROCK_AGENT_ID", "").strip()


def agent_alias_id() -> str:
    return os.getenv("BEDROCK_AGENT_ALIAS_ID", "").strip()


def fallback_model_id() -> str:
    return os.getenv("BEDROCK_FALLBACK_MODEL_ID", "").strip()


def force_fallback() -> bool:
    return os.getenv("BEDROCK_FORCE_FALLBACK", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def agent_configured() -> bool:
    return bool(agent_id() and agent_alias_id())


def fallback_configured() -> bool:
    return bool(fallback_model_id())


def guardrail_id() -> str:
    return os.getenv("BEDROCK_GUARDRAIL_ID", "").strip()


def guardrail_version() -> str:
    return os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT").strip() or "DRAFT"


def guardrail_configured() -> bool:
    return bool(guardrail_id())


def guardrail_config_dict() -> dict[str, str] | None:
    """Return Converse guardrailConfig when env is set."""
    if not guardrail_configured():
        return None
    return {
        "guardrailIdentifier": guardrail_id(),
        "guardrailVersion": guardrail_version(),
    }
