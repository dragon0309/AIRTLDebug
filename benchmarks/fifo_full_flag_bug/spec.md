# FIFO Full Flag Bug Benchmark

## Overview

An 8-entry FIFO with separate read/write pointers and a wrap bit to distinguish full from empty.

## Parameters

- `DEPTH = 8`
- Pointer width = 3 bits

## Interface

| Signal     | Direction | Description                              |
|------------|-----------|------------------------------------------|
| `clk`      | input     | Clock                                    |
| `reset`    | input     | Synchronous reset                        |
| `wr_en`    | input     | Write enable                             |
| `rd_en`    | input     | Read enable                              |
| `wr_ptr`   | output    | Write pointer                            |
| `rd_ptr`   | output    | Read pointer                             |
| `wrap_bit` | output    | Toggles when write pointer wraps         |
| `full`     | output    | FIFO full flag                           |
| `empty`    | output    | FIFO empty flag                          |

## Expected Behavior

- `empty` when `wr_ptr == rd_ptr` and no wrap has occurred.
- `full` when `wr_ptr == rd_ptr` and the write pointer has wrapped at least once.

## Top Module

`fifo`
