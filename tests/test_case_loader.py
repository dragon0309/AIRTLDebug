"""Tests for case_loader module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.case_loader import load_case

CASE_DIR = Path("benchmarks/counter_off_by_one")


def test_load_valid_case() -> None:
    data = load_case(CASE_DIR)
    assert data["case_name"] == "counter_off_by_one"
    assert "buggy_rtl" in data
    assert "ground_truth" in data
    assert data["files"]["buggy_rtl_path"].endswith("design_buggy.sv")


def test_missing_required_file(tmp_path: Path) -> None:
    case_dir = tmp_path / "broken_case"
    case_dir.mkdir()
    (case_dir / "ground_truth.json").write_text(
        json.dumps(
            {
                "case_name": "broken_case",
                "bug_type": "x",
                "root_cause": "x",
                "suspicious_signals": ["a"],
                "suspicious_regions": [
                    {
                        "file": "design_buggy.sv",
                        "start_line": 1,
                        "end_line": 2,
                        "description": "x",
                    }
                ],
                "expected_fix": "x",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FileNotFoundError, match="design_buggy.sv"):
        load_case(case_dir)


def test_invalid_ground_truth_json(tmp_path: Path) -> None:
    case_dir = tmp_path / "bad_json"
    case_dir.mkdir()
    for name in (
        "design_buggy.sv",
        "design_fixed.sv",
        "tb.sv",
        "spec.md",
        "expected_root_cause.md",
    ):
        (case_dir / name).write_text("x", encoding="utf-8")
    (case_dir / "ground_truth.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_case(case_dir)


def test_case_name_mismatch(tmp_path: Path) -> None:
    case_dir = tmp_path / "name_mismatch"
    case_dir.mkdir()
    for name in (
        "design_buggy.sv",
        "design_fixed.sv",
        "tb.sv",
        "spec.md",
        "expected_root_cause.md",
    ):
        (case_dir / name).write_text("x", encoding="utf-8")
    (case_dir / "ground_truth.json").write_text(
        json.dumps(
            {
                "case_name": "other_name",
                "bug_type": "x",
                "root_cause": "x",
                "suspicious_signals": ["a"],
                "suspicious_regions": [
                    {
                        "file": "design_buggy.sv",
                        "start_line": 1,
                        "end_line": 2,
                        "description": "x",
                    }
                ],
                "expected_fix": "x",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="does not match"):
        load_case(case_dir)
