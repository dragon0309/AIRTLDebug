# Experiment Results

## Experiment Setup

AIRTLDebug was evaluated on three RTL bug benchmarks:

| Case | Bug Type | Failed Signal | Failure Cycle |
|---|---|---:|---:|
| counter_off_by_one | Counter off-by-one bug | done | 17 |
| fifo_full_flag_bug | FIFO full flag logic bug | full | 12 |
| vending_machine_fsm_bug | FSM output / transition bug | dispense | 9 |

Each case contains:

- `design_buggy.sv`: buggy RTL that should fail simulation
- `design_fixed.sv`: prepared fixed RTL that should pass simulation
- `tb.sv`: testbench with structured failure messages
- `ground_truth.json`: expected root cause and suspicious RTL region

## Execution Command

```bash
uv run python scripts/run_experiments.py
```

## Summary

| Case | Buggy RTL | Fixed RTL | Generated Report | Generated Prompt |
|---|---|---|---|---|
| counter_off_by_one | FAIL | PASS | `outputs/counter_off_by_one/debug_report.md` | `outputs/counter_off_by_one/full_flow_prompt.txt` |
| fifo_full_flag_bug | FAIL | PASS | `outputs/fifo_full_flag_bug/debug_report.md` | `outputs/fifo_full_flag_bug/full_flow_prompt.txt` |
| vending_machine_fsm_bug | FAIL | PASS | `outputs/vending_machine_fsm_bug/debug_report.md` | `outputs/vending_machine_fsm_bug/full_flow_prompt.txt` |

## Observations

- The A-side pipeline successfully detects failures for all buggy RTL designs.
- The prepared fixed RTL versions pass simulation for all three benchmarks.
- The B-side prompt builder exports a full-flow prompt for every case.
- The B-side report writer generates a Markdown debug report for every case.
- Mock LLM mode provides deterministic output and is suitable for reproducible demo runs.
- Gemini backend is implemented, but external API availability depends on Google project quota. If the API fails, the tool reports the failure instead of crashing.

## Generated CSV

```text
outputs/experiment_summary.csv
```

## Current Limitation

The current stable demo uses `--model mock`. The mock backend uses benchmark ground truth to produce deterministic analysis. It is useful for reproducible testing and demo backup, but final experiments should clearly distinguish it from real external LLM output.
