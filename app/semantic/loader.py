"""Load and validate YAML concept definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.semantic.models import ConceptDef, ParamDef

DEFAULT_CONCEPTS_DIR = Path(__file__).resolve().parent / "concepts"


class ConceptLoadError(ValueError):
    """Raised when a concept YAML file is missing or invalid."""


def _parse_params(raw: Any, concept_name: str) -> tuple[ParamDef, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ConceptLoadError(f"{concept_name}: params must be a list")
    params: list[ParamDef] = []
    for item in raw:
        if not isinstance(item, dict) or "name" not in item:
            raise ConceptLoadError(f"{concept_name}: each param needs a name")
        params.append(
            ParamDef(
                name=str(item["name"]),
                required=bool(item.get("required", True)),
                type=str(item.get("type", "string")),
            )
        )
    return tuple(params)


def _parse_concept(data: dict[str, Any], source: Path) -> ConceptDef:
    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ConceptLoadError(f"{source.name}: missing string 'name'")

    sql = data.get("sql")
    if not sql or not isinstance(sql, str) or not sql.strip():
        raise ConceptLoadError(f"{name}: missing 'sql' template")

    description = data.get("description", "")
    if not isinstance(description, str):
        raise ConceptLoadError(f"{name}: description must be a string")

    require_one_of_raw = data.get("require_one_of") or []
    if not isinstance(require_one_of_raw, list):
        raise ConceptLoadError(f"{name}: require_one_of must be a list")

    allowed = data.get("allowed_roles") or []
    fields = data.get("response_fields") or []
    if not isinstance(allowed, list) or not isinstance(fields, list):
        raise ConceptLoadError(f"{name}: allowed_roles and response_fields must be lists")

    result_mode = str(data.get("result_mode", "many"))
    if result_mode not in ("many", "one"):
        raise ConceptLoadError(f"{name}: result_mode must be 'many' or 'one'")

    return ConceptDef(
        name=name,
        description=description,
        sql=sql.strip(),
        params=_parse_params(data.get("params"), name),
        require_one_of=tuple(str(x) for x in require_one_of_raw),
        allowed_roles=tuple(str(x) for x in allowed),
        response_fields=tuple(str(x) for x in fields),
        result_mode=result_mode,
    )


def load_concepts(directory: Path | None = None) -> dict[str, ConceptDef]:
    """Load all ``*.yaml`` concept files from *directory*."""
    concepts_dir = directory or DEFAULT_CONCEPTS_DIR
    if not concepts_dir.is_dir():
        raise ConceptLoadError(f"Concepts directory not found: {concepts_dir}")

    concepts: dict[str, ConceptDef] = {}
    for path in sorted(concepts_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ConceptLoadError(f"{path.name}: invalid YAML: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConceptLoadError(f"{path.name}: root must be a mapping")

        concept = _parse_concept(raw, path)
        if concept.name in concepts:
            raise ConceptLoadError(f"Duplicate concept name: {concept.name}")
        concepts[concept.name] = concept

    if not concepts:
        raise ConceptLoadError(f"No concept YAML files in {concepts_dir}")

    return concepts
