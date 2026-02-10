import requests
import json
from datetime import datetime

# Configuration
# Configuration
RPC_URL = "https://base-rpc.publicnode.com"
NPM_ADDRESS = "0x03a520b32c04bf3beef7beb72e919cf822ed34f1"
OUTPUT_FILE = "tools/fees_data.json"

def get_nft_id(config_path="tools/config.json"):
    try:
        with open(config_path, "r") as f:
            return json.load(f).get("nft_id", 4227642)
    except:
        return 4227642

NFT_ID = get_nft_id()

# Collect Event Topic (from actual transaction logs)
COLLECT_TOPIC = "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"

def get_logs(from_block, to_block, nft_id):
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
        if 'result' in data:
            return data['result']
    except:
        pass
    return []

def get_block_number():
    """Get current block number"""
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return int(res.json().get('result', '0x0'), 16)
    except:
        return 0

def fetch_fees(nft_id, previous_data_path=OUTPUT_FILE):
    print(f"Scanning for Collect events for NFT #{nft_id}...")
    
    current_block = get_block_number()
    if current_block == 0:
        print("Failed to get current block number")
        return None
    
    # Load previous state
    start_block = 20000000 # Default safe start
    previous_data = {}
    try:
        # Use the specific path provided for state, or default to global
        with open(previous_data_path, "r") as f:
            previous_data = json.load(f)
            # Only use previous block if it matches the current NFT ID (safety check)
            if str(previous_data.get("nft_id")) == str(nft_id):
                last_block = previous_data.get("last_scanned_block")
                if last_block:
                    start_block = last_block + 1
                    print(f"Resuming scan from block {start_block}")
    except:
        pass
        
    chunk_size = 5000 # Increased chunk size for faster skip
    
    all_logs = []
    block = start_block
    
    if block >= current_block:
        print("Already up to date.")
    else:
        print(f"Searching blocks {start_block} to {current_block}...")
    
        import time
        
        while block < current_block:
            end_block = min(block + chunk_size, current_block)
            
            # Retry logic
            retries = 3
            while retries > 0:
                try:
                    logs = get_logs(block, end_block, nft_id)
                    if logs is not None:
                        valid_logs = [l for l in logs if l]
                        all_logs.extend(valid_logs)
                    break
                except Exception as e:
                    retries -= 1
                    time.sleep(1)
                
            block = end_block + 1
        
        print(f"Found {len(all_logs)} NEW Collect events.")
    
    # Merge with previous total
    total_usdc = previous_data.get("total_collected_usdc", 0)
    total_cbbtc = previous_data.get("total_collected_cbbtc", 0)
    prev_count = previous_data.get("events_count", 0)
    
    for log in all_logs:
        data_hex = log.get('data', '0x')[2:]
        if len(data_hex) >= 192:
            amt0 = int(data_hex[64:128], 16)
            amt1 = int(data_hex[128:192], 16)
            
            # Add to totals
            # We need to know which amt is USDC and which is cbBTC.
            # Pool #4227642: Token0=USDC, Token1=cbBTC
            # Pool #1345196: Token0=cbBTC, Token1=USDC
            
            if str(nft_id) == "1345196":
                # Token0 is cbBTC (8 decimals), Token1 is USDC (6 decimals)
                amount_cbbtc = amt0 / 1e8
                amount_usdc = amt1 / 1e6
            else:
                # Default (Old Pool): Token0 is USDC (6), Token1 is cbBTC (8)
                amount_usdc = amt0 / 1e6
                amount_cbbtc = amt1 / 1e8
            
            total_usdc += amount_usdc
            total_cbbtc += amount_cbbtc
            
    print(f"Total Collected (Cumulative): {total_usdc:.4f} USDC + {total_cbbtc:.8f} cbBTC")
    
    result = {
        "nft_id": nft_id,
        "total_collected_usdc": total_usdc,
        "total_collected_cbbtc": total_cbbtc,
        "events_count": prev_count + len(all_logs),
        "last_scanned_block": current_block,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="tools/config.json", help="Path to config file")
    parser.add_argument("--output", default="tools/fees_data.json", help="Path to output file")
    args = parser.parse_args()

    nft_id = get_nft_id(args.config)
    
    # Update global OUTPUT_FILE for this run (imports might still use the top-level one if not careful, 
    # but for main execution this is fine. Ideally we pass output_file to fetch_fees too)
    global OUTPUT_FILE
    OUTPUT_FILE = args.output
    
    data = fetch_fees(nft_id)
    if data:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
