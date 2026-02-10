import requests
import json

RPC_URL = "https://mainnet.base.org"
TX_HASH = "0xc2a6d8ce68e65155c8ff621c75218ebdb8c8ca9aa8d513b9b5cf3f5d5afae82c"

def call_rpc(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print(f"Checking TX: {TX_HASH}")
    res = call_rpc("eth_getTransactionReceipt", [TX_HASH])
    
    if not res:
        print("TX not found.")
        return
        
    print(f"Status: {res.get('status')} (1=Success)")
    for i, log in enumerate(res.get('logs', [])):
        curr_addr = log.get('address')
        print(f"[Log {i}] Address: {curr_addr}")

                 
if __name__ == "__main__":
    main()
