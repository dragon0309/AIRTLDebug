# Counter Off-By-One Benchmark

## Overview

A simple enabled counter that asserts `done` when it reaches `MAX`.

## Parameters

- `MAX = 16`

## Interface

| Signal  | Direction | Description                          |
|---------|-----------|--------------------------------------|
| `clk`   | input     | Rising-edge clock                    |
| `reset` | input     | Synchronous active-high reset        |
| `enable`| input     | Count enable                         |
| `count` | output    | Current counter value (0 to MAX)     |
| `done`  | output    | High when counter has reached `MAX`  |

## Expected Behavior

- After reset, when `enable` is high, `count` increments once per clock cycle until it reaches `MAX`.
- `done` must remain low while `count < MAX`.
- `done` must be high when `count == MAX`.

## Top Module

`counter`
