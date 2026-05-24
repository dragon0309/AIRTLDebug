"""Parse simulation logs for PASS/FAIL results."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PASS_MARKER = "[PASS] all checks passed"
FAIL_PATTERN = re.compile(
    r"^\[FAIL\]\s+cycle=(\d+)\s+signal=([A-Za-z_][A-Za-z0-9_$]*)\s+"
    r"expected=([^\s]+)\s+actual=([^\s]+)\s+message=\"(.*)\"\s*$",
    re.MULTILINE,
)
FAIL_LINE_PATTERN = re.compile(r"^\[FAIL\].*$", re.MULTILINE)


def _empty_failure_fields() -> dict[str, Any]:
    return {
        "failure_cycle": None,
        "failed_signal": None,
        "expected": None,
        "actual": None,
        "message": None,
        "raw_failure_line": None,
    }


def parse_simulation_log(log_text: str) -> dict[str, Any]:
    """Parse simulation log text into structured failure information."""
    text = log_text or ""
    all_failure_lines = FAIL_LINE_PATTERN.findall(text)

    if PASS_MARKER in text:
        return {
            "status": "PASS",
            "failure_cycle": None,
            "failed_signal": None,
            "expected": None,
            "actual": None,
            "message": "all checks passed",
            "raw_failure_line": None,
            "all_failure_lines": all_failure_lines,
        }

    match = FAIL_PATTERN.search(text)
    if match:
        return {
            "status": "FAIL",
            "failure_cycle": int(match.group(1)),
            "failed_signal": match.group(2),
            "expected": match.group(3),
            "actual": match.group(4),
            "message": match.group(5),
            "raw_failure_line": match.group(0),
            "all_failure_lines": all_failure_lines,
        }

    if "[FAIL]" in text or all_failure_lines:
        raw_line = all_failure_lines[0] if all_failure_lines else None
        return {
            "status": "FAIL",
            **_empty_failure_fields(),
            "message": "Simulation failed, but no structured failure message was found.",
            "raw_failure_line": raw_line,
            "all_failure_lines": all_failure_lines,
        }

    if not text.strip():
        return {
            "status": "UNKNOWN",
            **_empty_failure_fields(),
            "message": "Log is empty.",
            "all_failure_lines": [],
        }

    return {
        "status": "FAIL",
        **_empty_failure_fields(),
        "message": "Simulation failed, but no structured failure message was found.",
        "all_failure_lines": all_failure_lines,
    }


def parse_simulation_log_file(log_path: str | Path) -> dict[str, Any]:
    """Parse a simulation log file."""
    path = Path(log_path)
    return parse_simulation_log(path.read_text(encoding="utf-8"))
