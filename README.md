# AIRTLDebug

AIRTLDebug is a lightweight LLM-assisted RTL debugging flow for the SoCV final project.

Given an RTL benchmark case, the tool can:

1. run buggy RTL simulation,
2. parse structured failure logs,
3. extract suspicious RTL code blocks,
4. build a full-flow LLM debugging prompt,
5. generate a mock LLM root-cause analysis,
6. generate a Markdown debug report,
7. optionally verify a prepared fixed RTL version.

## Current Status

Implemented:

- Case loader
- Icarus Verilog simulation runner
- Failure log parser
- RTL context extractor
- CLI pipeline
- Interactive mode
- Mock LLM analysis
- Full-flow prompt builder
- Markdown debug report writer
- Fixed RTL verification
- Three benchmark cases:
  - `counter_off_by_one`
  - `fifo_full_flag_bug`
  - `vending_machine_fsm_bug`

## Requirements

- Python >= 3.12
- uv
- Icarus Verilog

Ubuntu / WSL setup:

```bash
sudo apt-get update
sudo apt-get install -y iverilog
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv sync
```

## Run One Case

```bash
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --model mock \
  --fix-check
```

Generated files:

```text
outputs/counter_off_by_one/intermediate.json
outputs/counter_off_by_one/full_flow_prompt.txt
outputs/counter_off_by_one/debug_report.md
```

## Run All A-side Benchmark Cases

```bash
bash scripts/run_all_cases.sh
```

Expected result:

```text
counter_off_by_one         FAIL         PASS
fifo_full_flag_bug         FAIL         PASS
vending_machine_fsm_bug    FAIL         PASS
```

## Interactive Mode

```bash
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --interactive \
  --fix-check
```

Interactive options:

```text
1. Show buggy simulation log
2. Show extracted suspicious RTL blocks
3. Generate LLM analysis
4. Generate report
5. Run fixed RTL verification
6. Full analysis with LLM
0. Exit
```

Currently, options 3, 4, and 6 use the mock LLM backend.

## B-side LLM and Report Features

The current B-side implementation supports a deterministic mock LLM backend for reproducible no-key testing.

Implemented B-side features:

- Build a full-flow RTL debugging prompt from `intermediate.json`
- Generate `outputs/<case_name>/full_flow_prompt.txt`
- Generate `outputs/<case_name>/debug_report.md`
- Support mock LLM analysis without external API keys
- Support interactive menu options:
  - `3`: show mock LLM root-cause analysis
  - `4`: export debug report and prompt
  - `6`: run full mock LLM analysis and export results

Note: `mock` mode uses benchmark ground truth to produce deterministic analysis. It is intended for reproducible testing and demo backup, not as the final real LLM result.

## Test

```bash
uv run pytest tests/ -v
```

Expected result:

```text
25 passed
```

## Third-Party Tools

- Icarus Verilog: RTL simulation backend
- uv: Python dependency and virtual environment management
- pytest: testing framework
- ruff / mypy: code quality tools
- LLM API backend: planned for later integration

## Project Note

The tool does not automatically patch RTL source code. It reports a suggested fix and verifies the prepared `design_fixed.sv` in each benchmark case.
