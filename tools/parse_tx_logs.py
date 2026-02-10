import requests
import json
from decimal import Decimal

RPC_URL = "https://mainnet.base.org"
TX_HASH = "0xc2a6d8ce68e65155c8ff621c75218ebdb8c8ca9aa8d513b9b5cf3f5d5afae82c"

# V4 Event Signatures
# IncreaseLiquidity(uint256 tokenId, uint128 liquidity, uint128 amount0, uint128 amount1)
# Keccak("IncreaseLiquidity(uint256,uint128,uint128,uint128)") 
# -> 0x... wait, PositionManager emits IncreaseLiquidity?
# Or PoolManager emits ModifyLiquidity?
# ModifyLiquidity(bytes32,address,int24,int24,int256)
# Keccak("ModifyLiquidity(bytes32,address,int24,int24,int256)")

def call_rpc(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print(f"Parsing Logs for TX: {TX_HASH}")
    res = call_rpc("eth_getTransactionReceipt", [TX_HASH])
    
    if not res:
        print("TX not found.")
        return
        
    logs = res.get('logs', [])
    print(f"Found {len(logs)} logs.")
    
    for i, log in enumerate(logs):
        addr = log.get('address')
        topics = log.get('topics', [])
        data = log.get('data')
        
        print(f"\n[Log {i}] Address: {addr}")
        print(f"  Topics: {topics}")
        print(f"  Data: {data}")

                
if __name__ == "__main__":
    main()
