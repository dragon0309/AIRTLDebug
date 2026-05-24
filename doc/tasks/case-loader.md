# Module: case_loader.py

> 讀取 benchmark case 目錄，回傳結構化 `CaseData`，不執行 simulation 或 LLM。

## 目標

實作 `load_case(case_path) -> dict`，載入 case 下所有必需文件並驗證 `ground_truth.json`。

## 子任務

### 核心 API

- [ ] 實作 `load_case(case_path: str | Path) -> dict`
- [ ] 回傳字段：`case_name`、`case_path`、`files`（各路徑）、`buggy_rtl`、`fixed_rtl`、`testbench`、`spec`、`expected_root_cause`、`ground_truth`

### 輸入驗證

- [ ] case 目錄不存在 → 拋出 `FileNotFoundError`
- [ ] 缺少任一必需文件（`design_buggy.sv`、`design_fixed.sv`、`tb.sv`、`spec.md`、`expected_root_cause.md`、`ground_truth.json`）→ 拋出 `FileNotFoundError` 並指明缺失文件名
- [ ] `ground_truth.json` 非法 JSON → 拋出 `ValueError`
- [ ] `ground_truth.case_name` 與目錄名不一致 → 拋出 `ValueError`

### 錯誤訊息格式

- [ ] 缺失文件時輸出：`[ERROR] Required benchmark file is missing: benchmarks/<case_name>/<file>`

### 整合驗證

- [ ] 對三個 benchmark case 分別呼叫 `load_case`，均能成功回傳完整 dict

## 驗收標準

```python
from src.case_loader import load_case
data = load_case("benchmarks/counter_off_by_one")
assert data["case_name"] == "counter_off_by_one"
assert "buggy_rtl" in data and "ground_truth" in data
```

## 參考

- `doc/detailed_design.md` §8 case_loader.py Detailed Design
