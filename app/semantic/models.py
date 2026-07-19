"""Typed shapes for semantic concept definitions and resolve results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParamDef:
    name: str
    required: bool = True
    type: str = "string"


@dataclass(frozen=True)
class ConceptDef:
    name: str
    description: str
    sql: str
    params: tuple[ParamDef, ...] = ()
    require_one_of: tuple[str, ...] = ()
    allowed_roles: tuple[str, ...] = ()
    response_fields: tuple[str, ...] = ()
    result_mode: str = "many"  # "many" | "one"


@dataclass
class ResolveResult:
    concept: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    sql: str = ""
    params: dict[str, Any] = field(default_factory=dict)
