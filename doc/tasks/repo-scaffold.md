# Module: Repo Scaffold

> A-side 基礎目錄結構與工具鏈設定，供後續模塊開發使用。

## 目標

建立 A-side 所需的最小 repo 骨架，不含 B-side LLM / report 模塊。

## 子任務

- [ ] 建立 `src/` 目錄，並放置空模塊占位文件（`case_loader.py`、`sim_runner.py`、`log_parser.py`、`rtl_extractor.py`、`rtl_debug_agent.py`）
- [ ] 建立 `benchmarks/` 目錄
- [ ] 建立 `scripts/` 目錄
- [ ] 建立 `outputs/.gitkeep`，確保 `outputs/` 可被 git 追蹤但忽略生成物
- [ ] 建立 `tests/` 目錄（供後續 unit tests 使用）
- [ ] 確認 `.gitignore` 包含：`.env`、`*.out`、`*.vcd`、`*.o`、`__pycache__/`、`.venv/`、`outputs/*/`、`!outputs/.gitkeep`
- [ ] 完善 `pyproject.toml`：
  - dev 依賴：`pytest`、`ruff`、`mypy`
  - `[tool.ruff]`、`[tool.ruff.lint]`（見 `doc/prompt.md` §3.3）
  - `[tool.mypy]`（見 `doc/prompt.md` §3.2）
  - `[tool.pytest.ini_options]`：`pythonpath = ["."]`

## 驗收標準

```bash
uv sync
uv run pytest --version
```

```text
AIRTLDebug/
  src/
  benchmarks/
  scripts/
  outputs/.gitkeep
  tests/
  pyproject.toml   # 含 pytest / ruff / mypy 設定
```

## 參考

- `doc/prompt.md` §3 Environment & Toolchain
- `doc/detailed_design.md` §3 Repository Structure Used by A
- `doc/detailed_design.md` §19 Definition of Done — 不可 commit API key、binary、生成輸出
