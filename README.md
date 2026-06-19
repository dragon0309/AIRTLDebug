# AIRTLDebug: LLM-Assisted RTL Debugging Agent

## Group Members


| Name | Email                                                 |
| ---- | ----------------------------------------------------- |
| 詹育豐  | [dra02030309@gmail.com](mailto:dra02030309@gmail.com) |
| 洪紫馨  | [a0925500592@gmail.com](mailto:a0925500592@gmail.com) |


---

## Table of Contents

1. [How to Compile, Run, and Test](#how-to-compile-run-and-test)
2. [Key Research Contributions](#key-research-contributions)
3. [Prior Work and Third-Party Packages](#prior-work-and-third-party-packages)
4. [Algorithm Overview](#algorithm-overview)
5. [Algorithm Description](#algorithm-description)
6. [Noticeable Implementation Details](#noticeable-implementation-details)
7. [Experimental Results](#experimental-results)
8. [References](#references)
9. [Demo Video](#demo-video)

---

## How to Compile, Run, and Test

### Environment Requirements


| Tool                             | Version | Purpose                                              |
| -------------------------------- | ------- | ---------------------------------------------------- |
| Python                           | >= 3.12 | Runtime                                              |
| [uv](https://docs.astral.sh/uv/) | latest  | Python dependency and virtual environment management |
| Icarus Verilog                   | latest  | RTL simulation (`iverilog` + `vvp`)                  |


### Setup (Ubuntu / WSL)

```bash
# Install Icarus Verilog
sudo apt-get update
sudo apt-get install -y iverilog

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone and setup project
cd AIRTLDebug
uv sync
```

For Gemini LLM integration, copy `.env.example` to `.env` and set `GEMINI_API_KEY`:

```bash
cp .env.example .env
# Edit .env and fill in your Gemini API key
```

### Run a Single Benchmark Case

```bash
# A-side only (no LLM, simulation + parsing + extraction)
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --no-llm \
  --fix-check

# Full pipeline with mock LLM (no API key needed)
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --model mock \
  --fix-check

# Full pipeline with Gemini (requires API key in .env)
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --model gemini \
  --fix-check
```

**Note on LLM modes:**

- `--no-llm`: Only runs the A-side pipeline (simulation + parsing + extraction). No `debug_report.md` or `full_flow_prompt.txt` will be generated.
- `--model mock`: Runs the full pipeline using a deterministic mock backend that derives its analysis from `ground_truth.json`. No API key is needed, but the output is not a real LLM analysis.
- `--model gemini`: Runs the full pipeline with the real Gemini 2.5 Flash Lite API. **Requires a valid `GEMINI_API_KEY` in `.env`.** This is the only mode that produces genuine LLM root-cause analysis.

The `debug_report.md` files under `outputs/` were generated using `--model mock` (deterministic mock backend). The real Gemini API–generated reports are available in `docs/sample_reports/`.

Generated output files are placed under `outputs/<case_name>/`:

```
outputs/counter_off_by_one/
├── buggy_sim.log            # Buggy RTL simulation log
├── fixed_sim.log            # Fixed RTL simulation log
├── sim_buggy.out            # Compiled buggy simulation executable
├── sim_fixed.out            # Compiled fixed simulation executable
├── parsed_failure.json      # Structured failure information
├── extracted_context.json   # Suspicious signals and RTL blocks
├── intermediate.json        # Full pipeline handoff data
├── full_flow_prompt.txt     # LLM prompt (when LLM is enabled)
└── debug_report.md          # Markdown debug report (when LLM is enabled)
```

### Run All Benchmark Cases

```bash
# A-side batch run (no LLM)
bash scripts/run_all_cases.sh

# Full experiment with mock LLM + CSV summary
uv run python scripts/run_experiments.py
```

### Interactive Mode

```bash
uv run python src/rtl_debug_agent.py \
  --case benchmarks/counter_off_by_one \
  --interactive \
  --fix-check
```

The interactive menu provides:

```
1. Show buggy simulation log
2. Show extracted suspicious RTL blocks
3. Generate LLM analysis
4. Generate report
5. Run fixed RTL verification
6. Full analysis with LLM
0. Exit
```

### Run Tests

```bash
uv run pytest tests/ -v
```

Expected result: **25 passed** across 7 test files.


| Test File                 | Tests | Coverage                                                  |
| ------------------------- | ----- | --------------------------------------------------------- |
| `test_scaffold.py`        | 1     | Import smoke test                                         |
| `test_case_loader.py`     | 4     | Valid load, missing files, bad JSON, name mismatch        |
| `test_log_parser.py`      | 5     | FAIL/PASS parsing, malformed lines, binary values         |
| `test_rtl_extractor.py`   | 6     | Block extraction (always/assign/case), null signal, dedup |
| `test_sim_runner.py`      | 4     | Buggy FAIL, fixed PASS, compile error, missing iverilog   |
| `test_rtl_debug_agent.py` | 2     | CLI subprocess, interactive smoke                         |
| `test_integration.py`     | 3     | Full pipeline for all 3 benchmarks (parametrized)         |


Code quality checks:

```bash
uv run ruff check src tests   # Linting
uv run mypy src                # Type checking
```

### CLI Exit Codes


| Code | Meaning                                                                 |
| ---- | ----------------------------------------------------------------------- |
| 0    | Success (a buggy simulation `FAIL` is the expected input, not an error) |
| 1    | Case load error                                                         |
| 2    | Verilog compile error                                                   |
| 3    | Unexpected runtime error                                                |
| 4    | Internal error                                                          |


---

## Key Research Contributions

1. **End-to-end LLM-assisted RTL debugging pipeline.** We designed and implemented a complete automated flow that takes a buggy SystemVerilog design, simulates it, parses structured failure logs, extracts suspicious RTL blocks via heuristics, constructs a structured prompt, invokes an LLM for root-cause analysis, and generates a human-readable Markdown debug report.
2. **Text-based RTL context extraction heuristics.** Instead of requiring a full SystemVerilog parser, we developed a lightweight text-based extractor that locates the failed signal in the RTL source, walks backward to find enclosing `always`/`assign`/`case` blocks, tracks `begin`/`end` nesting to determine block boundaries, classifies block types, and collects suspicious signals by analyzing identifiers within the extracted code. This approach is practical and sufficient for the debugging use case without the overhead of a full parser.
3. **Structured testbench output contract.** We defined a `[FAIL] cycle=<N> signal=<name> expected=<val> actual=<val> message="<text>"` / `[PASS] all checks passed` protocol for testbench output. This structured format enables reliable automated parsing and serves as the bridge between simulation and the debugging pipeline.
4. **Stable JSON intermediate interface for A/B side decoupling.** The pipeline produces a well-defined `intermediate.json` that encapsulates all simulation evidence, parsed failures, extracted context, and ground truth. This allows the LLM prompt builder, LLM client, and report writer modules to work independently from the simulation/extraction modules.
5. **Dual LLM backend (mock + Gemini).** We implemented both a deterministic mock backend (using pre-defined ground truth for reproducible, API-free testing) and a real Gemini 2.5 Flash Lite backend. This design ensures the system is always demonstrable regardless of API availability.
6. **Three RTL bug benchmarks covering different bug categories.** We created benchmarks spanning counter logic errors, FIFO pointer/flag bugs, and FSM output timing issues, providing diverse test scenarios for the debugging pipeline.

---

## Prior Work and Third-Party Packages

The following components were **not** developed as part of this project and should not be counted as contributions:

### Third-Party Runtime Dependencies


| Package                                                              | Version  | Purpose                          | License    |
| -------------------------------------------------------------------- | -------- | -------------------------------- | ---------- |
| [google-genai](https://pypi.org/project/google-genai/)               | >= 2.8.0 | Gemini API client (new SDK)      | Apache 2.0 |
| [google-generativeai](https://pypi.org/project/google-generativeai/) | >= 0.8.6 | Gemini API client (legacy SDK)   | Apache 2.0 |
| [python-dotenv](https://pypi.org/project/python-dotenv/)             | >= 1.2.2 | `.env` file loading for API keys | BSD        |


### Third-Party Development Dependencies


| Package                                    | Version    | Purpose             |
| ------------------------------------------ | ---------- | ------------------- |
| [pytest](https://pypi.org/project/pytest/) | >= 8.0.0   | Testing framework   |
| [ruff](https://pypi.org/project/ruff/)     | >= 0.15.14 | Python linter       |
| [mypy](https://pypi.org/project/mypy/)     | >= 2.1.0   | Static type checker |


### External Tools


| Tool                                                   | Purpose                                                              |
| ------------------------------------------------------ | -------------------------------------------------------------------- |
| [Icarus Verilog](http://iverilog.icarus.com/)          | Open-source Verilog simulation (`iverilog` compiler + `vvp` runtime) |
| [uv](https://docs.astral.sh/uv/)                       | Python package and environment manager                               |
| [Google Gemini 2.5 Flash Lite](https://ai.google.dev/) | External LLM used for root-cause analysis                            |


### Prior Work Statement

All code in the `src/`, `tests/`, `scripts/`, and `benchmarks/` directories was written from scratch for this semester's SoCV final project. No code was reused from prior semesters or other courses. The RTL benchmark designs (counter, FIFO, vending machine FSM) are original creations for this project. The LLM prompt template and report structure were designed specifically for the RTL debugging use case.

Generated artifacts under `outputs/` and `docs/sample_reports/` are execution results produced by this project, not separate research contributions. The external Gemini model and the third-party tools/packages listed above are also not counted as project contributions.

---

## Algorithm Overview

### Pipeline Flow Chart

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AIRTLDebug Pipeline                          │
└─────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │  Benchmark   │  benchmarks/<case>/
  │  Case Input  │  (design_buggy.sv, design_fixed.sv, tb.sv,
  └──────┬───────┘   spec.md, ground_truth.json)
         │
         ▼
  ┌──────────────┐
  │ Case Loader  │  Validate required files, parse ground_truth.json
  │              │  Return structured case data
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  iverilog -g2012 → vvp
  │  Simulation  │  Compile and run buggy RTL with testbench
  │   Runner     │  → buggy_sim.log (FAIL expected)
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  Regex: [FAIL] cycle=N signal=X expected=E actual=A
  │  Log Parser  │  Extract structured failure details
  │              │  → parsed_failure.json
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  Find signal occurrences → walk backward to block
  │    RTL       │  start → track begin/end nesting → classify type
  │  Extractor   │  → extracted_context.json
  └──────┬───────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼ (optional: --fix-check)
  ┌──────┐  ┌──────────────┐
  │ Build│  │ Run fixed    │  iverilog + vvp on design_fixed.sv
  │inter-│  │ RTL verify   │  → fixed_sim.log (PASS expected)
  │media-│  └──────┬───────┘
  │te.   │         │
  │json  │◄────────┘
  └──┬───┘
     │
     ▼ (if LLM enabled: --model mock|gemini)
  ┌──────────────┐  Assemble spec + failure + suspicious signals +
  │   Prompt     │  RTL blocks into structured LLM prompt
  │   Builder    │  → full_flow_prompt.txt
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  mock: deterministic from ground_truth.json
  │  LLM Client  │  gemini: call Gemini 2.5 Flash Lite API
  │              │  → JSON analysis (root_cause, suggested_fix, ...)
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐  Combine simulation result + failure evidence +
  │   Report     │  extracted context + LLM analysis + fix verify
  │   Writer     │  → debug_report.md
  └──────────────┘
```

### RTL Extractor Pseudo Code

```
FUNCTION extract_context(rtl_text, parsed_failure):
    failed_signal ← parsed_failure.failed_signal
    IF failed_signal is NULL:
        RETURN empty result with warning

    lines ← split rtl_text into lines
    occurrences ← find_signal_occurrences(lines, failed_signal)
    IF occurrences is empty:
        RETURN result with warning "signal not found"

    blocks ← empty list
    seen ← empty set

    FOR EACH line_no IN occurrences:
        block_start ← walk backward from line_no to find
                       "always", "assign", or "case" keyword
        (start, end) ← extract_with_nesting(lines, block_start)
            IF block has "begin":
                count begin/end nesting until balanced
            ELSE:
                scan forward until next block or blank line
        block_type ← classify by leading keyword
            always_ff / always @(posedge) → "sequential_always"
            always_comb / always @(*)     → "combinational_always"
            assign                        → "assign"
            case                          → "case"
            otherwise                     → "context_window"
        key ← (file, start, end, type)
        IF key IN seen:
            merge matched_signals into existing block
        ELSE:
            add block to blocks, add key to seen

    suspicious_signals ← collect identifiers from all blocks
                         filtered against SystemVerilog keywords
    RETURN { suspicious_signals, blocks, warnings }
```

### LLM Prompt Construction Pseudo Code

```
FUNCTION build_full_flow_prompt(intermediate):
    parsed ← intermediate.parsed_failure
    context ← intermediate.extracted_context

    signals ← filter noise words from context.suspicious_signals
    blocks_text ← format each block as:
        "File: ..., Lines: ..., Type: ..., Code: ```systemverilog ... ```"

    prompt ← concatenate:
        1. System role: "You are an RTL debugging assistant."
        2. Given information: spec, failure, signals, blocks
        3. Rules: base on evidence only, explain why and how
        4. Output format: JSON with bug_summary, root_cause,
           suggested_fix, evidence, confidence_score
        5. Design specification (from intermediate.spec)
        6. Parsed failure details (cycle, signal, expected, actual)
        7. Suspicious signals list
        8. Extracted RTL code blocks

    RETURN prompt
```

---

## Algorithm Description

### 1. Case Loader (`case_loader.py`)

The case loader reads a benchmark directory and validates that all 6 required files exist: `design_buggy.sv`, `design_fixed.sv`, `tb.sv`, `spec.md`, `expected_root_cause.md`, and `ground_truth.json`. It parses `ground_truth.json` and validates its structure (case name match, non-empty suspicious signals, valid suspicious regions with proper line ranges). The output is a structured dictionary containing file paths and text contents for all downstream modules.

### 2. Simulation Runner (`sim_runner.py`)

The simulation runner invokes Icarus Verilog in two phases: (1) `iverilog -g2012` compiles the RTL design and testbench into a simulation executable, and (2) `vvp` runs the executable. Each phase has a 30-second timeout. The runner determines the overall simulation status by checking the log output for `[PASS]` or `[FAIL]` markers, and handles edge cases like compile errors, missing tools, and timeouts. Separate functions `run_buggy_simulation` and `run_fixed_simulation` select the appropriate RTL file.

### 3. Log Parser (`log_parser.py`)

The log parser uses a regex pattern to extract structured failure information from the `[FAIL] cycle=<N> signal=<name> expected=<val> actual=<val> message="<text>"` format. It handles multiple failure lines (uses the first match), malformed lines (returns a fallback with the raw line preserved), and `[PASS]` detection. The parser outputs a standardized dictionary with status, failure cycle, failed signal, expected/actual values, and the original failure line.

### 4. RTL Extractor (`rtl_extractor.py`)

This is the core heuristic module. Given the buggy RTL source text and the parsed failure, it:

- **Finds signal occurrences:** Searches all lines for the `failed_signal`, skipping port declarations (lines starting with `module`, `input`, `output`, `wire`, `logic`, `reg`).
- **Extracts enclosing blocks:** For each occurrence, walks backward to find the nearest `always`, `assign`, or `case` keyword. Then uses `begin`/`end` nesting analysis to determine the block's end boundary. If no `begin` is present, falls back to scanning forward until the next block start or empty line.
- **Classifies block types:** Inspects the leading construct of each block to classify it as `sequential_always`, `combinational_always`, `assign`, `case`, or `context_window`.
- **Collects suspicious signals:** Extracts all identifiers from the code blocks, filters out SystemVerilog keywords, and prepends the `failed_signal`.
- **Deduplicates:** Blocks with the same (file, start_line, end_line, type) are merged, combining their matched signal lists.

### 5. Prompt Builder (`prompt_builder.py`)

Assembles a structured LLM prompt from the intermediate data. The prompt includes the design specification, parsed failure details, filtered suspicious signals (removing noise tokens), and the extracted RTL code blocks formatted in SystemVerilog code fences. The prompt instructs the LLM to return a JSON object with `bug_summary`, `root_cause`, `suggested_fix`, `evidence`, and `confidence_score`.

### 6. LLM Client (`llm_client.py`)

Provides two backends:

- **Mock backend:** Returns a deterministic analysis derived from `ground_truth.json`, useful for reproducible testing and demonstrations without an API key.
- **Gemini backend:** Sends the constructed prompt to Gemini 2.5 Flash Lite via the `google-genai` SDK. Parses the JSON response with a fallback that handles markdown-wrapped responses or unparseable text.

### 7. Report Writer (`report_writer.py`)

Generates a 7-section Markdown debug report:

1. Simulation result (status, failure cycle, failed signal, expected vs. actual)
2. Failure evidence (raw failure line)
3. Extracted RTL context (suspicious signals and code blocks with syntax highlighting)
4. LLM root-cause analysis (summary, cause, evidence, confidence)
5. Suggested fix
6. Fix verification (whether the prepared fixed RTL passes)
7. Comparison with ground truth

---

## Noticeable Implementation Details

1. **No full SystemVerilog parser required.** The RTL extractor uses lightweight text-based heuristics (regex + nesting counter) rather than a full parser. This is a deliberate design choice: for the debugging use case, we only need to extract the code blocks relevant to the failed signal, not build a complete AST. This keeps the implementation simple and dependency-free.
2. **Structured testbench output protocol.** All testbenches follow a strict `[FAIL] cycle=... signal=... expected=... actual=... message="..."` format. This protocol bridges the gap between simulation and automated analysis, enabling reliable regex-based parsing.
3. **A/B side decoupling via `intermediate.json`.** The pipeline is split into A-side (simulation, parsing, extraction) and B-side (prompt, LLM, report). The `intermediate.json` file serves as a stable contract between them. B-side modules can be developed, tested, and swapped independently.
4. **Mock LLM for reproducibility.** The mock backend reads from `ground_truth.json` to produce deterministic results. This is essential for automated testing (all 25 pytest tests pass without API keys) and serves as a fallback when Gemini API quota is exhausted.
5. **Graceful error handling at every stage.** Missing `iverilog` returns a clear `COMPILE_ERROR` instead of crashing. Missing API keys return an informative result instead of an exception. Malformed simulation logs fall back to partial parsing. The pipeline never crashes on expected failure conditions.
6. **The tool does not auto-patch RTL.** AIRTLDebug reports a suggested fix via LLM analysis and then verifies the pre-prepared `design_fixed.sv`. This is a deliberate scope decision: automatic code patching introduces reliability risks, and verification of a known-good fix demonstrates the pipeline's correctness.
7. **Signal noise filtering.** Both the prompt builder and report writer filter out noise tokens (like `d0`, `b0`, `Bug`, `asserted`) from suspicious signals, improving the quality of LLM prompts.
8. **Comprehensive test coverage.** The 25 tests cover unit tests for each module (case loader, log parser, RTL extractor, simulation runner), CLI integration tests, and parametrized end-to-end integration tests across all 3 benchmarks.

---

## Experimental Results

### Benchmark Overview

We evaluated AIRTLDebug on three RTL bug benchmarks of varying complexity:


| Case                      | Bug Type             | Module            | Failed Signal | Failure Cycle |
| ------------------------- | -------------------- | ----------------- | ------------- | ------------- |
| `counter_off_by_one`      | Counter off-by-one   | `counter`         | `done`        | 17            |
| `fifo_full_flag_bug`      | FIFO full flag logic | `fifo`            | `full`        | 12            |
| `vending_machine_fsm_bug` | FSM output timing    | `vending_machine` | `dispense`    | 9             |


### Bug Details

**Counter Off-By-One:** The `done` signal is asserted when `count == MAX - 1` instead of `count == MAX`, causing it to go high one cycle too early.

```systemverilog
// Buggy:  done <= (count == MAX - 1);
// Fixed:  done <= (count == MAX);
```

**FIFO Full Flag Bug:** The `full` flag is computed as `(wr_ptr == rd_ptr) && !wrap_bit`, which is identical to the `empty` condition. The correct logic should check `&& wrap_bit` for full.

```systemverilog
// Buggy:  assign full = (wr_ptr == rd_ptr) && !wrap_bit;
// Fixed:  assign full = (wr_ptr == rd_ptr) && wrap_bit;
```

**Vending Machine FSM Bug:** The FSM enters `ST_DISPENSE` state but the sequential output logic never asserts `dispense` when credit reaches the price.

```systemverilog
// Buggy:  ST_DISPENSE case does not set dispense
// Fixed:  Add dispense <= 1'b1 in ST_DISPENSE
```

### A-Side Pipeline Results (Simulation + Extraction)


| Case                      | Buggy Sim | Fixed Sim | Raw Signals Extracted | Blocks Extracted                  |
| ------------------------- | --------- | --------- | --------------------- | --------------------------------- |
| `counter_off_by_one`      | FAIL      | PASS      | 15                    | 1 (`sequential_always`)           |
| `fifo_full_flag_bug`      | FAIL      | PASS      | 15                    | 2 (`sequential_always`, `assign`) |
| `vending_machine_fsm_bug` | FAIL      | PASS      | 26                    | 2 (`sequential_always`, `case`)   |


All three buggy RTL designs correctly produce `FAIL`, and all three fixed RTL designs correctly produce `PASS`. The raw signal counts above come from the `suspicious_signals` field in `outputs/<case>/extracted_context.json`; later prompt/report generation filters noisy tokens such as literal fragments and words from comments.

### B-Side LLM Results (Gemini 2.5 Flash Lite)


| Case                      | Root Cause Identified                                          | Suggested Fix Correct                     | Confidence |
| ------------------------- | -------------------------------------------------------------- | ----------------------------------------- | ---------- |
| `counter_off_by_one`      | Yes — identified `done <= (count == MAX - 1)` off-by-one       | Yes — change to `count == MAX`            | High       |
| `fifo_full_flag_bug`      | Yes — identified missing `wrap_bit` in full flag logic         | Yes — check `wrap_bit` for full           | High       |
| `vending_machine_fsm_bug` | Yes — identified missing `dispense` assertion in `ST_DISPENSE` | Yes — assert `dispense` in dispense state | High       |


The recorded Gemini run results in `docs/gemini_run_results.md` show that Gemini 2.5 Flash Lite identified the root cause and suggested the correct fix for all three benchmarks. The project also supports a deterministic `mock` backend for reproducible demonstrations without external API access, as documented in `docs/experiment_results.md`.

### Sample Debug Report Output

For `counter_off_by_one`, the generated report includes:

- **Simulation Result:** FAIL at cycle 17, signal `done`, expected `0`, actual `1`
- **Extracted Context:** `sequential_always` block at lines 11–21 containing the `done <= (count == MAX - 1)` assignment
- **LLM Analysis:** "The `done` signal is set to high when `count == MAX - 1`. According to the specification, `done` should only be asserted when `count == MAX`. Therefore, `done` is being asserted one cycle before the counter reaches its maximum value."
- **Fix Verification:** Fixed RTL simulation PASS

Sample reports for all three cases are available in `docs/sample_reports/`.

Additional experiment records are available in:

- `docs/experiment_results.md`: benchmark setup, mock-mode experiment summary, and current demo limitation notes
- `docs/gemini_run_results.md`: recorded Gemini execution commands and case-by-case results
- `docs/sample_reports/`: generated Markdown debug reports for all three benchmark cases

### Test Suite Results

```
tests/test_scaffold.py         1 passed
tests/test_case_loader.py      4 passed
tests/test_log_parser.py       5 passed
tests/test_rtl_extractor.py    6 passed
tests/test_sim_runner.py       4 passed
tests/test_rtl_debug_agent.py  2 passed
tests/test_integration.py      3 passed
─────────────────────────────────────────
Total                          25 passed
```

---

## References

1. Icarus Verilog. [http://iverilog.icarus.com/](http://iverilog.icarus.com/)
2. Google Gemini API Documentation. [https://ai.google.dev/docs](https://ai.google.dev/docs)
3. google-genai Python SDK. [https://pypi.org/project/google-genai/](https://pypi.org/project/google-genai/)
4. uv — An extremely fast Python package manager. [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/)
5. IEEE Standard for SystemVerilog — Unified Hardware Design, Specification, and Verification Language (IEEE Std 1800-2017). [https://ieeexplore.ieee.org/document/8299595](https://ieeexplore.ieee.org/document/8299595)

---

## Demo Video

> **Link:** *(To be added — please insert the demo video URL here)*

