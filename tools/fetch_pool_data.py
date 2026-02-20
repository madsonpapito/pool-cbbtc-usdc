import requests
import json
import sys
import os
from decimal import Decimal, getcontext

# Set high precision for V3 math
getcontext().prec = 50

# Configuration
RPC_URL = "https://mainnet.base.org"
MANAGER_ADDRESS = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"

# Token Info (known tokens on Base)
KNOWN_TOKENS = {
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": {"symbol": "USDC", "decimals": 6},
    "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf": {"symbol": "cbBTC", "decimals": 8},
}

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

def fetch_data(token_id=None):
    if token_id is None:
        token_id = 4227642  # Default for backwards compat
    
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
    fee = int(words[4], 16)
    tick_lower = signed_int24(words[5])
    tick_upper = signed_int24(words[6])
    liquidity = int(words[7], 16)
    tokens_owed0 = int(words[10], 16)
    tokens_owed1 = int(words[11], 16)

    # Determine token info from known tokens
    t0_info = KNOWN_TOKENS.get(token0_addr.lower(), {"symbol": "Token0", "decimals": 18})
    t1_info = KNOWN_TOKENS.get(token1_addr.lower(), {"symbol": "Token1", "decimals": 18})
    
    symbol0, dec0 = t0_info["symbol"], t0_info["decimals"]
    symbol1, dec1 = t1_info["symbol"], t1_info["decimals"]

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
    price_t0_in_t1 = float(Decimal("1.0001") ** Decimal(current_tick))
    price_t0_in_t1 *= 10 ** (dec0 - dec1)
    
    price_cbbtc = 0
    if price_t0_in_t1 != 0:
        price_cbbtc = 1 / price_t0_in_t1
        
    print(f"cbBTC Price (Pool): ${price_cbbtc:,.2f}")
    
    # Calculate USD
    if symbol0 == "USDC":
        value_usd = amount0 * 1.0 + amount1 * price_cbbtc
    else:
        value_usd = amount0 * price_cbbtc + amount1 * 1.0
    
    # Fees
    fees0 = tokens_owed0 / (10 ** dec0)
    fees1 = tokens_owed1 / (10 ** dec1)
    if symbol0 == "USDC":
        fees_usd = fees0 * 1.0 + fees1 * price_cbbtc
    else:
        fees_usd = fees0 * price_cbbtc + fees1 * 1.0
    
    print(f"\n=== REAL VALUES ===")
    print(f"Position Value: ${value_usd:,.2f}")
    print(f"Unclaimed Fees: ${fees_usd:,.2f}")
    
    # Convert ticks to prices (cbBTC/USDC)
    def tick_to_price_cbbtc_usdc(tick):
        price_t0_in_t1 = float(Decimal("1.0001") ** Decimal(tick))
        price_t0_in_t1 *= 10 ** (dec0 - dec1)
        if price_t0_in_t1 != 0:
            return 1 / price_t0_in_t1
        return 0
    
    price_lower = tick_to_price_cbbtc_usdc(tick_lower)
    price_upper = tick_to_price_cbbtc_usdc(tick_upper)
    price_current = tick_to_price_cbbtc_usdc(current_tick)
    
    print(f"Price Range: {price_lower:,.2f} - {price_upper:,.2f} cbBTC/USDC")
    print(f"Current Price: {price_current:,.2f} cbBTC/USDC")

    # Result Dict
    output = {
        "nft_id": token_id,
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

def main():
    # Accept NFT ID from CLI argument
    if len(sys.argv) > 1:
        token_id = int(sys.argv[1])
    else:
        token_id = 4227642  # Default
    
    # Determine output path
    pool_dir = f"tools/pools/{token_id}"
    os.makedirs(pool_dir, exist_ok=True)
    output_file = f"{pool_dir}/position_data.json"
    
    data = fetch_data(token_id)
    if data:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to {output_file}")
        
        # Also save to legacy path for backwards compat
        with open("tools/position_data.json", "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
