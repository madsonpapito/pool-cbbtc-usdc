import json
import os

# Dados extraídos manualmente dos screenshots e links fornecidos pelo usuário
# BaseScan Mint: 108.64 USDC + 0.00148 cbBTC
# Uniswap UI (Atual): 168.13 USDC + 40.53 USD (0.001 cbBTC) -> Total ~$208.65
# Price Range: 0.00001 - 0.00002 cbBTC/USDC (ou vice-versa, o print diz 0,00001 cbBTC = 1 USDC)
# Logo 1 cbBTC = 100,000 USDC. Range $50k - $100k?
# Min Tick -66000, Max -62790 (do OpenSea)

# Tick Math:
# 1.0001^-66000 = 0.00136...
# 1.0001^-62790 = 0.00187... 
# Inverted (USDC per cbBTC): 1/0.00136 = 73500, 1/0.00187 = 53300.
# Range parece ser $53k - $73.5k por BTC.

NFT_ID = 1345196
BASE_DIR = f"data/pools/{NFT_ID}"
os.makedirs(BASE_DIR, exist_ok=True)

# 1. Config Data
config = {
    "nft_id": NFT_ID,
    "total_invested_usd": 221.84, # Est 108.64 + 113.20 (at $76k BTC)
    "deposit_date": "2026-02-05",
    "last_deposit_date": "2026-02-05",
    "last_deposit_amount": 0.0,
    "fees_collected_usd": 3.03, # Do print (pending) + collected? O print diz "Tarifas recebidas 3.03"
    "initial_cbbtc_price": 76345 # Estimate from deposit ratio or time
}

with open(f"{BASE_DIR}/config.json", "w") as f:
    json.dump(config, f, indent=2)

# 2. Position Data (Mocked from latest Screenshot state for now, until we fix V4 fetch)
# User screenshot: 168.13 USDC, <0.001 cbBTC (likely 0.0005?)
# Total Value: $208.65
position = {
    "token0": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913", # USDC
    "token1": "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf", # cbBTC
    "symbol0": "USDC",
    "symbol1": "cbBTC",
    "fee": 500, # 0.05%
    "liquidity": 0, # Placeholder
    "tick_lower": -66000,
    "tick_upper": -62790,
    "current_tick": -63500, # Approx based on range
    "in_range": True,
    "amount0": 168.13, # USDC
    "amount1": 0.00057, # Est from rem value (40.53 / 70000)
    "price_cbbtc": 70041, # Current market
    "value_usd": 208.65,
    "fees_usd": 3.03,
    "unclaimed_0": 0,
    "unclaimed_1": 0,
    "price_lower": 53324,
    "price_upper": 73510,
    "price_current": 70041
}

with open(f"{BASE_DIR}/position_data.json", "w") as f:
    json.dump(position, f, indent=2)

print(f"Manually configured Pool {NFT_ID} with V4 data from screenshots.")
