# Expected Root Cause — vending_machine_fsm_bug

The buggy FSM transitions to `ST_DISPENSE` when credit is sufficient but never asserts `dispense` in the output logic for that state.

The sequential `case (state)` block updates credit during collection but omits the dispense assertion in `ST_DISPENSE`.
