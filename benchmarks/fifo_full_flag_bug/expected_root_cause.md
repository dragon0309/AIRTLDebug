# Expected Root Cause — fifo_full_flag_bug

The buggy design computes `full` using only `wr_ptr == rd_ptr`, which is also the empty condition when `wrap_bit` is low.

The continuous assignment for `full` ignores the wrap-around state, so the FIFO never reports full after filling to capacity.
