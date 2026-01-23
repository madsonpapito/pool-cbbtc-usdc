# SOP 001: Fetch Position Data

## Goal
Retrieve current liquidity, tick range, and token amounts for a specific Uniswap V3 NFT ID on Base.

## Inputs
- `nft_id` (int): 4227642
- `manager_address` (str): `0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1`

## Steps
1. **Call `positions(nft_id)`**:
    - Method: `eth_call`
    - Selector: `0x99fbab88`
2. **Decode Response**:
    - Extract `token0`, `token1`, `fee`, `tickLower`, `tickUpper`, `liquidity`.

## Outputs
- `tools/position_data.json`
