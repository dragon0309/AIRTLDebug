# Module: Unit Tests

> 完整 pytest（unit + integration）為必需；覆蓋 `doc/prompt.md` §5 與 detailed design §15。

## 目標

- 各 core 模塊（A2–A5）完成時已撰寫對應 `tests/test_*.py`
- Phase A6 補齊 integration / CLI 測試，並確認全部測試通過

## 子任務

### test_case_loader.py（Phase A5 case-loader 時完成）

- [ ] 載入有效 case 成功
- [ ] 缺少 `design_buggy.sv` 拋出錯誤
- [ ] 非法 `ground_truth.json` 拋出 `ValueError`
- [ ] `ground_truth.case_name` 與目錄名不一致拋出 `ValueError`

### test_sim_runner.py（Phase A2 sim-runner 時完成）

- [ ] 已知 passing case（fixed RTL）→ `status: PASS`
- [ ] 已知 failing case（buggy RTL）→ `status: FAIL`
- [ ] 缺失 RTL path 有清晰錯誤
- [ ] compile error 回報 `COMPILE_ERROR`
- [ ] log 文件被建立
- [ ] iverilog 缺失時以 `@pytest.mark.skipif` skip

### test_log_parser.py（Phase A3 log-parser 時完成）

- [ ] 解析有效 `[FAIL]` 行
- [ ] 解析 `[PASS]` log
- [ ] 解析畸形 fail 行（fallback）
- [ ] 多行 `[FAIL]` 取第一行
- [ ] binary expected / actual 值

### test_rtl_extractor.py（Phase A4 rtl-extractor 時完成）

- [ ] 擷取 `always_ff` / sequential always block（`done`）
- [ ] 擷取 `assign` statement（`full`）
- [ ] 擷取 `case` block（`state` / FSM）
- [ ] `failed_signal` 為 null 時回傳 warning
- [ ] signal 不存在時回傳 warning
- [ ] 重複 block 去重

### test_integration.py（Phase A6 本模塊完成）

- [ ] 三 case 各跑 `python src/rtl_debug_agent.py --case ... --no-llm --fix-check`
- [ ] 斷言輸出文件存在：`buggy_sim.log`、`parsed_failure.json`、`extracted_context.json`、`intermediate.json`、`fixed_sim.log`
- [ ] 斷言 `simulation.buggy.status == FAIL`、`fix_verification.status == PASS`
- [ ] iverilog 缺失時 skip

### test_rtl_debug_agent.py（Phase A6 本模塊完成，或合併至 integration）

- [ ] subprocess 跑 CLI
- [ ] `--interactive` smoke：`echo -e "0\n" | python src/rtl_debug_agent.py ... --interactive`

### 執行方式

- [ ] 可透過 `uv run pytest tests/ -v` 執行
- [ ] 所有測試在無 API key 環境下可跑

## 驗收標準

```bash
uv run pytest tests/ -v
# 全部 PASS（iverilog 相關 test 在工具缺失時可 skip，須在 progress 註明）
```

## 參考

- `doc/prompt.md` §5 Testing Strategy
- `doc/detailed_design.md` §15 Testing Plan
