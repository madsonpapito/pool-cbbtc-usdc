import requests
import json

RPC_URL = "https://mainnet.base.org"
ABI_SYMBOL = "0x95d89b41"

def get_symbol(token_addr):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": token_addr, "data": ABI_SYMBOL}, "latest"],
        "id": 1
    }
    try:
        res = requests.post(RPC_URL, json=payload, timeout=5)
        result = res.json().get('result')
        if result and result != "0x":
            # Decode string (offset 0x20, length, data)
            # Simplified decode for standard ERC20
            # Skip 0x, then 32 bytes offset, 32 bytes length
            # Text starts at 64 bytes (128 chars) + offset?
            # Actually standard ABI returns: offset(32)+len(32)+data
            # Often simpler tokens just return string bytes directly (rare)
            # Let's try flexible decode
            
            # Remove 0x
            raw = result[2:]
            # Skip offset (32 bytes) and length (32 bytes) -> 64 bytes = 128 chars
            if len(raw) > 128:
                hex_data = raw[128:]
                # Convert hex to ascii, ignoring nulls
                text = bytes.fromhex(hex_data).decode('utf-8', errors='ignore').strip('\x00')
                return text
            else:
                # Try direct decode if short (non-standard)
                return bytes.fromhex(raw).decode('utf-8', errors='ignore').strip('\x00')
                
    except Exception as e:
        print(e)
    return "Unknown"

t1 = "0x3ed6a56a9adec22cf1abfc8fc7100fda77312a10" # Token 0 from previous log
t2 = "0x4200000000000000000000000000000000000006" # Token 1

print(f"{t1}: {get_symbol(t1)}")
print(f"{t2}: {get_symbol(t2)}")
