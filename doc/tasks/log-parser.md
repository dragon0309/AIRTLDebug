# Module: log_parser.py

> 將 simulation log 轉換為結構化 failure JSON，供 extractor 與 B-side 使用。

## 目標

實作 `parse_simulation_log` 與 `parse_simulation_log_file`，解析固定 `[FAIL]` / `[PASS]` 格式。

## 子任務

### 核心 API

- [ ] 實作 `parse_simulation_log(log_text: str) -> dict`
- [ ] 實作 `parse_simulation_log_file(log_path: str | Path) -> dict`

### PASS 解析

- [ ] log 含 `[PASS] all checks passed` → 回傳 `status: PASS`，其餘 failure 字段為 `null`

### FAIL 解析

- [ ] 匹配格式：`[FAIL] cycle=<n> signal=<sig> expected=<exp> actual=<act> message="<msg>"`
- [ ] 回傳：`status`、`failure_cycle`（int）、`failed_signal`、`expected`、`actual`、`message`、`raw_failure_line`
- [ ] 支援 binary / decimal / symbolic 的 expected / actual 字符串

### Fallback

- [ ] simulation 失敗但無結構化 `[FAIL]` → `status: FAIL`，message 為 fallback 文字，`raw_failure_line: null`
- [ ] 空 log → 依 simulation 狀態回傳 `FAIL` 或 `UNKNOWN`
- [ ] 多行 `[FAIL]` → 使用第一行，並在 `all_failure_lines` 保存全部
- [ ] 畸形 `[FAIL]` 行 → fallback 並保留 raw line

### 狀態約束

- [ ] `parsed_failure.status` 僅允許：`PASS`、`FAIL`、`UNKNOWN`

### 整合驗證

- [ ] 解析三個 benchmark 的 `buggy_sim.log`，均能提取正確 `failed_signal`
- [ ] 解析 fixed sim log → `status: PASS`

## 驗收標準

```python
result = parse_simulation_log('[FAIL] cycle=17 signal=done expected=0 actual=1 message="done asserted too early"')
assert result["failure_cycle"] == 17
assert result["failed_signal"] == "done"
```

輸出文件由 `rtl_debug_agent.py` 寫入 `outputs/<case_name>/parsed_failure.json`。

## 參考

- `doc/detailed_design.md` §10 log_parser.py Detailed Design
