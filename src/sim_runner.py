"""Run Icarus Verilog simulations for benchmark cases."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 30


def _which_or_none(name: str) -> str | None:
    return shutil.which(name)


def _determine_status(stdout: str, stderr: str, compile_rc: int, run_rc: int) -> str:
    combined = f"{stdout}\n{stderr}"
    if compile_rc != 0:
        return "COMPILE_ERROR"
    if run_rc != 0:
        return "RUNTIME_ERROR"
    if "[PASS]" in combined:
        return "PASS"
    if "[FAIL]" in combined:
        return "FAIL"
    return "RUNTIME_ERROR"


def run_simulation(
    rtl_path: str | Path,
    tb_path: str | Path,
    output_dir: str | Path,
    output_name: str,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Compile and run a simulation, writing a combined log file."""
    rtl = Path(rtl_path)
    tb = Path(tb_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    sim_executable = out_dir / f"{output_name}.out"
    log_name = "buggy_sim.log" if "buggy" in output_name else "fixed_sim.log"
    log_path = out_dir / log_name

    iverilog = _which_or_none("iverilog")
    vvp = _which_or_none("vvp")

    command_compile = [
        "iverilog",
        "-g2012",
        "-o",
        str(sim_executable),
        str(rtl),
        str(tb),
    ]
    command_run = ["vvp", str(sim_executable)]

    result: dict[str, Any] = {
        "status": "RUNTIME_ERROR",
        "compile_status": "FAIL",
        "run_status": "SKIPPED",
        "rtl_path": str(rtl).replace("\\", "/"),
        "tb_path": str(tb).replace("\\", "/"),
        "sim_executable": str(sim_executable).replace("\\", "/"),
        "log_path": str(log_path).replace("\\", "/"),
        "returncode_compile": -1,
        "returncode_run": -1,
        "stdout": "",
        "stderr": "",
        "command_compile": command_compile,
        "command_run": command_run,
    }

    if iverilog is None:
        result["stderr"] = "iverilog not found in PATH"
        result["status"] = "COMPILE_ERROR"
        log_path.write_text(result["stderr"], encoding="utf-8")
        return result

    try:
        compile_proc = subprocess.run(
            command_compile,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        msg = f"Simulation timed out after {timeout_seconds} seconds during compile"
        result["stderr"] = msg
        result["status"] = "RUNTIME_ERROR"
        log_path.write_text(msg, encoding="utf-8")
        return result

    result["returncode_compile"] = compile_proc.returncode
    stdout_parts = [compile_proc.stdout]
    stderr_parts = [compile_proc.stderr]

    if compile_proc.returncode != 0:
        case_hint = rtl.parent.name
        stderr_parts.append(
            f"[ERROR] Icarus Verilog compile failed for case {case_hint}."
        )
        combined = "\n".join(part for part in stdout_parts + stderr_parts if part)
        result["stdout"] = compile_proc.stdout
        result["stderr"] = "\n".join(stderr_parts)
        result["status"] = "COMPILE_ERROR"
        result["compile_status"] = "FAIL"
        log_path.write_text(combined, encoding="utf-8")
        return result

    result["compile_status"] = "PASS"

    if vvp is None:
        msg = "vvp not found in PATH"
        result["stderr"] = msg
        result["status"] = "RUNTIME_ERROR"
        log_path.write_text("\n".join(stdout_parts + [msg]), encoding="utf-8")
        return result

    try:
        run_proc = subprocess.run(
            command_run,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        msg = f"Simulation timed out after {timeout_seconds} seconds during run"
        result["stderr"] = msg
        result["status"] = "RUNTIME_ERROR"
        log_path.write_text("\n".join(stdout_parts + [msg]), encoding="utf-8")
        return result

    result["returncode_run"] = run_proc.returncode
    stdout_parts.append(run_proc.stdout)
    stderr_parts.append(run_proc.stderr)

    combined = "\n".join(part for part in stdout_parts + stderr_parts if part)
    result["stdout"] = "\n".join(part for part in stdout_parts if part)
    result["stderr"] = "\n".join(part for part in stderr_parts if part)
    result["run_status"] = "PASS" if run_proc.returncode == 0 else "FAIL"
    result["status"] = _determine_status(
        result["stdout"],
        result["stderr"],
        compile_proc.returncode,
        run_proc.returncode,
    )
    log_path.write_text(combined, encoding="utf-8")
    return result


def run_buggy_simulation(case_data: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Run simulation using the buggy RTL design."""
    files = case_data["files"]
    return run_simulation(
        files["buggy_rtl_path"],
        files["testbench_path"],
        output_dir,
        "sim_buggy",
    )


def run_fixed_simulation(case_data: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Run simulation using the fixed RTL design."""
    files = case_data["files"]
    return run_simulation(
        files["fixed_rtl_path"],
        files["testbench_path"],
        output_dir,
        "sim_fixed",
    )
