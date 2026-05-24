"""Integration tests for the full A-side pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CASES = [
    "counter_off_by_one",
    "fifo_full_flag_bug",
    "vending_machine_fsm_bug",
]

HAS_IVERILOG = shutil.which("iverilog") is not None and shutil.which("vvp") is not None


@pytest.mark.skipif(not HAS_IVERILOG, reason="iverilog not installed")
@pytest.mark.parametrize("case_name", CASES)
def test_full_pipeline(case_name: str, tmp_path: Path) -> None:
    out_dir = tmp_path / case_name
    proc = subprocess.run(
        [
            sys.executable,
            "src/rtl_debug_agent.py",
            "--case",
            f"benchmarks/{case_name}",
            "--no-llm",
            "--fix-check",
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr

    expected_files = [
        "buggy_sim.log",
        "parsed_failure.json",
        "extracted_context.json",
        "intermediate.json",
        "fixed_sim.log",
    ]
    for name in expected_files:
        assert (out_dir / name).is_file()

    intermediate = json.loads((out_dir / "intermediate.json").read_text(encoding="utf-8"))
    assert intermediate["simulation"]["buggy"]["status"] == "FAIL"
    assert intermediate["fix_verification"]["status"] == "PASS"
