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

- Bug summary: The `full` flag is incorrectly asserted. In the failure cycle 12, the `full` signal is expected to be 1 but is actually 0. This indicates the `full` flag logic does not correctly identify the full state of the FIFO, specifically when wrap-around is involved.
- Root cause: The `full` flag is defined as `(wr_ptr == rd_ptr) && !wrap_bit`. This logic incorrectly asserts `full` only when the pointers are equal AND the `wrap_bit` is 0. The expected behavior for a full FIFO is when `wr_ptr == rd_ptr` AND the `wrap_bit` is 1 (indicating that the write pointer has wrapped around and caught up to the read pointer). The current logic essentially implements an 'empty' condition when the pointers are equal and wrap_bit is 1.
- Evidence: The simulation failure shows `full` is 0 when it should be 1 at cycle 12. The message "full flag ignores wrap-around state" directly points to an issue with how `wrap_bit` is used in the `full` flag logic. The current `full` logic `(wr_ptr == rd_ptr) && !wrap_bit` will evaluate to false if `wrap_bit` is 1, which is precisely when the FIFO should be full after wrapping. The `wrap_bit` is toggled in the `always` block when `wr_ptr` reaches `DEPTH - 1` and wraps around. Therefore, when `wr_ptr == rd_ptr` and `wrap_bit` is 1, it indicates the FIFO is full.
- Confidence score: 1.0

## 5. Suggested Fix

The `full` flag should be asserted when `wr_ptr == rd_ptr` and the `wrap_bit` is 1, or when the write pointer is one position ahead of the read pointer and wrap_bit is 0. A more standard FIFO full condition is `(wr_ptr == rd_ptr) && wrap_bit`. However, given the specific implementation detail of `wrap_bit` toggling on a wrap, the condition for `full` should be when `wr_ptr == rd_ptr` and `wrap_bit` is 1 (meaning the write pointer has wrapped and is now equal to the read pointer). If the `wrap_bit` is 0, and `wr_ptr == rd_ptr`, it implies the FIFO is empty. Thus, the fix is to change the `full` assignment to `assign full = (wr_ptr == rd_ptr) && wrap_bit;`.

## 6. Fix Verification

- Enabled: True
- Fixed RTL simulation: PASS

## 7. Comparison with Ground Truth

- Ground-truth root cause: full is computed as wr_ptr == rd_ptr without considering wrap_bit, so full and empty are ambiguous.
- Ground-truth suspicious signals: full, wr_ptr, rd_ptr, wrap_bit
- Ground-truth expected fix: Assert full when wr_ptr == rd_ptr && wrap_bit is set.
