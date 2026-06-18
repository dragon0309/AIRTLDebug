# AIRTLDebug Demo Script

## 1. 專案動機

RTL 除錯通常需要工程師查看 simulation log、波形以及 RTL 程式碼，再逐步推測錯誤原因。這個流程往往耗時且繁瑣。

AIRTLDebug 希望利用大型語言模型（LLM），結合模擬結果與 RTL context，自動協助使用者找出可能的 root cause，並產生除錯報告。

---

## 2. 執行單一 Benchmark

執行：

```bash
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --model gemini \
  --fix-check
```

展示：

* buggy RTL simulation FAIL
* fixed RTL simulation PASS
* failure cycle 與 failed signal

---

## 3. 查看產生的 Debug Report

執行：

```bash
cat outputs/counter_off_by_one/debug_report.md
```

展示內容：

* suspicious signals
* suspicious RTL blocks
* Gemini root cause analysis
* suggested fix
* fix verification

---

## 4. Interactive Mode

執行：

```bash
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --interactive \
  --fix-check
```

示範：

1. 顯示 simulation log
2. 顯示 RTL block
3. 產生 LLM 分析
4. 匯出 report
5. 驗證 fixed RTL

---

## 5. 執行所有 Benchmark

執行：

```bash
uv run python scripts/run_experiments.py
```

展示三個 benchmark：

* counter_off_by_one
* fifo_full_flag_bug
* vending_machine_fsm_bug

觀察：

* buggy RTL 全部 FAIL
* fixed RTL 全部 PASS

---

## 6. 執行測試

執行：

```bash
uv run pytest tests/ -v
```

結果：

```text
25 passed
```

代表整體流程與各模組測試皆通過。

---

## 7. 結論

AIRTLDebug 建立了一個 RTL debugging agent flow：

```text
RTL benchmark
→ simulation
→ failure log parsing
→ suspicious RTL extraction
→ prompt generation
→ Gemini analysis
→ debug report
→ fix verification
```

系統同時支援：

* --model gemini
* --model mock

其中 mock mode 可作為 API quota 不足時的備援方案。

目前專案已完成三個 benchmark 的驗證，並能自動產生 Markdown debug report。
