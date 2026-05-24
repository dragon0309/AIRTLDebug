# Vending Machine FSM Bug Benchmark

## Overview

A coin-operated vending machine FSM that collects 10/25 cent coins until the price is met, then dispenses.

## Parameters

- `PRICE = 50`

## Interface

| Signal      | Direction | Description                          |
|-------------|-----------|--------------------------------------|
| `clk`       | input     | Clock                                |
| `reset`     | input     | Synchronous reset                    |
| `coin`      | input     | 2-bit coin select (1=10, 2=25)       |
| `state`     | output    | Current FSM state                    |
| `next_state`| output    | Combinational next state             |
| `credit`    | output    | Accumulated credit                   |
| `dispense`  | output    | Dispense pulse when item vended      |
| `refund`    | output    | Refund pulse                         |

## Expected Behavior

- Accept coins in `ST_COLLECT` until `credit >= PRICE`.
- Transition to `ST_DISPENSE` and assert `dispense` for one cycle when enough credit is collected.

## Top Module

`vending_machine`
