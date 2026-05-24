"""Tests for log_parser module."""

from __future__ import annotations

from src.log_parser import parse_simulation_log


def test_parse_fail_line() -> None:
    log = (
        '[FAIL] cycle=17 signal=done expected=0 actual=1 '
        'message="done asserted too early"'
    )
    result = parse_simulation_log(log)
    assert result["status"] == "FAIL"
    assert result["failure_cycle"] == 17
    assert result["failed_signal"] == "done"
    assert result["expected"] == "0"
    assert result["actual"] == "1"


def test_parse_pass_line() -> None:
    result = parse_simulation_log("[PASS] all checks passed\n")
    assert result["status"] == "PASS"
    assert result["failed_signal"] is None
    assert result["message"] == "all checks passed"


def test_parse_malformed_fail_line() -> None:
    result = parse_simulation_log("[FAIL] this is malformed\n")
    assert result["status"] == "FAIL"
    assert result["failure_cycle"] is None
    assert result["raw_failure_line"] == "[FAIL] this is malformed"


def test_parse_multiple_fail_lines() -> None:
    log = (
        '[FAIL] cycle=9 signal=dispense expected=1 actual=0 message="first"\n'
        '[FAIL] cycle=10 signal=dispense expected=1 actual=0 message="second"\n'
    )
    result = parse_simulation_log(log)
    assert result["failure_cycle"] == 9
    assert result["message"] == "first"
    assert len(result["all_failure_lines"]) == 2


def test_parse_binary_values() -> None:
    log = '[FAIL] cycle=1 signal=flag expected=1\'b0 actual=1\'b1 message="bad"'
    result = parse_simulation_log(log)
    assert result["expected"] == "1'b0"
    assert result["actual"] == "1'b1"
