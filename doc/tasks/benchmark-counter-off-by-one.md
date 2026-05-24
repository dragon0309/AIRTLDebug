# Module: Benchmark — counter_off_by_one

> 最低難度 case，用於驗證完整 pipeline 可跑通。

## 目標

建立 `benchmarks/counter_off_by_one/`，buggy 版 FAIL、fixed 版 PASS，failure log 可被 parser 解析。

## 子任務

### 文件結構

- [ ] 建立 `benchmarks/counter_off_by_one/` 目錄
- [ ] 撰寫 `design_buggy.sv`（counter off-by-one bug：`done` 提前一 cycle 拉高）
- [ ] 撰寫 `design_fixed.sv`（與 buggy 使用**相同 top module 名稱**）
- [ ] 撰寫 `tb.sv`（驅動 reset / enable，檢查 `done` 時序）
- [ ] 撰寫 `spec.md`（設計規格：counter 行為、`MAX`、`done` 條件）
- [ ] 撰寫 `expected_root_cause.md`（人類可讀的 root cause 說明）
- [ ] 撰寫 `ground_truth.json`（符合 schema，`case_name` 與目錄名一致）

### RTL 與 testbench 約束

- [ ] `design_buggy.sv` 與 `design_fixed.sv` 定義相同 top module，testbench 只 instantiate 該名稱
- [ ] 信號包含：`clk`、`reset`、`enable`、`count`、`done`
- [ ] testbench 失敗時輸出固定格式：
  `[FAIL] cycle=<n> signal=done expected=0 actual=1 message="done asserted too early"`
- [ ] testbench 通過時輸出：`[PASS] all checks passed`
- [ ] 首次失敗後 `$finish` 停止 simulation

### ground_truth.json

- [ ] `suspicious_signals` 非空（至少 `count`、`done`）
- [ ] `suspicious_regions` 指向更新 `count` / `done` 的 sequential always block
- [ ] `start_line` / `end_line` 與 `design_buggy.sv` 實際行號一致（1-based）

### 手動驗證

- [ ] 編譯並執行 buggy 版：`iverilog -g2012 -o /tmp/sim_buggy.out design_buggy.sv tb.sv && vvp /tmp/sim_buggy.out` → 輸出含 `[FAIL]`
- [ ] 編譯並執行 fixed 版：替換為 `design_fixed.sv` → 輸出含 `[PASS] all checks passed`

## 驗收標準

| 項目 | 預期 |
|---|---|
| Buggy simulation | `[FAIL]`，`signal=done` |
| Fixed simulation | `[PASS] all checks passed` |
| 模塊名稱 | buggy / fixed 相同 |

## 參考

- `doc/detailed_design.md` §5 Case 1 Detailed Design
- `doc/detailed_design.md` §4.1–4.3 Common Case Folder Contract
