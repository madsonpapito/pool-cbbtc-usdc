import requests
import json
from decimal import Decimal, getcontext
from web3 import Web3
from v4_utils import PoolKey, get_pool_id, POOL_MANAGER_ADDRESS

getcontext().prec = 50

RPC_URL = "https://mainnet.base.org"

# Constants
ADDR_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ADDR_CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"
FEE = 500 
TICK_SPACING = 10
HOOKS_ADDR = "0x0000000000000000000000000000000000000000"

def call_rpc(to_addr, data):
    payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_code(addr):
    payload = {"jsonrpc": "2.0", "method": "eth_getCode", "params": [addr, "latest"], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        return None

def hex_to_int(hex_str):
    if not hex_str or hex_str == "0x": return 0
    return int(hex_str, 16)

def test_v4_fetch():
    print(f"--- Uniswap V4 Fetch Test ---")
    print(f"PoolManager: {POOL_MANAGER_ADDRESS}")
    
    # 0. Check Contract Existence
    code = get_code(POOL_MANAGER_ADDRESS)
    if not code or code == "0x":
        print("CRITICAL: PoolManager address has no code on this network!")
        return
    else:
        print(f"PoolManager Code Size: {len(code)/2} bytes (OK)")

    # 1. Pool Key
    t0_int = int(ADDR_USDC, 16)
    t1_int = int(ADDR_CBBTC, 16)
    if t0_int < t1_int:
        c0, c1 = ADDR_USDC, ADDR_CBBTC
        print(f"Tokens: USDC ({c0}) < cbBTC ({c1})")
    else:
        c0, c1 = ADDR_CBBTC, ADDR_USDC
        print(f"Tokens: cbBTC ({c0}) < USDC ({c1})")
        
    pool_key = PoolKey(c0, c1, FEE, TICK_SPACING, HOOKS_ADDR)
    pool_id = get_pool_id(pool_key)
    print(f"Pool ID: {pool_id.hex()}")
    
    # 2. Try Selectors
    # V4 Core (singleton) usually has `slot0` or `getSlot0` or `pools`.
    selectors = {
        "getSlot0": Web3.keccak(text="getSlot0(bytes32)").hex()[:10],
        "slot0": Web3.keccak(text="slot0(bytes32)").hex()[:10],
        "pools": Web3.keccak(text="pools(bytes32)").hex()[:10]
    }
    
    success = False
    
    for name, sel in selectors.items():
        data_str = sel + pool_id.hex()[2:].zfill(64)
        print(f"Trying {name} [{sel}]...")
        res = call_rpc(POOL_MANAGER_ADDRESS, data_str)
        
        if res and res != "0x":
            print(f"SUCCESS: {name} returned data!")
            # print(f"Raw: {res}")
            
            raw = res[2:]
            chunks = [raw[i:i+64] for i in range(0, len(raw), 64)]
            if len(chunks) >= 1:
                val0 = hex_to_int(chunks[0])
                print(f"  Word 0 (int): {val0}")
                if val0 > 0:
                     success = True
                     # If it's sqrtPriceX96, verify reasonable range
                     # 1:1 price is 2^96 = 7.9e28
                     # USDC/cbBTC price is approx 100k? No, 1 BTC ~ 100k USDC.
                     # 1 cbBTC = 100k USDC.
                     # Token0=USDC (dec 6), Token1=cbBTC (dec 8)
                     # Price 0->1 = Amount1/Amount0 = 1 cbBTC / 100k USDC = 1e-5 (raw units?)
                     # No, raw price is (sqrtPrice/2^96)^2
                     # Adjusted Price = Raw * 10^(d0-d1)
                     # Let's just output raw SqrtPrice and calculated price.
                     
                     p_raw = (Decimal(val0) / Decimal(2**96)) ** 2
                     print(f"  Raw Price: {p_raw}")
            break
        else:
            print(f"  {name} Failed (Empty/0x)")
            
    if not success:
        print("No valid data returned. Pool params might be wrong or pool not initialized.")

if __name__ == "__main__":
    test_v4_fetch()
