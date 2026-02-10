import requests
import json
from decimal import Decimal, getcontext

# Set high precision for V3 math
getcontext().prec = 50

# Configuration
RPC_URL = "https://mainnet.base.org"

def get_token_id(config_path="tools/config.json"):
    try:
        with open(config_path, "r") as f:
            return json.load(f).get("nft_id", 4227642)
    except:
        return 4227642

# Default for import compatibility
TOKEN_ID = get_token_id()
MANAGER_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"

# Token Info
ADDR_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ADDR_CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
DECIMALS_USDC = 6
DECIMALS_CBBTC = 8

# ABI Signatures
ABI_POSITIONS = "0x99fbab88"
ABI_SLOT0 = "0x3850c7bd"
ABI_GET_POOL = "0x1698ee82"
FACTORY_ADDRESS = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"

def call_rpc(to_addr, data):
    payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"RPC Error: {e}")
        return None

def signed_int24(hex_str):
    """Parse int24 from hex (right-aligned in 32 bytes)"""
    val = int(hex_str[-6:], 16)  # Last 3 bytes = 6 hex chars = 24 bits
    if val >= 2**23:
        return val - 2**24
    return val

def tick_to_sqrt_ratio(tick):
    """Convert tick to sqrt ratio using Decimal for precision"""
    base = Decimal("1.0001")
    return base ** (Decimal(tick) / 2)

def get_amounts(liquidity, sqrt_price, tick_lower, tick_upper, current_tick):
    """Calculate token amounts from liquidity"""
    L = Decimal(liquidity)
    sqrt_ratio_a = tick_to_sqrt_ratio(tick_lower)
    sqrt_ratio_b = tick_to_sqrt_ratio(tick_upper)
    
    if current_tick < tick_lower:
        # All in token0
        amount0 = L * (1/sqrt_ratio_a - 1/sqrt_ratio_b)
        amount1 = Decimal(0)
    elif current_tick >= tick_upper:
        # All in token1
        amount0 = Decimal(0)
        amount1 = L * (sqrt_ratio_b - sqrt_ratio_a)
    else:
        # In range
        amount0 = L * (1/sqrt_price - 1/sqrt_ratio_b)
        amount1 = L * (sqrt_price - sqrt_ratio_a)
    
    return float(amount0), float(amount1)

def get_cbbtc_price():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=coinbase-wrapped-btc&vs_currencies=usd"
        res = requests.get(url, timeout=5)
        return res.json().get('coinbase-wrapped-btc', {}).get('usd', 97000.0)
    except:
        return 97000.0

def fetch_data(token_id=TOKEN_ID):
    print(f"Fetching REAL Data for NFT #{token_id}...")
    
    # 1. Fetch Position Data
    data_str = ABI_POSITIONS + hex(token_id)[2:].zfill(64)
    res_pos = call_rpc(MANAGER_ADDRESS, data_str)
    
    if not res_pos or res_pos == "0x":
        print("Failed to fetch position.")
        return None

    raw = res_pos[2:]
    words = [raw[i:i+64] for i in range(0, len(raw), 64)]
    
    token0_addr = "0x" + words[2][-40:]
    token1_addr = "0x" + words[3][-40:]
    print(f"DEBUG: Token0 = {token0_addr}")
    print(f"DEBUG: Token1 = {token1_addr}")
    print(f"DEBUG: ADDR_USDC = {ADDR_USDC}")
    print(f"DEBUG: ADDR_CBBTC = {ADDR_CBBTC}")

    fee = int(words[4], 16)
    tick_lower = signed_int24(words[5])
    tick_upper = signed_int24(words[6])
    liquidity = int(words[7], 16)
    tokens_owed0 = int(words[10], 16)
    tokens_owed1 = int(words[11], 16)

    # Determine token order
    if token0_addr.lower() == ADDR_USDC.lower():
        symbol0, symbol1 = "USDC", "cbBTC"
        dec0, dec1 = DECIMALS_USDC, DECIMALS_CBBTC
    else:
        symbol0, symbol1 = "cbBTC", "USDC"
        dec0, dec1 = DECIMALS_CBBTC, DECIMALS_USDC

    print(f"Pair: {symbol0}/{symbol1}")
    print(f"Tick Range: [{tick_lower}, {tick_upper}]")
    print(f"Liquidity: {liquidity}")

    # 2. Get Pool Address
    padded_t0 = token0_addr[2:].zfill(64)
    padded_t1 = token1_addr[2:].zfill(64)
    padded_fee = hex(fee)[2:].zfill(64)
    data_pool = ABI_GET_POOL + padded_t0 + padded_t1 + padded_fee
    res_pool = call_rpc(FACTORY_ADDRESS, data_pool)
    
    if res_pool and res_pool != "0x" and len(res_pool) > 42:
        pool_address = "0x" + res_pool[-40:]
        print(f"Pool: {pool_address}")
        
        # 3. Get slot0
        res_slot0 = call_rpc(pool_address, ABI_SLOT0)
        if res_slot0 and len(res_slot0) > 130:
            slot0_raw = res_slot0[2:]
            sqrt_price_x96 = int(slot0_raw[:64], 16)
            current_tick = signed_int24(slot0_raw[64:128])
            sqrt_price = Decimal(sqrt_price_x96) / Decimal(2**96)
        else:
            current_tick = (tick_lower + tick_upper) // 2
            sqrt_price = tick_to_sqrt_ratio(current_tick)
    else:
        print("Pool not found, using mid-range estimate")
        current_tick = (tick_lower + tick_upper) // 2
        sqrt_price = tick_to_sqrt_ratio(current_tick)

    print(f"Current Tick: {current_tick}")
    
    # Check if position is in range
    in_range = tick_lower <= current_tick < tick_upper
    print(f"In Range: {in_range}")
    
    # 4. Calculate Amounts
    amount0_raw, amount1_raw = get_amounts(liquidity, sqrt_price, tick_lower, tick_upper, current_tick)
    amount0 = amount0_raw / (10 ** dec0)
    amount1 = amount1_raw / (10 ** dec1)
    
    print(f"{symbol0}: {amount0:.6f}")
    print(f"{symbol1}: {amount1:.8f}")
    
    # 5. Get Prices
    # Calculate price of Token0 in terms of Token1
    price0_in_1 = float(Decimal("1.0001") ** Decimal(current_tick))
    price0_in_1 *= 10 ** (dec0 - dec1)
    
    if symbol0 == "cbBTC":
        # Token0 is cbBTC, Token1 is USDC.
        # price0_in_1 is price of cbBTC in USDC (i.e. the Price)
        price_cbbtc = price0_in_1
        
        # In this case, 1/price is USDC in cbBTC
        price_lower = float(Decimal("1.0001") ** Decimal(tick_lower)) * (10 ** (dec0 - dec1))
        price_upper = float(Decimal("1.0001") ** Decimal(tick_upper)) * (10 ** (dec0 - dec1))
        price_current = price_cbbtc
        
    else: # symbol0 == "USDC"
        # Token0 is USDC, Token1 is cbBTC.
        # price0_in_1 is price of USDC in cbBTC (e.g. 0.00001)
        # We want cbBTC price in USDC, so invert
        price_cbbtc = 0
        if price0_in_1 != 0:
            price_cbbtc = 1 / price0_in_1
            
        def tick_to_price_cbbtc_usdc(tick):
            p = float(Decimal("1.0001") ** Decimal(tick))
            p *= 10 ** (dec0 - dec1)
            return 1 / p if p != 0 else 0

        price_lower = tick_to_price_cbbtc_usdc(tick_lower)
        price_upper = tick_to_price_cbbtc_usdc(tick_upper)
        price_current = price_cbbtc

    print(f"cbBTC Price (Pool): ${price_cbbtc:,.2f}")
    
    # Calculate USD Value
    # value = amount0 * price0 + amount1 * price1
    if symbol0 == "USDC":
        value_usd = amount0 * 1.0 + amount1 * price_cbbtc
    else:
        # symbol0 is cbBTC
        value_usd = amount0 * price_cbbtc + amount1 * 1.0
    
    # Fees Value
    fees0 = tokens_owed0 / (10 ** dec0)
    fees1 = tokens_owed1 / (10 ** dec1)
    
    if symbol0 == "USDC":
        fees_usd = fees0 * 1.0 + fees1 * price_cbbtc
    else:
        fees_usd = fees0 * price_cbbtc + fees1 * 1.0
    
    print(f"\n=== REAL VALUES ===")
    print(f"Position Value: ${value_usd:,.2f}")
    print(f"Unclaimed Fees: ${fees_usd:,.2f}")
    
    # Range Display (Always ensure Lower < Upper for display)
    if price_lower > price_upper:
        price_lower, price_upper = price_upper, price_lower
    
    print(f"Price Range: {price_lower:,.2f} - {price_upper:,.2f} cbBTC/USDC")
    print(f"Current Price: {price_current:,.2f} cbBTC/USDC")

    # Result Dict
    output = {
        "token0": token0_addr, "token1": token1_addr,
        "symbol0": symbol0, "symbol1": symbol1,
        "fee": fee, "liquidity": liquidity,
        "tick_lower": tick_lower, "tick_upper": tick_upper,
        "current_tick": current_tick, "in_range": in_range,
        "amount0": amount0, "amount1": amount1,
        "price_cbbtc": price_cbbtc,
        "value_usd": value_usd, "fees_usd": fees_usd,
        "unclaimed_0": tokens_owed0, "unclaimed_1": tokens_owed1,
        "price_lower": price_lower,
        "price_upper": price_upper,
        "price_current": price_current
    }
    
    return output

import argparse
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nft-id", type=int, help="Uniswap V3 NFT ID")
    parser.add_argument("--config", default="tools/config.json", help="Path to config file")
    args = parser.parse_args()
    
    # Resolve NFT ID: Argument > Config File > Default
    if args.nft_id:
        nft_id = args.nft_id
    else:
        # We need to use the config path passed in args, or default
        nft_id = get_token_id(args.config)
    
    # Create data directory if not exists (for non-default pools)
    # If using default tools/config.json, we keep behavior of saving to tools/position_data.json
    # BUT we also want to start populating data/pools/{id}/position_data.json for the future switch
    
    base_dir = f"data/pools/{nft_id}"
    os.makedirs(base_dir, exist_ok=True)
    
    data = fetch_data(nft_id)
    if data:
        # 1. Save to new structure (Always)
        outfile = f"{base_dir}/position_data.json"
        with open(outfile, "w") as f:
            json.dump(data, f, indent=2)
            
        # 2. Save to legacy location (Only if using default config/id, to keep app.py working)
        # We check if the config being used is the default one OR if the ID matches the default one
        try:
            with open("tools/config.json", "r") as f:
                default_id = json.load(f).get("nft_id")
        except:
            default_id = 4227642
            
        if str(nft_id) == str(default_id):
             with open("tools/position_data.json", "w") as f:
                json.dump(data, f, indent=2)
             print(f"\nSaved to {outfile} AND tools/position_data.json (Legacy Support)")
        else:
             print(f"\nSaved to {outfile}")

if __name__ == "__main__":
    main()
