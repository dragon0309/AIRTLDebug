# AIRTLDebug A-Side 總體進度

> Person A 負責：RTL benchmark、simulation runner、log parser、RTL extractor、CLI main flow、fix verification、batch script、intermediate JSON 接口。

## 環境備註

- **iverilog / vvp**：已安裝並通過整合驗收（`uv run pytest tests/ -v` → 25 passed；`bash scripts/run_all_cases.sh` → 三 case Buggy=FAIL / Fixed=PASS）。
- **benchmark failure log**：三 case 的 `[FAIL]` cycle / signal 已與 `doc/prompt.md` §5.2 範例對齊（counter cycle=17、fifo cycle=12、fsm cycle=9）。

## 建議實作順序

```text
Phase A1  repo-scaffold → benchmark cases (counter → fifo → fsm)
Phase A2  sim-runner
Phase A3  log-parser
Phase A4  rtl-extractor
Phase A5  case-loader → rtl-debug-agent
Phase A6  run-all-cases → unit-tests
```

## 模塊完成度

### Phase A1 — Benchmark Skeleton

- [x] [repo-scaffold](./repo-scaffold.md)
- [x] [benchmark-counter-off-by-one](./benchmark-counter-off-by-one.md)
- [x] [benchmark-fifo-full-flag-bug](./benchmark-fifo-full-flag-bug.md)
- [x] [benchmark-vending-machine-fsm-bug](./benchmark-vending-machine-fsm-bug.md)

### Phase A2 — Simulation

- [x] [sim-runner](./sim-runner.md)

### Phase A3 — Log Parser

- [x] [log-parser](./log-parser.md)

### Phase A4 — RTL Extractor

- [x] [rtl-extractor](./rtl-extractor.md)

### Phase A5 — CLI & Integration

- [x] [case-loader](./case-loader.md)
- [x] [rtl-debug-agent](./rtl-debug-agent.md)

### Phase A6 — Batch & Tests

- [x] [run-all-cases](./run-all-cases.md)
- [x] [unit-tests](./unit-tests.md)（完整 pytest + integration，見 doc/prompt.md §5）

## Definition of Done（A-side 全部完成時）

- [x] 三個 benchmark case 齊全，buggy FAIL / fixed PASS（含 iverilog 模擬驗收）
- [x] `case_loader.py` 可載入所有 case
- [x] `sim_runner.py` 可跑 buggy / fixed simulation（需 iverilog）
- [x] `log_parser.py` 產生 `parsed_failure.json`
- [x] `rtl_extractor.py` 產生 `extracted_context.json`
- [x] `rtl_debug_agent.py --no-llm --fix-check` 三 case 均可運行（需 iverilog）
- [x] `scripts/run_all_cases.sh` 可一鍵批次執行
- [x] `intermediate.json` schema 穩定，B-side 可消費
- [x] `uv run pytest tests/ -v` 全 PASS（25 passed，含 iverilog 整合測試）
- [x] `uv run ruff check src tests` 與 `uv run mypy src` 零 error
- [x] `requirements.txt` 已 export
- [x] 無 API key、binary、`.out`、生成輸出被 commit

## 最終整合驗收命令

```bash
# 單 case
python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm \
  --fix-check

# 全部 case
bash scripts/run_all_cases.sh
```

## 任務文件索引

| 模塊 | 文件 | 產出 |
|---|---|---|
| Repo Scaffold | [repo-scaffold.md](./repo-scaffold.md) | 目錄結構、`pyproject.toml` 工具鏈設定 |
| Counter Benchmark | [benchmark-counter-off-by-one.md](./benchmark-counter-off-by-one.md) | `benchmarks/counter_off_by_one/` |
| FIFO Benchmark | [benchmark-fifo-full-flag-bug.md](./benchmark-fifo-full-flag-bug.md) | `benchmarks/fifo_full_flag_bug/` |
| FSM Benchmark | [benchmark-vending-machine-fsm-bug.md](./benchmark-vending-machine-fsm-bug.md) | `benchmarks/vending_machine_fsm_bug/` |
| Case Loader | [case-loader.md](./case-loader.md) | `src/case_loader.py` |
| Sim Runner | [sim-runner.md](./sim-runner.md) | `src/sim_runner.py` |
| Log Parser | [log-parser.md](./log-parser.md) | `src/log_parser.py` |
| RTL Extractor | [rtl-extractor.md](./rtl-extractor.md) | `src/rtl_extractor.py` |
| CLI Agent | [rtl-debug-agent.md](./rtl-debug-agent.md) | `src/rtl_debug_agent.py` |
| Batch Script | [run-all-cases.md](./run-all-cases.md) | `scripts/run_all_cases.sh` |
| Unit Tests | [unit-tests.md](./unit-tests.md) | `tests/test_*.py` |

## 參考文檔

- 需求：`doc/SoCV_Final_Project.pdf` §25 A-side 分工（A-1 ~ A-7）
- 詳細設計：`doc/detailed_design.md` §18 Implementation Order、§19 Definition of Done
