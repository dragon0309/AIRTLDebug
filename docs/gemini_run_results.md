# Gemini 執行結果紀錄

## 實驗目的

驗證 AIRTLDebug 能夠完成：

```text
RTL benchmark
→ 模擬執行
→ failure log parsing
→ suspicious RTL extraction
→ prompt generation
→ Gemini 分析
→ Markdown debug report
→ fixed RTL 驗證
```

## 執行指令

```bash
uv run python src/rtl_debug_agent.py --case benchmarks/counter_off_by_one --model gemini --fix-check
uv run python src/rtl_debug_agent.py --case benchmarks/fifo_full_flag_bug --model gemini --fix-check
uv run python src/rtl_debug_agent.py --case benchmarks/vending_machine_fsm_bug --model gemini --fix-check
```

## 結果總覽

| Case | Buggy RTL | Fixed RTL | Failed Signal | Failure Cycle | Gemini 結果 |
|---|---|---|---|---:|---|
| counter_off_by_one | FAIL | PASS | done | 17 | 找出 done 提早 assert |
| fifo_full_flag_bug | FAIL | PASS | full | 12 | 找出 FIFO full flag 判斷錯誤 |
| vending_machine_fsm_bug | FAIL | PASS | dispense | 9 | 找出 dispense 訊號沒有正確 assert |

## counter_off_by_one

Gemini 成功指出：

```systemverilog
done <= (count == MAX - 1);
```

會導致 `done` 提早一個 cycle 被拉高。建議改成：

```systemverilog
done <= (count == MAX);
```

Fixed RTL simulation：PASS。

## fifo_full_flag_bug

Gemini 能定位 FIFO `full` flag 的判斷邏輯錯誤。原本邏輯沒有正確處理 write pointer wrap-around 後的狀態。

Fixed RTL simulation：PASS。

## vending_machine_fsm_bug

Gemini 能找出 FSM 中 `dispense` 訊號沒有在 credit 足夠時正確被 assert。

Fixed RTL simulation：PASS。

## 測試結果

```bash
uv run pytest tests/ -v
```

結果：

```text
25 passed
```

## 備註

- 外部 LLM 使用 Gemini 2.5 Flash Lite。
- 系統支援 `--model gemini` 和 `--model mock`。
- `mock` 模式可作為沒有 API 或 quota 不足時的備援。
- 詳細分析結果會輸出至：

```text
outputs/<case>/debug_report.md
outputs/<case>/full_flow_prompt.txt
```

- Gemini backend 已能成功產生結構化分析結果並整合至 debug report 中。