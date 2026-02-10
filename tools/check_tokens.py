import requests
import json

RPC_URL = "https://mainnet.base.org"

ABI_SYMBOL = "0x95d89b41"
ABI_DECIMALS = "0x313ce567"

def call_rpc(to_addr, data):
    payload = {"jsonrpc": "2.0", "method": "eth_call", "params": [{"to": to_addr, "data": data}, "latest"], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return res.json().get('result')
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_string(hex_str):
    try:
        # standard 32 byte offset
        offset = int(hex_str[2:66], 16) * 2
        length = int(hex_str[2+offset:2+offset+64], 16) * 2
        data = hex_str[2+offset+64 : 2+offset+64+length]
        return bytes.fromhex(data).decode('utf-8')
    except:
        return "?"

def get_uint8(hex_str):
    try:
        return int(hex_str, 16)
    except:
        return 0

tokens = [
    "0x3ed6a56a9adec22cf1abfc8fc7100fda77312a10",
    "0x4200000000000000000000000000000000000006"
]

for t in tokens:
    print(f"Checking {t}...")
    res_sym = call_rpc(t, ABI_SYMBOL)
    res_dec = call_rpc(t, ABI_DECIMALS)
    
    if res_sym:
        # Try parse string
        sym = get_string(res_sym)
        # If fail (not standard string), try direct
        if sym == "?":
             try: sym = bytes.fromhex(res_sym[2:]).decode('utf-8').replace('\x00', '')
             except: sym = "RAW:" + res_sym
    else:
        sym = "Unknown"
        
    dec = get_uint8(res_dec) if res_dec else 0
    
    print(f"  Symbol: {sym}")
    print(f"  Decimals: {dec}")
