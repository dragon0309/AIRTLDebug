"""Run AIRTLDebug experiments for all benchmark cases."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

CASES = [
    "counter_off_by_one",
    "fifo_full_flag_bug",
    "vending_machine_fsm_bug",
]


def main() -> int:
    rows = []

    for case in CASES:
        case_path = f"benchmarks/{case}"
        print(f"=== Running {case} ===")

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "src/rtl_debug_agent.py",
                "--case",
                case_path,
                "--model",
                "mock",
                "--fix-check",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return result.returncode

        intermediate_path = Path(f"outputs/{case}/intermediate.json")
        if not intermediate_path.exists():
            print(f"[ERROR] missing {intermediate_path}")
            return 1

        import json

        data = json.loads(intermediate_path.read_text(encoding="utf-8"))
        failure = data["parsed_failure"]
        rows.append(
            {
                "case_name": case,
                "buggy_status": data["simulation"]["buggy"]["status"],
                "fixed_status": data["fix_verification"]["status"],
                "failed_signal": failure.get("failed_signal"),
                "failure_cycle": failure.get("failure_cycle"),
                "debug_report": f"outputs/{case}/debug_report.md",
                "prompt": f"outputs/{case}/full_flow_prompt.txt",
            }
        )

    out_path = Path("outputs/experiment_summary.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "case_name",
                "buggy_status",
                "fixed_status",
                "failed_signal",
                "failure_cycle",
                "debug_report",
                "prompt",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Summary written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
