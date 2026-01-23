# SOP 002: Calculate Business Metrics

## Goal
Convert raw liquidity/ticks into USD Value and Impermanent Loss.

## Formulas
1. **Token Amounts**:
    - Use `Liquidity`, `SqrtPrice` (from Pool), `TickLower`, `TickUpper` to calculate `Amount0` and `Amount1`.
2. **USD Value**:
    - `Value = (Amount0 * Price0_USD) + (Amount1 * Price1_USD)`
3. **Impermanent Loss**:
    - `IL = (CurrentValue - HoldValue) / HoldValue`

## Implementation
- Currently implemented in `tools/dashboard_gen.py` (Simplified).
