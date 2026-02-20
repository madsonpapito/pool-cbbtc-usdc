import requests
import json
import sys
import os
from datetime import datetime

# Configuration
RPC_URL = "https://base-rpc.publicnode.com"
NPM_ADDRESS = "0x03a520b32c04bf3beef7beb72e919cf822ed34f1"

# Collect Event Topic (from actual transaction logs)
COLLECT_TOPIC = "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"

def get_logs(nft_id, from_block, to_block):
    """Fetch logs using eth_getLogs via JSON-RPC"""
    nft_id_topic = "0x" + f"{nft_id:064x}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "address": NPM_ADDRESS,
            "topics": [COLLECT_TOPIC, nft_id_topic],
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block)
        }],
        "id": 1
    }
    
    try:
        res = requests.post(RPC_URL, json=payload, timeout=30)
        data = res.json()
        if 'result' in data and isinstance(data['result'], list):
            return data['result']
    except Exception as e:
        print(f"get_logs error: {e}")
    return []

def get_block_number():
    """Get current block number"""
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return int(res.json().get('result', '0x0'), 16)
    except:
        return 0

def fetch_fees(nft_id=None):
    if nft_id is None:
        nft_id = 4227642  # Default
    
    print(f"Scanning for Collect events for NFT #{nft_id}...")
    
    current_block = get_block_number()
    if current_block == 0:
        print("Failed to get current block number")
        return None
    
    start_block = 38000000
    chunk_size = 40000
    
    all_logs = []
    block = start_block
    
    print(f"Searching blocks {start_block} to {current_block}...")
    
    while block < current_block:
        end_block = min(block + chunk_size, current_block)
        logs = get_logs(nft_id, block, end_block)
        all_logs.extend(logs)
        block = end_block + 1
    
    print(f"Found {len(all_logs)} Collect events.")
    
    total_amount0 = 0
    total_amount1 = 0
    
    for log in all_logs:
        data_hex = log.get('data', '0x')[2:]
        if len(data_hex) >= 192:
            amt0 = int(data_hex[64:128], 16)
            amt1 = int(data_hex[128:192], 16)
            total_amount0 += amt0
            total_amount1 += amt1
            print(f"  Found: {amt0/1e6:.4f} USDC + {amt1/1e8:.8f} cbBTC")
    
    # USDC = 6 decimals, cbBTC = 8 decimals
    total_usdc = total_amount0 / 1e6
    total_cbbtc = total_amount1 / 1e8
    
    print(f"\nTotal Collected: {total_usdc:.4f} USDC + {total_cbbtc:.8f} cbBTC")
    
    result = {
        "nft_id": nft_id,
        "total_collected_usdc": total_usdc,
        "total_collected_cbbtc": total_cbbtc,
        "events_count": len(all_logs),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result

def main():
    # Accept NFT ID from CLI argument
    if len(sys.argv) > 1:
        nft_id = int(sys.argv[1])
    else:
        nft_id = 4227642  # Default
    
    pool_dir = f"tools/pools/{nft_id}"
    os.makedirs(pool_dir, exist_ok=True)
    output_file = f"{pool_dir}/fees_data.json"
    
    data = fetch_fees(nft_id)
    if data:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {output_file}")
        
        # Also save to legacy path
        with open("tools/fees_data.json", "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
