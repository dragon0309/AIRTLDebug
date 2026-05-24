# Module: rtl_extractor.py

> 根據 parsed failure 從 `design_buggy.sv` 擷取 suspicious signals 與 code blocks（text-based，非完整 SV parser）。

## 目標

實作 `extract_context(rtl_text, parsed_failure, file_name) -> dict`。

## 子任務

### 核心 API

- [ ] 實作 `extract_context(rtl_text, parsed_failure, file_name="design_buggy.sv") -> dict`
- [ ] 可選 helper：`find_signal_occurrences`、`extract_enclosing_block`、`infer_block_type`、`collect_suspicious_signals`

### Signal 擷取策略

- [ ] `failed_signal` 非 null 時必須包含該 signal
- [ ] 搜尋 signal 在 RTL 中的所有出現位置
- [ ] 依優先級收集 suspicious signals：failed signal → block 內 assignment → RHS 相關 → condition 相關
- [ ] 過濾 SystemVerilog 關鍵字（`module`、`always`、`assign` 等）

### Block 擷取優先級

- [ ] `always_ff` / `always @(posedge ...)`
- [ ] `always_comb` / `always @(*)`
- [ ] `assign` statement
- [ ] `case ... endcase`
- [ ] `if ... begin ... end`
- [ ] fallback：`context_window`（小範圍上下文）

### Block 邊界規則

- [ ] 使用 `begin` / `end` nesting counter 掃描 always block
- [ ] 無 explicit begin/end 時 fallback 到 context window
- [ ] 行號 1-based，`start_line <= end_line`，`code` 保留原始文本

### Block 類型分類

- [ ] 輸出 `type`：`sequential_always`、`combinational_always`、`assign`、`case`、`context_window`

### 去重

- [ ] 相同 `file + start_line + end_line + type` 的 block 合併，`matched_signals` 合併

### Fallback 行為

- [ ] `failed_signal` 為 null → 空 blocks + warning
- [ ] signal 在 RTL 中不存在 → 保留 signal + warning

### 整合驗證

- [ ] `counter_off_by_one` + `failed_signal=done` → 擷取 sequential always block
- [ ] `fifo_full_flag_bug` + `failed_signal=full` → 擷取 assign 或 combinational block
- [ ] `vending_machine_fsm_bug` + `failed_signal=dispense` → 擷取 case 或 always block

## 驗收標準

```python
ctx = extract_context(buggy_rtl, parsed_failure)
assert "done" in ctx["suspicious_signals"]
assert len(ctx["suspicious_code_blocks"]) >= 1
assert ctx["suspicious_code_blocks"][0]["type"] in (
    "sequential_always", "combinational_always", "assign", "case", "context_window"
)
```

輸出文件由 `rtl_debug_agent.py` 寫入 `outputs/<case_name>/extracted_context.json`。

## 參考

- `doc/detailed_design.md` §11 rtl_extractor.py Detailed Design
