"""Mock LLM backend."""

from __future__ import annotations

from typing import Any


def run_llm_analysis(
    intermediate: dict[str, Any],
    *,
    model: str = "mock",
) -> dict[str, Any]:
    """Return a mock LLM analysis."""

    parsed = intermediate["parsed_failure"]
    gt = intermediate["ground_truth"]

    return {
        "bug_summary":
            f"Signal {parsed['failed_signal']} mismatches at cycle "
            f"{parsed['failure_cycle']}.",

        "root_cause":
            gt["root_cause"],

        "evidence":
            parsed["raw_failure_line"],

        "suggested_fix":
            gt["expected_fix"],

        "confidence_score":
            "High",
    }