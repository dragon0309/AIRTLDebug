# Module: Benchmark — fifo_full_flag_bug

> 中等難度 case，測試 pointer / flag logic bug 的定位能力。

## 目標

建立 `benchmarks/fifo_full_flag_bug/`，buggy 版因 `full` 邏輯忽略 wrap-around 而 FAIL。

## 子任務

### 文件結構

- [ ] 建立 `benchmarks/fifo_full_flag_bug/` 目錄
- [ ] 撰寫 `design_buggy.sv`（`full` 僅比較 `wr_ptr == rd_ptr`，無法區分 full / empty）
- [ ] 撰寫 `design_fixed.sv`（正確考慮 wrap-around / 額外 flag）
- [ ] 撰寫 `tb.sv`（填滿 FIFO 至 capacity，檢查 `full`）
- [ ] 撰寫 `spec.md`
- [ ] 撰寫 `expected_root_cause.md`
- [ ] 撰寫 `ground_truth.json`

### RTL 與 testbench 約束

- [ ] buggy / fixed 使用相同 top module 名稱
- [ ] 信號包含：`clk`、`reset`、`wr_en`、`rd_en`、`wr_ptr`、`rd_ptr`、`full`、`empty`、`wrap_bit`（或等效設計）
- [ ] testbench 失敗範例：
  `[FAIL] cycle=12 signal=full expected=1 actual=0 message="full flag ignores wrap-around state"`
- [ ] testbench 通過時輸出：`[PASS] all checks passed`

### ground_truth.json

- [ ] `suspicious_regions` 指向計算 `full` 的 `assign` 或 `combinational_always` block
- [ ] `suspicious_signals` 包含 `full`、`wr_ptr`、`rd_ptr` 等

### 手動驗證

- [ ] Buggy 版 simulation → `[FAIL]`，`signal=full`
- [ ] Fixed 版 simulation → `[PASS] all checks passed`

## 驗收標準

| 項目 | 預期 |
|---|---|
| Buggy simulation | `[FAIL]`，`signal=full` |
| Fixed simulation | `[PASS]` |
| Suspicious region type | `assign` 或 `combinational_always` |

## 參考

- `doc/detailed_design.md` §6 Case 2 Detailed Design
