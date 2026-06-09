"""CLI entry point and pipeline orchestration for RTL debug workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from case_loader import load_case  # noqa: E402
from log_parser import parse_simulation_log_file  # noqa: E402
from rtl_extractor import extract_context  # noqa: E402
from sim_runner import run_buggy_simulation, run_fixed_simulation  # noqa: E402
from llm_client import run_llm_analysis  # noqa: E402
from report_writer import write_debug_report  # noqa: E402
from prompt_builder import build_full_flow_prompt  # noqa: E402

def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _build_intermediate(
    case_data: dict[str, Any],
    buggy_result: dict[str, Any],
    fixed_result: dict[str, Any] | None,
    parsed_failure: dict[str, Any],
    extracted_context: dict[str, Any],
    *,
    fix_check: bool,
) -> dict[str, Any]:
    simulation: dict[str, Any] = {
        "buggy": {
            "status": buggy_result["status"],
            "log_path": buggy_result["log_path"],
        }
    }
    fix_verification: dict[str, Any]
    if fix_check and fixed_result is not None:
        simulation["fixed"] = {
            "status": fixed_result["status"],
            "log_path": fixed_result["log_path"],
        }
        fix_verification = {
            "enabled": True,
            "status": fixed_result["status"],
        }
    else:
        fix_verification = {
            "enabled": False,
            "status": None,
        }

    return {
        "case_name": case_data["case_name"],
        "case_path": case_data["case_path"],
        "spec": case_data["spec"],
        "buggy_rtl": case_data["buggy_rtl"],
        "testbench": case_data["testbench"],
        "simulation": simulation,
        "parsed_failure": parsed_failure,
        "extracted_context": extracted_context,
        "ground_truth": case_data["ground_truth"],
        "fix_verification": fix_verification,
    }


def _print_summary(intermediate: dict[str, Any]) -> None:
    sim = intermediate["simulation"]
    print(f"Case: {intermediate['case_name']}")
    print(f"  Buggy simulation: {sim['buggy']['status']}")
    if intermediate["fix_verification"]["enabled"]:
        print(f"  Fixed simulation: {sim['fixed']['status']}")
    pf = intermediate["parsed_failure"]
    if pf.get("failed_signal"):
        print(
            f"  Failure: cycle={pf.get('failure_cycle')} signal={pf.get('failed_signal')}"
        )


def run_pipeline(
    case_path: str,
    output_dir: str | Path,
    *,
    fix_check: bool = False,
) -> tuple[dict[str, Any], int]:
    """Execute the full A-side pipeline for one case."""
    try:
        case_data = load_case(case_path)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return {}, 1

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    buggy_result = run_buggy_simulation(case_data, out_dir)
    if buggy_result["status"] == "COMPILE_ERROR":
        return {}, 2
    if buggy_result["status"] == "RUNTIME_ERROR" and "[FAIL]" not in (
        buggy_result["stdout"] + buggy_result["stderr"]
    ):
        return {}, 3

    parsed_failure = parse_simulation_log_file(buggy_result["log_path"])
    _write_json(out_dir / "parsed_failure.json", parsed_failure)

    extracted_context = extract_context(case_data["buggy_rtl"], parsed_failure)
    _write_json(out_dir / "extracted_context.json", extracted_context)

    fixed_result: dict[str, Any] | None = None
    if fix_check:
        fixed_result = run_fixed_simulation(case_data, out_dir)
        if fixed_result["status"] == "COMPILE_ERROR":
            return {}, 2
        if fixed_result["status"] == "RUNTIME_ERROR" and "[PASS]" not in (
            fixed_result["stdout"] + fixed_result["stderr"]
        ):
            return {}, 3

    intermediate = _build_intermediate(
        case_data,
        buggy_result,
        fixed_result,
        parsed_failure,
        extracted_context,
        fix_check=fix_check,
    )
    _write_json(out_dir / "intermediate.json", intermediate)
    return intermediate, 0


def _interactive_menu(case_path: str, output_dir: Path, fix_check: bool) -> int:
    intermediate, exit_code = run_pipeline(case_path, output_dir, fix_check=fix_check)
    if exit_code != 0:
        return exit_code

    while True:
        print("\nInteractive RTL Debug Menu")
        print("1. Show buggy simulation log")
        print("2. Show extracted suspicious RTL blocks")
        print("3. Generate LLM analysis")
        print("4. Generate report")
        print("5. Run fixed RTL verification")
        print("6. Full analysis with LLM")
        print("0. Exit")
        choice = input("Select option: ").strip()

        if choice == "0":
            return 0

        if choice == "1":
            log_path = intermediate["simulation"]["buggy"]["log_path"]
            print(Path(log_path).read_text(encoding="utf-8"))

        elif choice == "2":
            for block in intermediate["extracted_context"]["suspicious_code_blocks"]:
                print(
                    f"\n--- {block['type']} {block['file']}:{block['start_line']}-"
                    f"{block['end_line']} ---"
                )
                print(block["code"])

        elif choice == "3":
            prompt = build_full_flow_prompt(intermediate)
            llm_analysis = run_llm_analysis(intermediate, model="mock", prompt=prompt)

        elif choice == "4":
            prompt = build_full_flow_prompt(intermediate)
            prompt_path = output_dir / "full_flow_prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")

            llm_analysis = run_llm_analysis(intermediate, model="mock")
            report_path = write_debug_report(
                intermediate,
                llm_analysis,
                output_dir / "debug_report.md",
            )
            print(f"Report written to: {report_path}")
            print(f"Prompt written to: {prompt_path}")

        elif choice == "5":
            case_data = load_case(case_path)
            fixed_result = run_fixed_simulation(case_data, output_dir)
            print(f"Fixed simulation status: {fixed_result['status']}")
            intermediate["simulation"]["fixed"] = {
                "status": fixed_result["status"],
                "log_path": fixed_result["log_path"],
            }
            intermediate["fix_verification"] = {
                "enabled": True,
                "status": fixed_result["status"],
            }
            _write_json(output_dir / "intermediate.json", intermediate)

        elif choice == "6":
            prompt = build_full_flow_prompt(intermediate)
            prompt_path = output_dir / "full_flow_prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")

            llm_analysis = run_llm_analysis(intermediate, model="mock")
            report_path = write_debug_report(
                intermediate,
                llm_analysis,
                output_dir / "debug_report.md",
            )

            print("\nFull LLM Analysis")
            print(f"- Root cause: {llm_analysis.get('root_cause')}")
            print(f"- Suggested fix: {llm_analysis.get('suggested_fix')}")
            print(f"- Report: {report_path}")
            print(f"- Prompt: {prompt_path}")

        else:
            print("Invalid option.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="AIRTLDebug A-side RTL debug agent")
    parser.add_argument("--case", required=False, help="Path to benchmark case directory")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: outputs/<case_name>)",
    )
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM integration")
    parser.add_argument(
        "--fix-check",
        action="store_true",
        help="Run fixed RTL verification simulation",
    )
    parser.add_argument("--interactive", action="store_true", help="Interactive menu mode")
    parser.add_argument("--output", default=None, help="Report output path (reserved)")
    parser.add_argument("--model", default=None, help="LLM model name (reserved)")
    args = parser.parse_args(argv)

    if args.interactive:
        if not args.case:
            print("--case is required for interactive mode", file=sys.stderr)
            return 1
        case_data = load_case(args.case)
        output_dir = Path(args.output_dir or f"outputs/{case_data['case_name']}")
        return _interactive_menu(args.case, output_dir, args.fix_check)

    if not args.case:
        print("--case is required", file=sys.stderr)
        return 1

    case_data = load_case(args.case)
    output_dir = Path(args.output_dir or f"outputs/{case_data['case_name']}")

    try:
        intermediate, exit_code = run_pipeline(
            args.case,
            output_dir,
            fix_check=args.fix_check,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Internal error: {exc}", file=sys.stderr)
        return 4

    if exit_code != 0:
        return exit_code

    if args.no_llm:
        _print_summary(intermediate)
        return 0

    prompt = build_full_flow_prompt(intermediate)
    prompt_path = output_dir / "full_flow_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    model = args.model or "mock"
    llm_analysis = run_llm_analysis(intermediate, model=model, prompt=prompt)

    output_path = args.output
    if output_path is None:
        output_path = str(output_dir / "debug_report.md")

    report_path = write_debug_report(intermediate, llm_analysis, output_path)

    _print_summary(intermediate)
    print(f"  Report: {report_path}")
    print(f"  Prompt: {prompt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
