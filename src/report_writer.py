"""Write Markdown debug reports for AIRTLDebug."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _make_code_fence(language: str, code: str) -> str:
    fence = "```"
    return f"{fence}{language}\n{code}\n{fence}"


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


def write_debug_report(
    intermediate: dict[str, Any],
    llm_analysis: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Write a Markdown debug report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    parsed = intermediate["parsed_failure"]
    context = intermediate["extracted_context"]
    fix = intermediate["fix_verification"]
    gt = intermediate["ground_truth"]

    blocks_md: list[str] = []
    for block in context.get("suspicious_code_blocks", []):
        block_md = (
            f"### {block['file']}:{block['start_line']}-{block['end_line']}\n\n"
            f"Type: `{block['type']}`\n\n"
            f"{_make_code_fence('systemverilog', block['code'])}"
        )
        blocks_md.append(block_md)

    clean_signals = _filter_signals(context.get("suspicious_signals", []))
    suspicious_signals_md = "\n".join(f"- `{sig}`" for sig in clean_signals)
    suspicious_blocks_md = "\n\n".join(blocks_md)
    failure_evidence = _make_code_fence("text", str(parsed.get("raw_failure_line")))

    content = f"""# Debug Report: {intermediate["case_name"]}

## 1. Simulation Result

- Buggy RTL simulation: {intermediate["simulation"]["buggy"]["status"]}
- Failure cycle: {parsed.get("failure_cycle")}
- Failed signal: `{parsed.get("failed_signal")}`
- Expected: `{parsed.get("expected")}`
- Actual: `{parsed.get("actual")}`
- Message: {parsed.get("message")}

## 2. Failure Evidence

{failure_evidence}

## 3. Extracted RTL Context

### Suspicious Signals

{suspicious_signals_md}

### Suspicious RTL Blocks

{suspicious_blocks_md}

## 4. LLM Root Cause Analysis

- Bug summary: {llm_analysis.get("bug_summary")}
- Root cause: {llm_analysis.get("root_cause")}
- Evidence: {llm_analysis.get("evidence")}
- Confidence score: {llm_analysis.get("confidence_score")}

## 5. Suggested Fix

{llm_analysis.get("suggested_fix")}

## 6. Fix Verification

- Enabled: {fix.get("enabled")}
- Fixed RTL simulation: {fix.get("status")}

## 7. Comparison with Ground Truth

- Ground-truth root cause: {gt.get("root_cause")}
- Ground-truth suspicious signals: {", ".join(gt.get("suspicious_signals", []))}
- Ground-truth expected fix: {gt.get("expected_fix")}
"""

    path.write_text(content, encoding="utf-8")
    return path