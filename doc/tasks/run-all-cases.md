# Module: scripts/run_all_cases.sh

> 一鍵批次執行全部 benchmark cases 的 A-side pipeline。

## 目標

實作 `bash scripts/run_all_cases.sh`，對三個 case 依序跑 `--no-llm --fix-check` 並彙總結果。

## 子任務

### 腳本行為

- [ ] 依序執行三個 case：
  - `benchmarks/counter_off_by_one`
  - `benchmarks/fifo_full_flag_bug`
  - `benchmarks/vending_machine_fsm_bug`
- [ ] 每 case 命令：
  ```bash
  python src/rtl_debug_agent.py --case benchmarks/<case_name> --no-llm --fix-check
  ```
- [ ] 腳本可從 repo root 執行：`bash scripts/run_all_cases.sh`

### 錯誤策略

- [ ] buggy simulation `FAIL` **不**視為腳本失敗
- [ ] 繼續跑完所有 case，最後彙總
- [ ] 僅在 Python 入口或 simulation 工具缺失時停止

### 輸出檢查

- [ ] 每 case 生成：
  - `outputs/<case_name>/buggy_sim.log`
  - `outputs/<case_name>/fixed_sim.log`
  - `outputs/<case_name>/parsed_failure.json`
  - `outputs/<case_name>/extracted_context.json`
  - `outputs/<case_name>/intermediate.json`

### 結束摘要

- [ ] 印出表格：
  ```text
  Case                       Buggy RTL    Fixed RTL
  counter_off_by_one          FAIL         PASS
  fifo_full_flag_bug          FAIL         PASS
  vending_machine_fsm_bug     FAIL         PASS
  ```

## 驗收標準

```bash
bash scripts/run_all_cases.sh
# 三 case 均完成，摘要表 Buggy=FAIL / Fixed=PASS
```

## 參考

- `doc/detailed_design.md` §13 scripts/run_all_cases.sh Detailed Design
