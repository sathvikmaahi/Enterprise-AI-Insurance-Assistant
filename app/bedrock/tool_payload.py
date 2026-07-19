"""Format semantic tool results for Bedrock Agent / Converse."""

from __future__ import annotations

from typing import Any

from app.bedrock.runner import ToolRunResult

MAX_PREVIEW_ROWS = 10

_ID_KEYS = (
    "policy_id",
    "claim_id",
    "coverage_id",
    "full_name",
    "customer_id",
    "premium_amount",
)


def format_rows_for_display(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(no rows)"
    lines: list[str] = []
    for index, row in enumerate(rows, start=1):
        parts = [f"{key}={value}" for key, value in row.items()]
        lines.append(f"{index}. " + ", ".join(parts))
    return "\n".join(lines)


def build_success_payload(result: ToolRunResult) -> dict[str, Any]:
    """Cap rows and add a readable preview so the model lists facts, not just a header."""
    preview = list(result.rows[:MAX_PREVIEW_ROWS])
    payload: dict[str, Any] = {
        "concept": result.concept,
        "row_count": result.row_count,
        "rows": preview,
        "formatted_preview": format_rows_for_display(preview),
        "instruction": (
            "Your final answer MUST include the concrete values from "
            "formatted_preview (policy IDs, amounts, names). Do not stop at a header."
        ),
    }
    if result.row_count > MAX_PREVIEW_ROWS:
        payload["truncated"] = True
        payload["note"] = (
            f"Showing first {MAX_PREVIEW_ROWS} of {result.row_count} rows."
        )
    return payload


def enrich_answer_if_needed(answer: str, last_payload: dict[str, Any] | None) -> str:
    """If the model returned a hollow intro, append the formatted preview."""
    if not last_payload or last_payload.get("error"):
        return answer

    rows = last_payload.get("rows") or []
    formatted = (last_payload.get("formatted_preview") or "").strip()
    if not rows or not formatted:
        return answer

    sample_values = [
        str(row[key])
        for row in rows[:5]
        for key in _ID_KEYS
        if key in row and row[key] is not None
    ]
    stripped = (answer or "").strip()
    has_data = any(value and value in stripped for value in sample_values)
    hollow = (not stripped) or stripped.endswith(":") or not has_data
    if not hollow:
        return answer

    note = last_payload.get("note")
    block = formatted if not note else f"{formatted}\n({note})"
    if not stripped:
        return f"Here are the results:\n{block}"
    if stripped.endswith(":"):
        return f"{stripped}\n{block}"
    return f"{stripped}\n\n{block}"
