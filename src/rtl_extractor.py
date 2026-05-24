"""Extract relevant RTL context around failure signals."""

from __future__ import annotations

import re
from typing import Any

KEYWORDS = {
    "module",
    "endmodule",
    "input",
    "output",
    "wire",
    "logic",
    "reg",
    "always",
    "always_ff",
    "always_comb",
    "assign",
    "begin",
    "end",
    "if",
    "else",
    "case",
    "endcase",
    "default",
    "posedge",
    "negedge",
    "parameter",
    "localparam",
}

IDENTIFIER_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_$]*)\b")
ASSIGN_PATTERN = re.compile(r"^\s*assign\s+")
SKIP_LINE_PATTERN = re.compile(
    r"^\s*(module|endmodule|input|output|inout|wire|logic|reg)\b"
)


def find_signal_occurrences(lines: list[str], signal: str) -> list[int]:
    """Return 1-based line numbers where signal appears."""
    pattern = re.compile(rf"\b{re.escape(signal)}\b")
    occurrences: list[int] = []
    for idx, line in enumerate(lines):
        if SKIP_LINE_PATTERN.match(line):
            continue
        if pattern.search(line):
            occurrences.append(idx + 1)
    return occurrences


def infer_block_type(block_text: str) -> str:
    """Classify an RTL block by its leading construct."""
    stripped = block_text.lstrip()
    if stripped.startswith("always_ff"):
        return "sequential_always"
    if re.match(r"always\s*@\(\s*(posedge|negedge)", stripped):
        return "sequential_always"
    if stripped.startswith("always_comb"):
        return "combinational_always"
    if re.match(r"always\s*@\(\*\)", stripped):
        return "combinational_always"
    if ASSIGN_PATTERN.match(stripped):
        return "assign"
    if re.search(r"\bcase\b", stripped):
        return "case"
    return "context_window"


def _find_block_start(lines: list[str], line_index: int) -> int:
    """Find the start line index (0-based) for an enclosing block."""
    for idx in range(line_index, -1, -1):
        line = lines[idx]
        if re.search(r"\balways\b", line):
            return idx
        if ASSIGN_PATTERN.match(line):
            return idx
        if re.match(r"^\s*case\b", line):
            return idx
    return max(0, line_index - 2)


def _extract_with_nesting(lines: list[str], start_idx: int) -> tuple[int, int]:
    """Extract block end using begin/end nesting from start_idx."""
    if start_idx >= len(lines):
        return start_idx, start_idx

    first_line = lines[start_idx]
    if "begin" not in first_line.lower():
        end_idx = start_idx
        while end_idx + 1 < len(lines):
            next_line = lines[end_idx + 1]
            if re.match(r"^\s*(always|assign|case|endmodule)\b", next_line):
                break
            if next_line.strip() == "":
                end_idx += 1
                continue
            if re.match(r"^\s*//", next_line):
                end_idx += 1
                continue
            if not next_line.startswith(" ") and not next_line.startswith("\t"):
                break
            end_idx += 1
        return start_idx, end_idx

    nesting = 0
    end_idx = start_idx
    for idx in range(start_idx, len(lines)):
        line = lines[idx]
        nesting += len(re.findall(r"\bbegin\b", line))
        nesting -= len(re.findall(r"\bend\b", line))
        end_idx = idx
        if idx > start_idx and nesting <= 0:
            break
    return start_idx, end_idx


def extract_enclosing_block(lines: list[str], line_index: int) -> dict[str, Any]:
    """Extract the smallest useful enclosing block around a line."""
    zero_index = max(0, min(line_index - 1, len(lines) - 1))
    start_idx = _find_block_start(lines, zero_index)
    start_idx, end_idx = _extract_with_nesting(lines, start_idx)
    code = "\n".join(lines[start_idx : end_idx + 1])
    return {
        "start_line": start_idx + 1,
        "end_line": end_idx + 1,
        "code": code,
        "type": infer_block_type(code),
    }


def _signals_in_text(text: str) -> list[str]:
    found: list[str] = []
    for match in IDENTIFIER_PATTERN.finditer(text):
        name = match.group(1)
        if name not in KEYWORDS and name not in found:
            found.append(name)
    return found


def collect_suspicious_signals(rtl_text: str, parsed_failure: dict[str, Any]) -> list[str]:
    """Collect suspicious signal names using priority heuristics."""
    failed_signal = parsed_failure.get("failed_signal")
    signals: list[str] = []
    if failed_signal:
        signals.append(failed_signal)

    lines = rtl_text.splitlines()
    if failed_signal:
        for line_no in find_signal_occurrences(lines, failed_signal):
            block = extract_enclosing_block(lines, line_no)
            for name in _signals_in_text(block["code"]):
                if name not in signals:
                    signals.append(name)
    return signals


def extract_context(
    rtl_text: str,
    parsed_failure: dict[str, Any],
    file_name: str = "design_buggy.sv",
) -> dict[str, Any]:
    """Extract suspicious signals and code blocks from RTL text."""
    warnings: list[str] = []
    failed_signal = parsed_failure.get("failed_signal")
    lines = rtl_text.splitlines()
    blocks: list[dict[str, Any]] = []

    if not failed_signal:
        warnings.append("failed_signal is null; no blocks extracted")
        return {
            "suspicious_signals": [],
            "suspicious_code_blocks": [],
            "extraction_warnings": warnings,
        }

    occurrences = find_signal_occurrences(lines, failed_signal)
    if not occurrences:
        warnings.append(f"signal '{failed_signal}' not found in RTL")
        return {
            "suspicious_signals": [failed_signal],
            "suspicious_code_blocks": [],
            "extraction_warnings": warnings,
        }

    seen: set[tuple[str, int, int, str]] = set()
    for line_no in occurrences:
        block = extract_enclosing_block(lines, line_no)
        key = (file_name, block["start_line"], block["end_line"], block["type"])
        matched_signals = _signals_in_text(block["code"])
        if failed_signal not in matched_signals:
            matched_signals.insert(0, failed_signal)

        if key in seen:
            for existing in blocks:
                if (
                    existing["file"] == file_name
                    and existing["start_line"] == block["start_line"]
                    and existing["end_line"] == block["end_line"]
                    and existing["type"] == block["type"]
                ):
                    for sig in matched_signals:
                        if sig not in existing["matched_signals"]:
                            existing["matched_signals"].append(sig)
            continue

        seen.add(key)
        blocks.append(
            {
                "type": block["type"],
                "file": file_name,
                "start_line": block["start_line"],
                "end_line": block["end_line"],
                "code": block["code"],
                "matched_signals": matched_signals,
            }
        )

    suspicious_signals = collect_suspicious_signals(rtl_text, parsed_failure)
    return {
        "suspicious_signals": suspicious_signals,
        "suspicious_code_blocks": blocks,
        "extraction_warnings": warnings,
    }
