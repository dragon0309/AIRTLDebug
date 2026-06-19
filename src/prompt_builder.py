"""Build LLM prompts from AIRTLDebug intermediate data."""

from __future__ import annotations

from typing import Any


def _filter_signals(signals: list[str]) -> list[str]:
    ignored = {
        "d0",
        "b0",
        "b1",
        "Bug",
        "asserted",
        "when",
        "reaches",
        "instead",
        "of",
    }
    return [sig for sig in signals if sig not in ignored]


def _format_blocks(blocks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in blocks:
        parts.append(
            f"File: {block['file']}\n"
            f"Lines: {block['start_line']}-{block['end_line']}\n"
            f"Type: {block['type']}\n"
            "Code:\n"
            "```systemverilog\n"
            f"{block['code']}\n"
            "```"
        )
    return "\n\n".join(parts)


def build_full_flow_prompt(intermediate: dict[str, Any]) -> str:
    """Build the full AIRTLDebug prompt using simulation evidence and RTL context."""
    parsed = intermediate["parsed_failure"]
    context = intermediate["extracted_context"]

    suspicious_signals = ", ".join(
    _filter_signals(context.get("suspicious_signals", []))
    )
    suspicious_blocks = _format_blocks(context.get("suspicious_code_blocks", []))

    return f"""You are an RTL debugging assistant.

You are given:
1. Design specification
2. Parsed simulation failure
3. Suspicious signals
4. Extracted RTL code blocks

Task:
Find the most likely root cause of the RTL bug.

Rules:
- Base your answer only on the given RTL code and simulation evidence.
- Do not invent signals that do not exist.
- If the evidence is insufficient, state what is missing.
- Explain why the failure happens.
- Explain how the suggested fix addresses the failure.

Required output format:
Return ONLY a valid JSON object with the following keys:
{{
  "bug_summary": "...",
  "suspicious_signals": ["..."],
  "suspicious_regions": ["..."],
  "root_cause": "...",
  "suggested_fix": "...",
  "evidence": "...",
  "confidence_score": "..."
}}
Do not wrap the JSON in Markdown code fences.

# Design Specification

{intermediate["spec"]}

# Parsed Simulation Failure

- Status: {parsed.get("status")}
- Failure cycle: {parsed.get("failure_cycle")}
- Failed signal: {parsed.get("failed_signal")}
- Expected: {parsed.get("expected")}
- Actual: {parsed.get("actual")}
- Message: {parsed.get("message")}
- Raw failure line: {parsed.get("raw_failure_line")}

# Suspicious Signals

{suspicious_signals}

# Extracted RTL Code Blocks

{suspicious_blocks}
"""
