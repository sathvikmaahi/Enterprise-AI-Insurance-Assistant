"""Build Bedrock Converse tool specs from semantic concept YAML."""

from __future__ import annotations

from typing import Any

from app.semantic import get_concepts
from app.semantic.models import ConceptDef


def _param_schema(concept: ConceptDef) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param in concept.params:
        properties[param.name] = {
            "type": "string" if param.type == "string" else param.type,
            "description": f"Parameter {param.name} for {concept.name}",
        }
        if param.required:
            required.append(param.name)

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    if concept.require_one_of:
        schema["description"] = (
            f"{concept.description} "
            f"Provide at least one of: {', '.join(concept.require_one_of)}."
        )
    return schema


def converse_tool_config() -> dict[str, Any]:
    """ToolConfig payload for bedrock-runtime converse()."""
    tools: list[dict[str, Any]] = []
    for concept in get_concepts().values():
        description = concept.description
        if concept.require_one_of:
            description = (
                f"{description} "
                f"Provide at least one of: {', '.join(concept.require_one_of)}."
            )
        tools.append(
            {
                "toolSpec": {
                    "name": concept.name,
                    "description": description,
                    "inputSchema": {"json": _param_schema(concept)},
                }
            }
        )
    return {"tools": tools}


def known_tool_names() -> set[str]:
    return set(get_concepts().keys())
