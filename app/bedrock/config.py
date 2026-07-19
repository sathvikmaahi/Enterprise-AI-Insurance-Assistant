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
