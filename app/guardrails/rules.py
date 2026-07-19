"""Keyword / regex guardrails for free-text questions."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None


_DESTRUCTIVE = re.compile(
    r"\b(delete|drop\s+table|truncate|update\s+\w+\s+set)\b",
    re.IGNORECASE,
)
_RAW_SQL = re.compile(
    r"(select\s+\*\s+from\b|;--|/\*|\bunion\s+select\b)",
    re.IGNORECASE,
)
_PII_DUMP = re.compile(
    r"("
    r"all\s+customers\s+with\s+(email|ssn|social)"
    r"|dump\s+all\s+(emails|ssns|customers)"
    r"|show\s+all\s+(emails|ssns)"
    r"|everyone'?s\s+(email|ssn)"
    r")",
    re.IGNORECASE,
)
_OFF_DOMAIN = re.compile(
    r"("
    r"\bstock(s)?\b|\bticker\b|\bnasdaq\b|\bbitcoin\b|\bcrypto\b"
    r"|\bmedical\s+advice\b|\bdiagnos(e|is)\b|\bprescribe\b"
    r"|\brecipe\b|\bweather\b"
    r")",
    re.IGNORECASE,
)


def check_question(text: str) -> GuardrailResult:
    """Return whether free-text is allowed; reason set when blocked."""
    if not text or not text.strip():
        return GuardrailResult(allowed=True)

    if _DESTRUCTIVE.search(text):
        return GuardrailResult(allowed=False, reason="Destructive intent is not allowed")
    if _RAW_SQL.search(text):
        return GuardrailResult(allowed=False, reason="Raw SQL is not allowed")
    if _PII_DUMP.search(text):
        return GuardrailResult(allowed=False, reason="Over-broad PII request is not allowed")
    if _OFF_DOMAIN.search(text):
        return GuardrailResult(allowed=False, reason="Off-domain question is not allowed")

    return GuardrailResult(allowed=True)
