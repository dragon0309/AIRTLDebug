# Debug Report: fifo_full_flag_bug

## 1. Simulation Result

- Buggy RTL simulation: FAIL
- Failure cycle: 12
- Failed signal: `full`
- Expected: `1`
- Actual: `0`
- Message: full flag ignores wrap-around state

## 2. Failure Evidence

```text
[FAIL] cycle=12 signal=full expected=1 actual=0 message="full flag ignores wrap-around state"
```

## 3. Extracted RTL Context

### Suspicious Signals

- `full`
- `clk`
- `reset`
- `wr_ptr`
- `PTR_W`
- `rd_ptr`
- `wrap_bit`
- `wr_en`
- `fifo_full`
- `mem`
- `DEPTH`
- `rd_en`
- `empty`

### Suspicious RTL Blocks

### design_buggy.sv:20-42

Type: `sequential_always`

```systemverilog
    always @(posedge clk) begin
        if (reset) begin
            wr_ptr   <= {PTR_W{1'b0}};
            rd_ptr   <= {PTR_W{1'b0}};
            wrap_bit <= 1'b0;
        end else begin
            if (wr_en && !fifo_full) begin
                mem[wr_ptr] <= mem[wr_ptr];
                if (wr_ptr == DEPTH - 1) begin
                    wr_ptr   <= {PTR_W{1'b0}};
                    wrap_bit <= ~wrap_bit;
                end else begin
                    wr_ptr <= wr_ptr + 1'b1;
                end
            end
            if (rd_en && !empty) begin
                if (rd_ptr == DEPTH - 1)
                    rd_ptr <= {PTR_W{1'b0}};
                else
                    rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end
```

### design_buggy.sv:45-45

Type: `assign`

```systemverilog
    assign full  = (wr_ptr == rd_ptr) && !wrap_bit;
```

## 4. LLM Root Cause Analysis

- Bug summary: Signal full mismatches at cycle 12.
- Root cause: full is computed as wr_ptr == rd_ptr without considering wrap_bit, so full and empty are ambiguous.
- Evidence: [FAIL] cycle=12 signal=full expected=1 actual=0 message="full flag ignores wrap-around state"
- Confidence score: High

## 5. Suggested Fix

Assert full when wr_ptr == rd_ptr && wrap_bit is set.

## 6. Fix Verification

- Enabled: True
- Fixed RTL simulation: PASS

## 7. Comparison with Ground Truth

- Ground-truth root cause: full is computed as wr_ptr == rd_ptr without considering wrap_bit, so full and empty are ambiguous.
- Ground-truth suspicious signals: full, wr_ptr, rd_ptr, wrap_bit
- Ground-truth expected fix: Assert full when wr_ptr == rd_ptr && wrap_bit is set.
