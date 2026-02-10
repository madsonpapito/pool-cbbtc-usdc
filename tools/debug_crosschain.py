import requests
import json

# URLs
RPC_BASE = "https://mainnet.base.org"
RPC_OP = "https://mainnet.optimism.io"
RPC_ARB = "https://arb1.arbitrum.io/rpc"

# Addresses
MGR_BASE_STD = "0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1"
MGR_UNIVERSAL = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88" # Mainnet, Op, Arb, Polygon...
NFT_ID = 1345196

ABI_POSITIONS = "0x99fbab88" # positions(uint256)

def call_rpc(url, to_addr, data):
    payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        return None

def check(name, url, mgr):
    print(f"Checking {name} on {mgr}...")
    data = ABI_POSITIONS + hex(NFT_ID)[2:].zfill(64)
    res = call_rpc(url, mgr, data)
    
    if res and len(res) > 100:
        # Parse tokens
        raw = res[2:]
        words = [raw[i:i+64] for i in range(0, len(raw), 64)]
        if len(words) < 4:
            print("  -> Invalid response length")
            return
            
        t0 = "0x" + words[2][-40:]
        t1 = "0x" + words[3][-40:]
        liq = int(words[7], 16)
        print(f"  -> FOUND! Token0: {t0}, Token1: {t1}, Liquidity: {liq}")
    else:
        print("  -> Not found / Error")

def main():
    # 1. Check UNIVERSAL Manager on BASE (Does it exist?)
    check("Base (Universal Mgr)", RPC_BASE, MGR_UNIVERSAL)
    
    # 2. Check Standard Manager on BASE (Already did, but confirm)
    check("Base (Standard Mgr)", RPC_BASE, MGR_BASE_STD)
    
    # 3. Check Optimism (Universal)
    check("Optimism (Universal Mgr)", RPC_OP, MGR_UNIVERSAL)
    
    # 4. Check Arbitrum (Universal)
    check("Arbitrum (Universal Mgr)", RPC_ARB, MGR_UNIVERSAL)

if __name__ == "__main__":
    main()
