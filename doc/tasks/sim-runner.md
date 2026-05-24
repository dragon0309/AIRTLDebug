# Module: sim_runner.py

> 使用 Icarus Verilog 編譯並執行 RTL simulation，寫入 log 文件。

## 目標

實作 buggy / fixed simulation 函數，回傳結構化 `SimulationResult` dict。

## 子任務

### 核心 API

- [ ] 實作 `run_simulation(rtl_path, tb_path, output_dir, output_name) -> dict`
- [ ] 實作 `run_buggy_simulation(case_data, output_dir) -> dict`
- [ ] 實作 `run_fixed_simulation(case_data, output_dir) -> dict`

### 編譯與執行

- [ ] compile：`iverilog -g2012 -o <output_dir>/<output_name>.out <rtl> <tb>`
- [ ] run：`vvp <output_dir>/<output_name>.out`
- [ ] log 寫入 `outputs/<case_name>/buggy_sim.log` 或 `fixed_sim.log`（含 stdout + stderr）
- [ ] `output_dir` 不存在時自動建立

### 狀態判定

- [ ] compile 非零 → `status: COMPILE_ERROR`
- [ ] compile 成功、run 非零 → `status: RUNTIME_ERROR`
- [ ] log 含 `[PASS]` → `status: PASS`
- [ ] log 含 `[FAIL]` → `status: FAIL`
- [ ] 無 `[PASS]` 也無 `[FAIL]` → `status: RUNTIME_ERROR`

### 回傳 JSON 字段

- [ ] 包含：`status`、`compile_status`、`run_status`、`rtl_path`、`tb_path`、`sim_executable`、`log_path`、`returncode_compile`、`returncode_run`、`stdout`、`stderr`、`command_compile`、`command_run`

### 錯誤處理

- [ ] `iverilog` 未找到 → `COMPILE_ERROR` 並附清晰訊息
- [ ] `vvp` 未找到 → `RUNTIME_ERROR` 並附清晰訊息
- [ ] compile + run 合計超過 30 秒 → `RUNTIME_ERROR` 並附 timeout 訊息（見 `doc/prompt.md` §3.6）
- [ ] compile 失敗時輸出：`[ERROR] Icarus Verilog compile failed for case <case_name>.`

### 整合驗證

- [ ] 對 `counter_off_by_one` 跑 buggy sim → `status: FAIL`，log 文件存在
- [ ] 對 `counter_off_by_one` 跑 fixed sim → `status: PASS`
- [ ] 三個 benchmark case 的 buggy sim 均為 `FAIL`

## 驗收標準

```bash
# 在 Python REPL 或測試中
result = run_buggy_simulation(case_data, "outputs/counter_off_by_one")
assert result["status"] == "FAIL"
assert Path(result["log_path"]).exists()
```

## 參考

- `doc/detailed_design.md` §9 sim_runner.py Detailed Design
