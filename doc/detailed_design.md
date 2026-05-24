# AIRTLDebug Detailed Design Document

## 1. Document Scope

This document defines the detailed design for the A-side work of AIRTLDebug.

A-side responsibility:

- RTL bug benchmark design
- Simulation runner
- Failure log parser
- RTL code extractor
- CLI main flow
- Fix verification
- Batch run script
- Intermediate JSON interface for B-side LLM, prompt, report, and experiment modules

This design follows the requirement document `SoCV_Final_Project.pdf`.

## 2. Design Principles

### 2.1 Module Independence

Each module must be independently testable.

| Module | Input | Output | Can test independently |
|---|---|---|---|
| `case_loader.py` | benchmark case directory | `CaseData` object or dictionary | Yes |
| `sim_runner.py` | RTL file paths, output directory | `SimulationResult` | Yes |
| `log_parser.py` | simulation log text or path | `ParsedFailure` | Yes |
| `rtl_extractor.py` | buggy RTL text, parsed failure | `ExtractedContext` | Yes |
| `rtl_debug_agent.py` | CLI arguments | output JSON, logs, report path | Integration test |
| `scripts/run_all_cases.sh` | benchmark root | per-case output files | Integration test |

### 2.2 No Hidden Dependency on LLM

A-side pipeline must work even when no API key exists.

The following command must run without LLM:

```bash
python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm
```

Expected output files:

```text
outputs/counter_off_by_one/buggy_sim.log
outputs/counter_off_by_one/parsed_failure.json
outputs/counter_off_by_one/extracted_context.json
outputs/counter_off_by_one/intermediate.json
```

### 2.3 Stable Interface for B

A-side modules must generate stable JSON files so B-side modules can build prompts, call LLM, write reports, and run experiments without depending on A's internal implementation.

Primary interface file:

```text
outputs/<case_name>/intermediate.json
```

### 2.4 Prepared Fix Verification Only

The tool must not claim automatic RTL patching.

Correct behavior:

- LLM may suggest a fix.
- A-side tool verifies `design_fixed.sv` already prepared inside the benchmark folder.
- `--fix-check` records whether the prepared fixed RTL passes simulation.

## 3. Repository Structure Used by A

```text
AIRTLDebug/
src/
  rtl_debug_agent.py
  case_loader.py
  sim_runner.py
  log_parser.py
  rtl_extractor.py
scripts/
  run_all_cases.sh
benchmarks/
  counter_off_by_one/
    design_buggy.sv
    design_fixed.sv
    tb.sv
    spec.md
    expected_root_cause.md
    ground_truth.json
  fifo_full_flag_bug/
    design_buggy.sv
    design_fixed.sv
    tb.sv
    spec.md
    expected_root_cause.md
    ground_truth.json
  vending_machine_fsm_bug/
    design_buggy.sv
    design_fixed.sv
    tb.sv
    spec.md
    expected_root_cause.md
    ground_truth.json
outputs/
  .gitkeep
```

## 4. Benchmark Case Design

### 4.1 Common Case Folder Contract

Every benchmark case must contain exactly these required files:

```text
design_buggy.sv
design_fixed.sv
tb.sv
spec.md
expected_root_cause.md
ground_truth.json
```

Optional generated files must not be stored inside the benchmark folder. They must be written under:

```text
outputs/<case_name>/
```

### 4.1.1 RTL Module Naming Rule

For each benchmark, `design_buggy.sv` and `design_fixed.sv` must define the same top module name. The testbench `tb.sv` must instantiate this shared module name. This allows the simulator to switch between buggy and fixed RTL by changing only the design file path.

Rules:

- Buggy and fixed switching must happen only by passing a different RTL file to the simulator.
- The testbench must not depend on different module names for buggy and fixed variants.

Example compile commands:

```bash
iverilog -g2012 -o outputs/<case_name>/sim_buggy.out \
  benchmarks/<case_name>/design_buggy.sv \
  benchmarks/<case_name>/tb.sv

iverilog -g2012 -o outputs/<case_name>/sim_fixed.out \
  benchmarks/<case_name>/design_fixed.sv \
  benchmarks/<case_name>/tb.sv
```

### 4.2 Testbench Output Contract

All testbenches must print structured messages.

For passing simulation:

```text
[PASS] all checks passed
```

For failing simulation:

```text
[FAIL] cycle=<cycle> signal=<signal> expected=<expected> actual=<actual> message="<message>"
```

Example:

```text
[FAIL] cycle=17 signal=done expected=0 actual=1 message="done asserted too early"
```

Rules:

- `cycle` must be an integer.
- `signal` must match a signal name in `design_buggy.sv` when possible.
- `expected` and `actual` are stored as strings to support binary, decimal, and symbolic values.
- `message` must be human-readable and enclosed in double quotes.
- A testbench should stop after the first detected failure using `$finish`.

### 4.3 Ground Truth JSON Contract

Each case must provide `ground_truth.json`.

Required schema:

```json
{
  "case_name": "counter_off_by_one",
  "bug_type": "counter off-by-one",
  "root_cause": "done is asserted one cycle too early because the comparison condition uses MAX - 1.",
  "suspicious_signals": ["count", "done"],
  "suspicious_regions": [
    {
      "file": "design_buggy.sv",
      "start_line": 23,
      "end_line": 35,
      "description": "sequential always block that updates count and done"
    }
  ],
  "expected_fix": "Compare count with MAX, or compute next_count and compare next_count with MAX."
}
```

Validation rules:

- `case_name` must equal the folder name.
- `suspicious_signals` must be a non-empty list.
- Each suspicious region must contain `file`, `start_line`, `end_line`, and `description`.
- `start_line <= end_line`.
- Line numbers use 1-based indexing.

## 5. Case 1 Detailed Design: `counter_off_by_one`

### 5.1 Purpose

This is the lowest-difficulty case used to confirm the full pipeline works.

### 5.2 Intended Correct Behavior

`done` should be asserted when the counter reaches `MAX`.

### 5.3 Buggy Behavior

`done` is asserted one cycle too early because the buggy RTL checks `MAX - 1` or otherwise compares against the wrong count value.

### 5.4 Required Signals

Recommended signals:

- `clk`
- `reset`
- `enable`
- `count`
- `done`

### 5.5 Testbench Strategy

The testbench drives reset, enables counting, and checks the expected timing of `done`.

Expected failure example:

```text
[FAIL] cycle=17 signal=done expected=0 actual=1 message="done asserted too early"
```

### 5.6 Suspicious Region

The ground truth suspicious region should point to the sequential always block that updates `count` and `done`.

Expected region type:

```text
sequential_always
```

## 6. Case 2 Detailed Design: `fifo_full_flag_bug`

### 6.1 Purpose

This case tests whether AIRTLDebug can handle pointer and flag logic.

### 6.2 Intended Correct Behavior

`full` should distinguish full from empty using write pointer, read pointer, and wrap-around information.

### 6.3 Buggy Behavior

The buggy RTL compares only `wr_ptr == rd_ptr`, causing full and empty ambiguity.

### 6.4 Required Signals

Recommended signals:

- `clk`
- `reset`
- `wr_en`
- `rd_en`
- `wr_ptr`
- `rd_ptr`
- `full`
- `empty`
- `wrap_bit`

### 6.5 Testbench Strategy

The testbench fills the FIFO to capacity and checks that `full` becomes 1.

Expected failure example:

```text
[FAIL] cycle=12 signal=full expected=1 actual=0 message="full flag ignores wrap-around state"
```

### 6.6 Suspicious Region

The ground truth suspicious region should point to the combinational or continuous assignment logic that computes `full`.

Expected region type:

```text
assign
```

or:

```text
combinational_always
```

## 7. Case 3 Detailed Design: `vending_machine_fsm_bug`

### 7.1 Purpose

This case tests whether AIRTLDebug can handle controller and FSM bugs.

### 7.2 Intended Correct Behavior

When accumulated coin value reaches the price, `dispense` should be asserted in the correct state or cycle.

### 7.3 Buggy Behavior

The buggy RTL either misses a transition or asserts `dispense` in the wrong state or cycle.

### 7.4 Required Signals

Recommended signals:

- `clk`
- `reset`
- `coin`
- `state`
- `next_state`
- `credit`
- `dispense`
- `refund`

### 7.5 Testbench Strategy

The testbench inserts enough coin value to reach the price, then checks whether `dispense` is asserted at the expected cycle.

Expected failure example:

```text
[FAIL] cycle=9 signal=dispense expected=1 actual=0 message="dispense was not asserted after enough credit"
```

### 7.6 Suspicious Region

The ground truth suspicious region should point to the FSM transition block or output logic block.

Expected region type:

```text
case
```

or:

```text
sequential_always
```

or:

```text
combinational_always
```

## 8. `case_loader.py` Detailed Design

### 8.1 Responsibility

`case_loader.py` reads all benchmark files and returns structured data.

It does not run simulation, parse logs, extract RTL context, call LLM, or write reports.

### 8.2 Public API

Recommended function:

```python
def load_case(case_path: str | Path) -> dict:
    ...
```

### 8.3 Input

```text
benchmarks/<case_name>/
```

### 8.4 Output

```json
{
  "case_name": "counter_off_by_one",
  "case_path": "benchmarks/counter_off_by_one",
  "files": {
    "buggy_rtl_path": "benchmarks/counter_off_by_one/design_buggy.sv",
    "fixed_rtl_path": "benchmarks/counter_off_by_one/design_fixed.sv",
    "testbench_path": "benchmarks/counter_off_by_one/tb.sv",
    "spec_path": "benchmarks/counter_off_by_one/spec.md",
    "expected_root_cause_path": "benchmarks/counter_off_by_one/expected_root_cause.md",
    "ground_truth_path": "benchmarks/counter_off_by_one/ground_truth.json"
  },
  "buggy_rtl": "...",
  "fixed_rtl": "...",
  "testbench": "...",
  "spec": "...",
  "expected_root_cause": "...",
  "ground_truth": {}
}
```

### 8.5 Error Handling

| Condition | Behavior |
|---|---|
| Case directory missing | Raise `FileNotFoundError` |
| Required file missing | Raise `FileNotFoundError` and name the missing file |
| `ground_truth.json` invalid JSON | Raise `ValueError` |
| `case_name` mismatch | Raise `ValueError` |

### 8.6 Unit Tests

Minimum tests:

- Load valid case.
- Missing `design_buggy.sv` raises error.
- Invalid `ground_truth.json` raises error.
- `ground_truth.case_name` mismatch raises error.

## 9. `sim_runner.py` Detailed Design

### 9.1 Responsibility

`sim_runner.py` compiles and runs RTL simulation using Icarus Verilog.

It does not parse failure details beyond determining broad status.

### 9.2 Public API

Recommended functions:

```python
def run_buggy_simulation(case_data: dict, output_dir: str | Path) -> dict:
    ...

def run_fixed_simulation(case_data: dict, output_dir: str | Path) -> dict:
    ...

def run_simulation(
    rtl_path: str | Path,
    tb_path: str | Path,
    output_dir: str | Path,
    output_name: str
) -> dict:
    ...
```

### 9.3 Compile Command

```bash
iverilog -g2012 -o outputs/<case_name>/<output_name>.out \
  benchmarks/<case_name>/design_buggy.sv \
  benchmarks/<case_name>/tb.sv
```

For fixed RTL:

```bash
iverilog -g2012 -o outputs/<case_name>/sim_fixed.out \
  benchmarks/<case_name>/design_fixed.sv \
  benchmarks/<case_name>/tb.sv
```

### 9.4 Run Command

```bash
vvp outputs/<case_name>/<output_name>.out
```

### 9.5 Output JSON

```json
{
  "status": "FAIL",
  "compile_status": "PASS",
  "run_status": "FAIL",
  "rtl_path": "benchmarks/counter_off_by_one/design_buggy.sv",
  "tb_path": "benchmarks/counter_off_by_one/tb.sv",
  "sim_executable": "outputs/counter_off_by_one/sim_buggy.out",
  "log_path": "outputs/counter_off_by_one/buggy_sim.log",
  "returncode_compile": 0,
  "returncode_run": 0,
  "stdout": "...",
  "stderr": "",
  "command_compile": ["iverilog", "-g2012", "-o", "...", "...", "..."],
  "command_run": ["vvp", "..."]
}
```

### 9.6 Status Rules

| Condition | `status` |
|---|---|
| Compile command returns non-zero | `COMPILE_ERROR` |
| Compile succeeds, run command returns non-zero | `RUNTIME_ERROR` |
| Log contains `[PASS]` | `PASS` |
| Log contains `[FAIL]` | `FAIL` |
| No `[PASS]` and no `[FAIL]` | `RUNTIME_ERROR` |

### 9.7 Log Files

Buggy simulation log:

```text
outputs/<case_name>/buggy_sim.log
```

Fixed simulation log:

```text
outputs/<case_name>/fixed_sim.log
```

The log file should include both stdout and stderr.

### 9.8 Error Handling

| Condition | Behavior |
|---|---|
| `iverilog` not found | Return `COMPILE_ERROR` with clear message |
| `vvp` not found | Return `RUNTIME_ERROR` with clear message |
| Timeout | Return `RUNTIME_ERROR` and include timeout message |
| Output directory missing | Create it |

### 9.9 Unit Tests

Minimum tests:

- Compile and run a known passing case.
- Compile and run a known failing case.
- Missing RTL path returns or raises clear error.
- Compile error is reported as `COMPILE_ERROR`.
- Log file is created.

## 10. `log_parser.py` Detailed Design

### 10.1 Responsibility

`log_parser.py` converts simulation logs into structured failure information.

It does not run simulation or inspect RTL source code.

### 10.2 Public API

Recommended functions:

```python
def parse_simulation_log(log_text: str) -> dict:
    ...

def parse_simulation_log_file(log_path: str | Path) -> dict:
    ...
```

### 10.3 Primary Regex

The parser should recognize:

```text
[FAIL] cycle=17 signal=done expected=0 actual=1 message="done asserted too early"
```

Recommended regex concept:

```text
^\[FAIL\]\s+cycle=(\d+)\s+signal=([A-Za-z_][A-Za-z0-9_$]*)\s+expected=([^\s]+)\s+actual=([^\s]+)\s+message="(.*)"\s*$
```

### 10.4 PASS Detection

If log contains:

```text
[PASS] all checks passed
```

then output:

```json
{
  "status": "PASS",
  "failure_cycle": null,
  "failed_signal": null,
  "expected": null,
  "actual": null,
  "message": "all checks passed",
  "raw_failure_line": null
}
```

### 10.5 FAIL Detection

If structured fail line is found:

```json
{
  "status": "FAIL",
  "failure_cycle": 17,
  "failed_signal": "done",
  "expected": "0",
  "actual": "1",
  "message": "done asserted too early",
  "raw_failure_line": "[FAIL] cycle=17 signal=done expected=0 actual=1 message=\"done asserted too early\""
}
```

### 10.6 Fallback Detection

If simulation status is failed but no structured failure message exists:

```json
{
  "status": "FAIL",
  "failure_cycle": null,
  "failed_signal": null,
  "expected": null,
  "actual": null,
  "message": "Simulation failed, but no structured failure message was found.",
  "raw_failure_line": null
}
```

`parsed_failure.status` must be one of: `PASS`, `FAIL`, `UNKNOWN`.

### 10.7 Output File

`rtl_debug_agent.py` writes parser output to:

```text
outputs/<case_name>/parsed_failure.json
```

### 10.8 Error Handling

| Condition | Behavior |
|---|---|
| Empty log | Return fallback `FAIL` or `UNKNOWN` depending on simulation status |
| Multiple `[FAIL]` lines | Use first failure and store all failure lines in `all_failure_lines` |
| Malformed `[FAIL]` line | Return fallback and preserve raw line |

### 10.9 Unit Tests

Minimum tests:

- Parse valid `[FAIL]` line.
- Parse `[PASS]` log.
- Parse malformed fail line.
- Parse multiple fail lines and keep first.
- Parse log with binary expected and actual values.

## 11. `rtl_extractor.py` Detailed Design

### 11.1 Responsibility

`rtl_extractor.py` extracts suspicious RTL signals and code blocks from `design_buggy.sv`.

It uses text-based extraction. It is not a full SystemVerilog parser.

### 11.2 Public API

Recommended functions:

```python
def extract_context(
    rtl_text: str,
    parsed_failure: dict,
    file_name: str = "design_buggy.sv"
) -> dict:
    ...
```

Optional helper functions:

```python
def find_signal_occurrences(lines: list[str], signal: str) -> list[int]:
    ...

def extract_enclosing_block(lines: list[str], line_index: int) -> dict:
    ...

def infer_block_type(block_text: str) -> str:
    ...

def collect_suspicious_signals(rtl_text: str, parsed_failure: dict) -> list[str]:
    ...
```

### 11.3 Input

```json
{
  "status": "FAIL",
  "failure_cycle": 17,
  "failed_signal": "done",
  "expected": "0",
  "actual": "1",
  "message": "done asserted too early"
}
```

### 11.4 Output

```json
{
  "suspicious_signals": ["done", "count", "enable"],
  "suspicious_code_blocks": [
    {
      "type": "sequential_always",
      "file": "design_buggy.sv",
      "start_line": 23,
      "end_line": 35,
      "code": "always_ff @(posedge clk) begin\n  ...\nend",
      "matched_signals": ["done", "count"]
    }
  ],
  "extraction_warnings": []
}
```

### 11.5 Signal Extraction Strategy

The extractor should prioritize:

1. The failed signal.
2. Identifiers assigned in the extracted block.
3. Identifiers used on the RHS of assignments related to the failed signal.
4. Identifiers appearing in conditions that guard the failed signal assignment.

It should not blindly include every identifier in the extracted block.

Minimum required behavior:

1. If `failed_signal` is not null, include it.
2. Search `design_buggy.sv` for occurrences of `failed_signal`.
3. Extract enclosing blocks around those occurrences.
4. Collect suspicious signals using the priority rules above.
5. Filter out SystemVerilog keywords.

The keyword filter is a basic filter only. It does not mean every remaining non-keyword identifier should be added to `suspicious_signals`.

Recommended keyword filter:

```text
module, endmodule, input, output, wire, logic, reg, always, always_ff,
always_comb, assign, begin, end, if, else, case, endcase, default,
posedge, negedge, parameter, localparam
```

### 11.6 Block Extraction Priority

When a signal occurrence is found, extract the smallest useful enclosing block using this priority:

1. `always_ff` or `always @(posedge ...)`
2. `always_comb` or `always @(*)`
3. `assign` statement
4. `case ... endcase`
5. `if ... begin ... end`
6. fallback window around matched line

### 11.6.1 Block Boundary Rule

The extractor uses a lightweight text-based heuristic rather than a full SystemVerilog parser. For `always` blocks, it should find the block start line and then scan forward while maintaining a simple `begin` / `end` nesting counter. The block ends when the nesting counter returns to zero. If the block has no explicit `begin/end`, the extractor falls back to a small context window.

### 11.7 Block Type Classification

| Pattern | Type |
|---|---|
| `always_ff` | `sequential_always` |
| `always @(posedge` or `always @(negedge` | `sequential_always` |
| `always_comb` | `combinational_always` |
| `always @(*)` | `combinational_always` |
| `assign` | `assign` |
| `case` and `endcase` | `case` |
| fallback nearby lines | `context_window` |

### 11.8 Line Number Rules

- Use 1-based line numbers in output.
- Preserve original RTL text exactly in `code`.
- `start_line` and `end_line` are inclusive.

### 11.9 Deduplication Rules

Two blocks are duplicates if they have the same:

```text
file, start_line, end_line, type
```

If duplicate blocks are found, keep one and merge `matched_signals`.

### 11.10 Fallback Behavior

If `failed_signal` is null:

```json
{
  "suspicious_signals": [],
  "suspicious_code_blocks": [],
  "extraction_warnings": [
    "No failed signal was available in parsed failure. RTL context extraction was skipped."
  ]
}
```

If signal is not found in RTL:

```json
{
  "suspicious_signals": ["done"],
  "suspicious_code_blocks": [],
  "extraction_warnings": [
    "Failed signal 'done' was not found in design_buggy.sv."
  ]
}
```

### 11.11 Output File

`rtl_debug_agent.py` writes extractor output to:

```text
outputs/<case_name>/extracted_context.json
```

### 11.12 Unit Tests

Minimum tests:

- Extract `always_ff` block for `done`.
- Extract `assign` statement for `full`.
- Extract `case` block for `state`.
- Return warning when failed signal is null.
- Return warning when signal does not exist.
- Deduplicate repeated block results.

## 12. `rtl_debug_agent.py` Detailed Design

### 12.1 Responsibility

`rtl_debug_agent.py` is the CLI entry point and pipeline coordinator.

It should keep business logic inside modules and only orchestrate the flow.

### 12.2 Supported CLI Arguments

```text
--case <path>          Required for single-case mode
--output <path>        Reserved for B-side Markdown debug report output
--model <name>         Optional, default may be mock or gemini depending on B-side
--fix-check            Optional, run design_fixed.sv simulation
--no-llm               Optional, skip LLM and report only intermediate artifacts
--interactive          Optional, enter interactive mode
--output-dir <path>    Optional, default outputs/<case_name>
```

Output argument responsibilities:

- A-side must support `--output-dir` for generated logs and JSON artifacts.
- `--output` is reserved for B-side report generation.
- If `--no-llm` is enabled, `--output` can be ignored or only recorded in `intermediate.json`.
- A-side guaranteed outputs are:
  - `buggy_sim.log`
  - `fixed_sim.log` if `--fix-check` is enabled
  - `parsed_failure.json`
  - `extracted_context.json`
  - `intermediate.json`

### 12.3 Main Pipeline

Algorithm:

```text
1. Parse CLI arguments.
2. Load benchmark case with case_loader.load_case.
3. Create outputs/<case_name>/.
4. Run buggy RTL simulation with sim_runner.run_buggy_simulation.
5. Save buggy simulation log.
6. Parse buggy simulation log with log_parser.
7. Save parsed_failure.json.
8. Extract RTL context with rtl_extractor.
9. Save extracted_context.json.
10. If --fix-check is enabled, run fixed RTL simulation.
11. Build intermediate.json.
12. If --no-llm is enabled, stop after intermediate.json.
13. If B-side modules are available, call prompt builder, LLM client, and report writer.
14. If --interactive is enabled, show user-guided menu.
```

### 12.4 Intermediate JSON Output

Output path:

```text
outputs/<case_name>/intermediate.json
```

Schema:

```json
{
  "case_name": "counter_off_by_one",
  "case_path": "benchmarks/counter_off_by_one",
  "spec": "...",
  "buggy_rtl": "...",
  "testbench": "...",
  "simulation": {
    "buggy": {
      "status": "FAIL",
      "log_path": "outputs/counter_off_by_one/buggy_sim.log"
    },
    "fixed": {
      "status": "PASS",
      "log_path": "outputs/counter_off_by_one/fixed_sim.log"
    }
  },
  "parsed_failure": {
    "status": "FAIL",
    "failure_cycle": 17,
    "failed_signal": "done",
    "expected": "0",
    "actual": "1",
    "message": "done asserted too early"
  },
  "extracted_context": {
    "suspicious_signals": ["count", "done", "enable"],
    "suspicious_code_blocks": []
  },
  "ground_truth": {},
  "fix_verification": {
    "enabled": true,
    "status": "PASS"
  }
}
```

### 12.5 Exit Code Rules

| Condition | Exit code |
|---|---|
| Pipeline completed, even if buggy simulation fails as expected | 0 |
| Case loading error | 1 |
| Compile error | 2 |
| Runtime error | 3 |
| Internal tool error | 4 |

A buggy RTL simulation returning `[FAIL]` is not a CLI failure. It is the expected input to the debug flow.

### 12.6 `--no-llm` Behavior

When `--no-llm` is set:

- Run case loader.
- Run simulation.
- Run log parser.
- Run RTL extractor.
- Optionally run fix verification if `--fix-check` is also set.
- Write intermediate JSON and other A-side guaranteed outputs under `--output-dir`.
- Do not import or call `llm_client.py`.
- Do not require `--output`. If provided, it may be recorded in `intermediate.json` but no Markdown report is generated by A-side.
- A simple no-LLM text summary may be printed to the terminal.

### 12.7 `--fix-check` Behavior

When `--fix-check` is set:

- Run `design_fixed.sv` with the same `tb.sv`.
- Save `fixed_sim.log`.
- Store result in `intermediate.json`.
- Do not modify any RTL file.

When `--fix-check` is not set:

- Set `fix_verification.enabled` to `false`.
- Set `fix_verification.status` to `null`.

### 12.8 Interactive Mode

Interactive mode should use data already generated by the pipeline.

Menu:

```text
AIRTLDebug found a simulation failure.
Case: <case_name>
Failure cycle: <cycle>
Failed signal: <signal>
Expected: <expected>
Actual: <actual>

Choose next action:
1. Show failure log
2. Show suspicious RTL block
3. Ask LLM for root cause
4. Ask LLM to explain signal relation
5. Run fixed RTL verification
6. Export debug report
0. Exit
```

A-side required actions:

| Option | A-side responsibility |
|---|---|
| 1 | Print `buggy_sim.log` |
| 2 | Print extracted suspicious RTL blocks |
| 5 | Run fixed RTL verification |
| 0 | Exit |

B-side related actions:

| Option | B-side responsibility |
|---|---|
| 3 | LLM root cause |
| 4 | LLM signal relation explanation |
| 6 | report writer |

If B-side modules are not implemented yet, options 3, 4, and 6 should print a clear message such as:

```text
LLM/report module is not available in this build.
```

## 13. `scripts/run_all_cases.sh` Detailed Design

### 13.1 Responsibility

Run all benchmark cases with one command.

### 13.2 Command

```bash
bash scripts/run_all_cases.sh
```

### 13.3 Required Behavior

The script should run:

```bash
python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm \
  --fix-check

python src/rtl_debug_agent.py \
  --case benchmarks/fifo_full_flag_bug \
  --no-llm \
  --fix-check

python src/rtl_debug_agent.py \
  --case benchmarks/vending_machine_fsm_bug \
  --no-llm \
  --fix-check
```

### 13.4 Output

Each case should generate:

```text
outputs/<case_name>/buggy_sim.log
outputs/<case_name>/fixed_sim.log
outputs/<case_name>/parsed_failure.json
outputs/<case_name>/extracted_context.json
outputs/<case_name>/intermediate.json
```

### 13.5 Error Handling

Recommended default:

- Continue running all benchmark cases and summarize results at the end.
- Stop only when the Python entry point or required simulation tools are missing.
- Do not treat buggy simulation `FAIL` as script failure.
- Print summary after all cases.

Summary format:

```text
Case                       Buggy RTL    Fixed RTL
counter_off_by_one          FAIL         PASS
fifo_full_flag_bug          FAIL         PASS
vending_machine_fsm_bug     FAIL         PASS
```

## 14. JSON File Summary

### 14.0 Status Field Conventions

| Field | Allowed values |
|---|---|
| `parsed_failure.status` | `PASS`, `FAIL`, `UNKNOWN` |
| `simulation.buggy.status` | `PASS`, `FAIL`, `COMPILE_ERROR`, `RUNTIME_ERROR` |
| `simulation.fixed.status` | `PASS`, `FAIL`, `COMPILE_ERROR`, `RUNTIME_ERROR` |
| `fix_verification.status` | `PASS`, `FAIL`, `COMPILE_ERROR`, `RUNTIME_ERROR`, or `null` when disabled |
| `extracted_context.suspicious_code_blocks[*].type` | `sequential_always`, `combinational_always`, `assign`, `case`, `context_window` |

### 14.1 `parsed_failure.json`

```json
{
  "status": "FAIL",
  "failure_cycle": 17,
  "failed_signal": "done",
  "expected": "0",
  "actual": "1",
  "message": "done asserted too early",
  "raw_failure_line": "[FAIL] cycle=17 signal=done expected=0 actual=1 message=\"done asserted too early\""
}
```

### 14.2 `extracted_context.json`

```json
{
  "suspicious_signals": ["done", "count", "enable"],
  "suspicious_code_blocks": [
    {
      "type": "sequential_always",
      "file": "design_buggy.sv",
      "start_line": 23,
      "end_line": 35,
      "code": "...",
      "matched_signals": ["done", "count"]
    }
  ],
  "extraction_warnings": []
}
```

### 14.3 `intermediate.json`

```json
{
  "case_name": "counter_off_by_one",
  "case_path": "benchmarks/counter_off_by_one",
  "spec": "...",
  "buggy_rtl": "...",
  "testbench": "...",
  "simulation": {
    "buggy": {
      "status": "FAIL",
      "log_path": "outputs/counter_off_by_one/buggy_sim.log"
    },
    "fixed": {
      "status": "PASS",
      "log_path": "outputs/counter_off_by_one/fixed_sim.log"
    }
  },
  "parsed_failure": {},
  "extracted_context": {},
  "ground_truth": {},
  "fix_verification": {
    "enabled": true,
    "status": "PASS"
  }
}
```

## 15. Testing Plan

### 15.1 Unit Tests

Recommended folder:

```text
tests/
  test_case_loader.py
  test_sim_runner.py
  test_log_parser.py
  test_rtl_extractor.py
```

Minimum unit test coverage:

| Module | Required tests |
|---|---|
| `case_loader.py` | valid case, missing file, invalid JSON |
| `sim_runner.py` | passing sim, failing sim, compile error |
| `log_parser.py` | PASS, structured FAIL, malformed FAIL |
| `rtl_extractor.py` | always block, assign, case, fallback |

### 15.2 Integration Tests

Recommended commands:

```bash
python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm \
  --fix-check

python src/rtl_debug_agent.py \
  --case benchmarks/fifo_full_flag_bug \
  --no-llm \
  --fix-check

python src/rtl_debug_agent.py \
  --case benchmarks/vending_machine_fsm_bug \
  --no-llm \
  --fix-check
```

Expected for every case:

- Buggy simulation status is `FAIL`.
- Fixed simulation status is `PASS`.
- `parsed_failure.json` exists.
- `extracted_context.json` exists.
- `intermediate.json` exists.

### 15.3 Manual Inspection Checklist

For each case:

- Failure cycle is reasonable.
- Failed signal matches the intended bug.
- Expected and actual values are correct.
- Extracted RTL block contains the real buggy logic.
- Ground truth suspicious region line numbers match `design_buggy.sv`.
- Fixed RTL passes the same testbench.

## 16. Error Message Design

### 16.1 Missing File

```text
[ERROR] Required benchmark file is missing: benchmarks/<case_name>/design_buggy.sv
```

### 16.2 Compile Error

```text
[ERROR] Icarus Verilog compile failed for case <case_name>.
See outputs/<case_name>/buggy_sim.log
```

### 16.3 Parser Fallback

```text
[WARN] Simulation failed, but no structured failure message was found.
```

### 16.4 Extractor Fallback

```text
[WARN] Failed signal '<signal>' was not found in design_buggy.sv.
```

### 16.5 Missing LLM Module in Interactive Mode

```text
[WARN] LLM/report module is not available in this build.
```

## 17. A and B Interface Contract

### 17.1 Files A Provides to B

A must provide these files:

```text
outputs/<case_name>/buggy_sim.log
outputs/<case_name>/fixed_sim.log
outputs/<case_name>/parsed_failure.json
outputs/<case_name>/extracted_context.json
outputs/<case_name>/intermediate.json
```

### 17.2 Fields B Can Depend On

B can depend on:

```text
case_name
spec
buggy_rtl
testbench
simulation.buggy.status
simulation.buggy.log_path
parsed_failure.status
parsed_failure.failure_cycle
parsed_failure.failed_signal
parsed_failure.expected
parsed_failure.actual
parsed_failure.message
extracted_context.suspicious_signals
extracted_context.suspicious_code_blocks
ground_truth
fix_verification.enabled
fix_verification.status
```

### 17.3 Fields B Should Not Depend On

B should not depend on:

- Internal helper function names.
- Temporary subprocess return code fields.
- Exact extractor heuristic implementation.
- Ordering of suspicious signals unless documented later.

## 18. Implementation Order for A

### Phase A1: Benchmark Skeleton

1. Create three benchmark folders.
2. Add all required files.
3. Make buggy versions fail.
4. Make fixed versions pass.
5. Add structured failure messages.

### Phase A2: Simulation Runner

1. Implement `sim_runner.py`.
2. Verify one case.
3. Verify all cases.
4. Save logs under `outputs/<case_name>/`.

### Phase A3: Log Parser

1. Implement parser for fixed `[FAIL]` format.
2. Implement `[PASS]` parser.
3. Implement fallback.
4. Save `parsed_failure.json`.

### Phase A4: RTL Extractor

1. Find failed signal occurrences.
2. Extract enclosing blocks.
3. Classify block type.
4. Deduplicate blocks.
5. Save `extracted_context.json`.

### Phase A5: CLI Flow

1. Implement `--case`.
2. Implement `--no-llm`.
3. Implement `--fix-check`.
4. Implement `--output-dir`.
5. Generate `intermediate.json`.

### Phase A6: Interactive and Batch

1. Implement A-side interactive actions.
2. Implement `scripts/run_all_cases.sh`.
3. Verify from clean repo state.

## 19. Definition of Done for A

A-side work is complete when all conditions hold:
- `design_buggy.sv` and `design_fixed.sv` use the same top module name for each benchmark.
- Three benchmark cases exist.
- Every case has `design_buggy.sv`, `design_fixed.sv`, `tb.sv`, `spec.md`, `expected_root_cause.md`, and `ground_truth.json`.
- Every buggy RTL simulation produces `[FAIL]`.
- Every fixed RTL simulation produces `[PASS]`.
- `case_loader.py` loads all cases.
- `sim_runner.py` runs buggy and fixed simulations.
- `log_parser.py` generates `parsed_failure.json`.
- `rtl_extractor.py` generates `extracted_context.json`.
- `rtl_debug_agent.py --no-llm --fix-check` works for every case.
- `scripts/run_all_cases.sh` works.
- Intermediate JSON is stable enough for B-side modules.
- No API key, binary, `.out`, `.vcd`, `.o`, core dump, or generated output folder is committed.

## 20. Implementation Decisions

1. **Testing scope**
   Decision: Include lightweight unit tests if time allows, but command-line integration tests are required.

2. **Interactive mode**
   Decision: Implement a minimal A-side interactive menu because the project topic emphasizes user interaction.

3. **A-side report output**
   Decision: A only guarantees JSON intermediate output. A simple no-LLM text summary may be printed to the terminal, but Markdown report generation belongs to B.

4. **Batch script failure policy**
   Decision: `scripts/run_all_cases.sh` should continue running all benchmark cases and summarize results, except when the Python entry point or required simulation tools are missing.

5. **RTL syntax compatibility**
   Decision: Prefer standard `always @(posedge clk)` and `always @(*)` blocks for maximum Icarus Verilog compatibility. The extractor still supports `always_ff` and `always_comb`.
