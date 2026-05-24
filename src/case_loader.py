"""Load and validate RTL benchmark cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FILES = {
    "design_buggy.sv": "buggy_rtl",
    "design_fixed.sv": "fixed_rtl",
    "tb.sv": "testbench",
    "spec.md": "spec",
    "expected_root_cause.md": "expected_root_cause",
    "ground_truth.json": "ground_truth",
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _validate_ground_truth(ground_truth: dict[str, Any], case_name: str) -> None:
    if ground_truth.get("case_name") != case_name:
        msg = (
            f"ground_truth.case_name '{ground_truth.get('case_name')}' "
            f"does not match directory name '{case_name}'"
        )
        raise ValueError(msg)

    suspicious_signals = ground_truth.get("suspicious_signals")
    if not isinstance(suspicious_signals, list) or not suspicious_signals:
        raise ValueError("ground_truth.suspicious_signals must be a non-empty list")

    regions = ground_truth.get("suspicious_regions")
    if not isinstance(regions, list) or not regions:
        raise ValueError("ground_truth.suspicious_regions must be a non-empty list")

    for region in regions:
        if not isinstance(region, dict):
            raise ValueError("Each suspicious region must be an object")
        for key in ("file", "start_line", "end_line", "description"):
            if key not in region:
                raise ValueError(f"suspicious region missing required field: {key}")
        if region["start_line"] > region["end_line"]:
            raise ValueError("suspicious region start_line must be <= end_line")


def load_case(case_path: str | Path) -> dict[str, Any]:
    """Load a benchmark case directory and return structured case data."""
    case_dir = Path(case_path)
    if not case_dir.is_dir():
        raise FileNotFoundError(f"Case directory not found: {case_dir}")

    case_name = case_dir.name
    case_path_str = str(case_dir).replace("\\", "/")

    contents: dict[str, str] = {}

    for filename, content_key in REQUIRED_FILES.items():
        file_path = case_dir / filename
        if not file_path.is_file():
            msg = f"[ERROR] Required benchmark file is missing: {case_path_str}/{filename}"
            raise FileNotFoundError(msg)
        if filename != "ground_truth.json":
            contents[content_key] = _read_text(file_path)

    ground_truth_path = case_dir / "ground_truth.json"
    try:
        ground_truth = json.loads(_read_text(ground_truth_path))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in ground_truth.json: {exc}") from exc

    if not isinstance(ground_truth, dict):
        raise ValueError("ground_truth.json must contain a JSON object")

    _validate_ground_truth(ground_truth, case_name)

    file_paths = {
        "buggy_rtl_path": f"{case_path_str}/design_buggy.sv",
        "fixed_rtl_path": f"{case_path_str}/design_fixed.sv",
        "testbench_path": f"{case_path_str}/tb.sv",
        "spec_path": f"{case_path_str}/spec.md",
        "expected_root_cause_path": f"{case_path_str}/expected_root_cause.md",
        "ground_truth_path": f"{case_path_str}/ground_truth.json",
    }

    return {
        "case_name": case_name,
        "case_path": case_path_str,
        "files": file_paths,
        "buggy_rtl": contents["buggy_rtl"],
        "fixed_rtl": contents["fixed_rtl"],
        "testbench": contents["testbench"],
        "spec": contents["spec"],
        "expected_root_cause": contents["expected_root_cause"],
        "ground_truth": ground_truth,
    }
