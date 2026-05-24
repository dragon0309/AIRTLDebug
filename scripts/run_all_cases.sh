#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CASES=(
  "counter_off_by_one"
  "fifo_full_flag_bug"
  "vending_machine_fsm_bug"
)

declare -A BUGGY_STATUS
declare -A FIXED_STATUS

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "ERROR: python is not available"
  exit 1
fi

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  PYTHON=python
fi

for case_name in "${CASES[@]}"; do
  case_path="benchmarks/${case_name}"
  echo "=== Running case: ${case_name} ==="
  if ! "$PYTHON" src/rtl_debug_agent.py --case "$case_path" --no-llm --fix-check; then
    echo "WARNING: CLI returned non-zero for ${case_name}; continuing"
  fi

  intermediate="outputs/${case_name}/intermediate.json"
  if [[ -f "$intermediate" ]]; then
    BUGGY_STATUS["$case_name"]="$(
      "$PYTHON" -c "import json; d=json.load(open('$intermediate')); print(d['simulation']['buggy']['status'])"
    )"
    if [[ "$( "$PYTHON" -c "import json; d=json.load(open('$intermediate')); print(d['fix_verification']['enabled'])" )" == "True" ]]; then
      FIXED_STATUS["$case_name"]="$(
        "$PYTHON" -c "import json; d=json.load(open('$intermediate')); print(d['fix_verification']['status'])"
      )"
    else
      FIXED_STATUS["$case_name"]="N/A"
    fi
  else
    BUGGY_STATUS["$case_name"]="MISSING"
    FIXED_STATUS["$case_name"]="MISSING"
  fi
done

printf "\nCase                       Buggy RTL    Fixed RTL\n"
for case_name in "${CASES[@]}"; do
  printf "%-26s %-12s %s\n" "$case_name" "${BUGGY_STATUS[$case_name]}" "${FIXED_STATUS[$case_name]}"
done
