# Module: Benchmark — vending_machine_fsm_bug

> 中等難度 case，測試 FSM transition / output timing bug 的定位能力。

## 目標

建立 `benchmarks/vending_machine_fsm_bug/`，buggy 版在 credit 足夠時未正確 assert `dispense`。

## 子任務

### 文件結構

- [ ] 建立 `benchmarks/vending_machine_fsm_bug/` 目錄
- [ ] 撰寫 `design_buggy.sv`（FSM 漏 transition 或在錯誤 state / cycle assert `dispense`）
- [ ] 撰寫 `design_fixed.sv`
- [ ] 撰寫 `tb.sv`（投入足夠 coin，檢查 `dispense` 時序）
- [ ] 撰寫 `spec.md`
- [ ] 撰寫 `expected_root_cause.md`
- [ ] 撰寫 `ground_truth.json`

### RTL 與 testbench 約束

- [ ] buggy / fixed 使用相同 top module 名稱
- [ ] 信號包含：`clk`、`reset`、`coin`、`state`、`next_state`、`credit`、`dispense`、`refund`
- [ ] testbench 失敗範例：
  `[FAIL] cycle=9 signal=dispense expected=1 actual=0 message="dispense was not asserted after enough credit"`
- [ ] testbench 通過時輸出：`[PASS] all checks passed`
- [ ] 優先使用 `always @(posedge clk)` / `always @(*)` 以兼容 Icarus Verilog

### ground_truth.json

- [ ] `suspicious_regions` 指向 FSM transition block 或 output logic（`case` / `sequential_always` / `combinational_always`）
- [ ] `suspicious_signals` 包含 `state`、`dispense`、`credit` 等

### 手動驗證

- [ ] Buggy 版 simulation → `[FAIL]`，`signal=dispense`
- [ ] Fixed 版 simulation → `[PASS] all checks passed`

## 驗收標準

| 項目 | 預期 |
|---|---|
| Buggy simulation | `[FAIL]`，`signal=dispense` |
| Fixed simulation | `[PASS]` |
| Suspicious region type | `case`、`sequential_always` 或 `combinational_always` |

## 參考

- `doc/detailed_design.md` §7 Case 3 Detailed Design
