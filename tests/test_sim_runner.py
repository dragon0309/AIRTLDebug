"""Tests for sim_runner module."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.case_loader import load_case
from src.sim_runner import run_buggy_simulation, run_fixed_simulation, run_simulation

HAS_IVERILOG = shutil.which("iverilog") is not None and shutil.which("vvp") is not None


@pytest.mark.skipif(not HAS_IVERILOG, reason="iverilog not installed")
def test_buggy_simulation_fails(tmp_path: Path) -> None:
    case_data = load_case("benchmarks/counter_off_by_one")
    out_dir = tmp_path / "counter"
    result = run_buggy_simulation(case_data, out_dir)
    assert result["status"] == "FAIL"
    assert Path(result["log_path"]).is_file()


@pytest.mark.skipif(not HAS_IVERILOG, reason="iverilog not installed")
def test_fixed_simulation_passes(tmp_path: Path) -> None:
    case_data = load_case("benchmarks/counter_off_by_one")
    out_dir = tmp_path / "counter"
    result = run_fixed_simulation(case_data, out_dir)
    assert result["status"] == "PASS"
    assert Path(result["log_path"]).is_file()


def test_compile_error_missing_rtl(tmp_path: Path) -> None:
    result = run_simulation(
        tmp_path / "missing.sv",
        "benchmarks/counter_off_by_one/tb.sv",
        tmp_path,
        "sim_buggy",
    )
    if HAS_IVERILOG:
        assert result["status"] == "COMPILE_ERROR"
    else:
        assert result["status"] == "COMPILE_ERROR"
    assert Path(result["log_path"]).is_file()


def test_iverilog_missing_message(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.sim_runner._which_or_none", lambda name: None)
    result = run_simulation(
        "benchmarks/counter_off_by_one/design_buggy.sv",
        "benchmarks/counter_off_by_one/tb.sv",
        tmp_path,
        "sim_buggy",
    )
    assert result["status"] == "COMPILE_ERROR"
    assert "iverilog not found" in result["stderr"]
