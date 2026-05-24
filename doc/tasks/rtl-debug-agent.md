# Module: rtl_debug_agent.py

> CLI 入口與 pipeline 協調器；串接 loader → sim → parser → extractor → intermediate JSON。

## 目標

實作完整 A-side pipeline，支援 `--no-llm` 模式下無 API key 可運行。

## 子任務

### CLI 參數

- [ ] `--case <path>`（單 case 模式必需）
- [ ] `--output-dir <path>`（預設 `outputs/<case_name>`）
- [ ] `--no-llm`（跳過 LLM，只產生 A-side artifacts）
- [ ] `--fix-check`（額外跑 `design_fixed.sv` simulation）
- [ ] `--interactive`（進入互動選單）
- [ ] `--output <path>`（保留給 B-side report，A-side 可不生成 Markdown）
- [ ] `--model <name>`（保留參數，A-side 不強制使用）

### Pipeline 主流程

- [ ] 1. 解析 CLI 參數
- [ ] 2. `case_loader.load_case`
- [ ] 3. 建立 `output_dir`
- [ ] 4. `sim_runner.run_buggy_simulation`
- [ ] 5. `log_parser.parse_simulation_log_file` → 寫 `parsed_failure.json`
- [ ] 6. `rtl_extractor.extract_context` → 寫 `extracted_context.json`
- [ ] 7. 若 `--fix-check`：`sim_runner.run_fixed_simulation` → 寫 `fixed_sim.log`
- [ ] 8. 組裝並寫入 `intermediate.json`
- [ ] 9. `--no-llm` 模式下停止，可印簡短 terminal summary

### intermediate.json

- [ ] 包含：`case_name`、`case_path`、`spec`、`buggy_rtl`、`testbench`
- [ ] 包含：`simulation.buggy`、`simulation.fixed`（fix-check 時）
- [ ] 包含：`parsed_failure`、`extracted_context`、`ground_truth`
- [ ] 包含：`fix_verification.enabled` / `fix_verification.status`
- [ ] `--fix-check` 未啟用時：`fix_verification.enabled: false`，`status: null`

### Exit Code

- [ ] pipeline 完成（含預期 buggy FAIL）→ exit 0
- [ ] case loading 錯誤 → exit 1
- [ ] compile error → exit 2
- [ ] runtime error → exit 3
- [ ] 內部工具錯誤 → exit 4

### Fix Verification（A-6）

- [ ] `--fix-check` 跑 `design_fixed.sv` + 同一 `tb.sv`
- [ ] 不修改任何 RTL 源文件
- [ ] 結果寫入 `intermediate.json` 的 `fix_verification`

### Interactive Mode（A-side 部分）

- [ ] 顯示 failure summary 與選單（1–6, 0）
- [ ] 選項 1：印出 `buggy_sim.log`
- [ ] 選項 2：印出 extracted suspicious RTL blocks
- [ ] 選項 5：執行 fixed RTL verification
- [ ] 選項 0：退出
- [ ] 選項 3 / 4 / 6：B-side 未就緒時印 `[WARN] LLM/report module is not available in this build.`

### B-side 隔離

- [ ] `--no-llm` 時不 import / 不呼叫 `llm_client.py`
- [ ] 不要求 `--output` 參數

### 整合驗證

- [ ] 三個 case 均通過：
  ```bash
  python src/rtl_debug_agent.py \
    --case benchmarks/<case_name> \
    --no-llm \
    --fix-check
  ```
- [ ] 每 case 生成：`buggy_sim.log`、`parsed_failure.json`、`extracted_context.json`、`intermediate.json`
- [ ] fix-check 時額外生成：`fixed_sim.log`
- [ ] buggy sim status = `FAIL`，fixed sim status = `PASS`

## 驗收標準

```bash
python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm \
  --fix-check
echo $?  # 應為 0
ls outputs/counter_off_by_one/{buggy_sim.log,parsed_failure.json,extracted_context.json,intermediate.json,fixed_sim.log}
```

## 參考

- `doc/detailed_design.md` §12 rtl_debug_agent.py Detailed Design
- `doc/detailed_design.md` §17 A and B Interface Contract
