"""CLI tests for rtl_debug_agent."""

from __future__ import annotations

import shutil
import subprocess
import sys

import pytest

HAS_IVERILOG = shutil.which("iverilog") is not None and shutil.which("vvp") is not None


@pytest.mark.skipif(not HAS_IVERILOG, reason="iverilog not installed")
def test_cli_subprocess() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "src/rtl_debug_agent.py",
            "--case",
            "benchmarks/counter_off_by_one",
            "--no-llm",
            "--fix-check",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr


@pytest.mark.skipif(not HAS_IVERILOG, reason="iverilog not installed")
def test_interactive_smoke() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "src/rtl_debug_agent.py",
            "--case",
            "benchmarks/counter_off_by_one",
            "--no-llm",
            "--interactive",
        ],
        input="0\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Interactive RTL Debug Menu" in proc.stdout
