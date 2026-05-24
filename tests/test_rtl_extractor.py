"""Tests for rtl_extractor module."""

from __future__ import annotations

from src.rtl_extractor import extract_context

COUNTER_RTL = """
module counter (
    input clk,
    output reg done
);
    always @(posedge clk) begin
        done <= 1'b0;
    end
endmodule
"""

FIFO_RTL = """
module fifo (
    input wr_ptr,
    input rd_ptr,
    output full
);
    assign full = (wr_ptr == rd_ptr);
endmodule
"""

FSM_RTL = """
module vm (
    input clk,
    output reg dispense
);
    always @(posedge clk) begin
        case (1'b1)
            default: dispense <= 1'b0;
        endcase
    end
endmodule
"""


def test_extract_sequential_always_for_done() -> None:
    parsed = {"failed_signal": "done", "status": "FAIL"}
    ctx = extract_context(COUNTER_RTL, parsed)
    assert "done" in ctx["suspicious_signals"]
    assert ctx["suspicious_code_blocks"]
    assert ctx["suspicious_code_blocks"][0]["type"] == "sequential_always"


def test_extract_assign_for_full() -> None:
    parsed = {"failed_signal": "full", "status": "FAIL"}
    ctx = extract_context(FIFO_RTL, parsed)
    assert "full" in ctx["suspicious_signals"]
    assert ctx["suspicious_code_blocks"][0]["type"] == "assign"


def test_extract_case_for_fsm() -> None:
    parsed = {"failed_signal": "dispense", "status": "FAIL"}
    ctx = extract_context(FSM_RTL, parsed)
    assert "dispense" in ctx["suspicious_signals"]
    assert ctx["suspicious_code_blocks"][0]["type"] in {"case", "sequential_always"}


def test_null_failed_signal_warning() -> None:
    parsed = {"failed_signal": None, "status": "FAIL"}
    ctx = extract_context(COUNTER_RTL, parsed)
    assert ctx["suspicious_code_blocks"] == []
    assert ctx["extraction_warnings"]


def test_missing_signal_warning() -> None:
    parsed = {"failed_signal": "missing_sig", "status": "FAIL"}
    ctx = extract_context(COUNTER_RTL, parsed)
    assert "missing_sig" in ctx["suspicious_signals"]
    assert ctx["extraction_warnings"]


def test_deduplicate_blocks() -> None:
    rtl = """
module m(input clk, output reg done);
    always @(posedge clk) begin
        done <= done;
    end
endmodule
"""
    parsed = {"failed_signal": "done", "status": "FAIL"}
    ctx = extract_context(rtl, parsed)
    assert len(ctx["suspicious_code_blocks"]) == 1
