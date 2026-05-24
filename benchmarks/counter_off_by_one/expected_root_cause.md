# Expected Root Cause — counter_off_by_one

The buggy design asserts `done` when `count == MAX - 1` instead of when `count == MAX`.

The sequential always block that updates `count` and `done` uses the wrong comparison threshold, causing `done` to rise one cycle too early while `count` is still below `MAX`.
