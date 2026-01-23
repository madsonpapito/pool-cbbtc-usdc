# Project Constitution (gemini.md)

## 0. Discovery Inputs
- **North Star:** Weekly tracking of Liquidity Pool results (cbBTC-USDC).
- **Source of Truth:** User Wallet `0xad10...94E9` (Base).
- **Asset:** Uniswap V3 NFT ID `4227642`.
- **Target Contract:** `0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1` (Base Position Manager)

## 1. Data Schemas

### Raw Input
```json
{
  "wallet": "0xad10F69C518eFb01586C8BE6FA3a02C021BD94E9",
  "chain_id": 8453,
  "nft_id": 4227642
}
```

### Processed Output (Payload)
- **File**: `tools/position_data.json`
- **Fields**: Liquidty, Tick Range, Token Addresses, Unclaimed Fees.

## 2. Architectural Invariants
- **Layer 1 (SOPs)**: See `architecture/`.
- **Layer 2 (Nav)**: `fetch_pool_data.py` acts as orchestrator.
- **Layer 3 (Tools)**: Direct RPC calls (No heavy API dependencies).

## 3. Maintenance Log
- **2026-01-23**: Initial Initialization. Link Established.
