"""Tool result formatting / hollow-answer enrichment."""

from __future__ import annotations

from app.bedrock.runner import ToolRunResult
from app.bedrock.tool_payload import (
    MAX_PREVIEW_ROWS,
    build_success_payload,
    enrich_answer_if_needed,
)


def test_build_success_payload_caps_rows() -> None:
    rows = [{"policy_id": f"P{i}"} for i in range(25)]
    result = ToolRunResult(
        concept="coverage_by_type",
        role="agent",
        rows=rows,
        row_count=25,
        sql="SELECT 1",
        params={"coverage_type": "windshield"},
    )
    payload = build_success_payload(result)
    assert payload["row_count"] == 25
    assert len(payload["rows"]) == MAX_PREVIEW_ROWS
    assert payload["truncated"] is True
    assert "P0" in payload["formatted_preview"]
    assert "instruction" in payload


def test_enrich_appends_when_answer_is_hollow() -> None:
    payload = {
        "rows": [{"policy_id": "P1001", "full_name": "John Smith"}],
        "formatted_preview": "1. policy_id=P1001, full_name=John Smith",
        "note": "Showing first 10 of 22 rows.",
    }
    answer = enrich_answer_if_needed(
        "Here are the policies that cover windshield damage:",
        payload,
    )
    assert "P1001" in answer
    assert "John Smith" in answer
    assert "Showing first 10 of 22 rows." in answer


def test_enrich_keeps_good_answer() -> None:
    payload = {
        "rows": [{"policy_id": "P1001"}],
        "formatted_preview": "1. policy_id=P1001",
    }
    original = "Policy P1001 includes windshield coverage."
    assert enrich_answer_if_needed(original, payload) == original
