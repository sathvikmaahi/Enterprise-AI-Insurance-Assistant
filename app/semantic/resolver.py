"""Resolve business concepts to parameterized SQL results."""

from __future__ import annotations

from typing import Any

from app.db import fetch_all, fetch_one
from app.semantic.loader import DEFAULT_CONCEPTS_DIR, load_concepts
from app.semantic.models import ConceptDef, ResolveResult

_concepts_cache: dict[str, ConceptDef] | None = None


class ConceptNotFoundError(KeyError):
    """Raised when the requested concept name is not defined."""


class MissingParameterError(ValueError):
    """Raised when required concept parameters are missing."""


def get_concepts(*, reload: bool = False) -> dict[str, ConceptDef]:
    """Return loaded concepts (cached after first load)."""
    global _concepts_cache
    if _concepts_cache is None or reload:
        _concepts_cache = load_concepts(DEFAULT_CONCEPTS_DIR)
    return _concepts_cache


def clear_concepts_cache() -> None:
    """Reset concept cache (tests)."""
    global _concepts_cache
    _concepts_cache = None


def _bind_params(concept: ConceptDef, params: dict[str, Any]) -> dict[str, Any]:
    bound: dict[str, Any] = {}

    for param in concept.params:
        value = params.get(param.name)
        if value is None or (isinstance(value, str) and not value.strip()):
            if param.required:
                raise MissingParameterError(
                    f"Concept '{concept.name}' requires parameter '{param.name}'"
                )
            bound[param.name] = None
        else:
            bound[param.name] = value.strip() if isinstance(value, str) else value

    if concept.require_one_of:
        if not any(bound.get(name) is not None for name in concept.require_one_of):
            names = " or ".join(concept.require_one_of)
            raise MissingParameterError(
                f"Concept '{concept.name}' requires one of: {names}"
            )

    # Ensure every placeholder name used by require_one_of exists in the bind dict
    for name in concept.require_one_of:
        bound.setdefault(name, None)

    return bound


def _shape_rows(concept: ConceptDef, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not concept.response_fields:
        return rows
    shaped: list[dict[str, Any]] = []
    for row in rows:
        shaped.append({field: row.get(field) for field in concept.response_fields})
    return shaped


def resolve(concept_name: str, params: dict[str, Any] | None = None) -> ResolveResult:
    """
    Resolve a named business concept to database rows.

    SQL comes only from the approved YAML template. Parameters are bound
    separately (never concatenated into the SQL string).
    """
    concepts = get_concepts()
    concept = concepts.get(concept_name)
    if concept is None:
        raise ConceptNotFoundError(f"Unknown concept: {concept_name}")

    bound = _bind_params(concept, params or {})

    if concept.result_mode == "one":
        row = fetch_one(concept.sql, bound)
        rows = [row] if row is not None else []
    else:
        rows = fetch_all(concept.sql, bound)

    return ResolveResult(
        concept=concept.name,
        rows=_shape_rows(concept, rows),
        sql=concept.sql,
        params=bound,
    )
