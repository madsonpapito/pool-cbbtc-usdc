import requests
import json
import sys
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Configuration
RPC_URL = os.getenv("RPC_URL", "https://base-rpc.publicnode.com")
NPM_ADDRESS = "0x03a520b32c04bf3beef7beb72e919cf822ed34f1"

# Uniswap V3 NonfungiblePositionManager Event Topics
COLLECT_TOPIC = "0x40d0efd1a53d60ecbf40971b9daf7dc90178c3aadc7aab1765632738fa8b8f01"
DECREASE_LIQ_TOPIC = "0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8d58ad6b8ce9"

def fetch_chunk(args):
    """Fetch a single chunk of logs. Used by ThreadPoolExecutor."""
    from_block, to_block, nft_id = args
    nft_id_topic = "0x" + f"{nft_id:064x}"
    
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "address": NPM_ADDRESS,
            "topics": [[COLLECT_TOPIC, DECREASE_LIQ_TOPIC], nft_id_topic],
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block)
        }],
        "id": 1
    }
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            res = requests.post(RPC_URL, json=payload, timeout=60)
            
            if res.status_code == 429:
                time.sleep(3 + attempt * 2)
                continue
            
            data = res.json()
            
            if 'error' in data:
                error_msg = data['error'].get('message', '')
                # Block range too large - split in half
                if 'limited' in error_msg.lower() or 'too many' in error_msg.lower():
                    if from_block >= to_block:
                        return []
                    mid = (from_block + to_block) // 2
                    left = fetch_chunk((from_block, mid, nft_id))
                    right = fetch_chunk((mid + 1, to_block, nft_id))
                    return left + right
                # Rate limit - retry
                if 'rate limit' in error_msg.lower() or '429' in str(data['error']):
                    time.sleep(3 + attempt * 2)
                    continue
                # Other error - retry
                time.sleep(2)
                continue
            
            if 'result' in data and isinstance(data['result'], list):
                return data['result']
                
        except Exception as e:
            time.sleep(2 ** min(attempt, 3))
    
    return []

def get_block_number():
    """Get current block number"""
    payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
    try:
        res = requests.post(RPC_URL, json=payload, timeout=10)
        return int(res.json().get('result', '0x0'), 16)
    except:
        return 0

def get_pool_start_block(nft_id):
    """Get the start_block for a pool from pools.json"""
    pools_file = "tools/pools.json"
    try:
        with open(pools_file, "r") as f:
            pools_data = json.load(f)
        for pool in pools_data.get("pools", []):
            if pool["nft_id"] == nft_id:
                return pool.get("start_block", 38000000)
    except:
        pass
    return 38000000

def fetch_fees(nft_id=None):
    if nft_id is None:
        nft_id = 4227642

    pool_dir = f"tools/pools/{nft_id}"
    cache_file = f"{pool_dir}/fees_data.json"
    default_start = get_pool_start_block(nft_id)

    # Load previous state
    collected_usdc = 0
    collected_cbbtc = 0
    withdrawn_usdc = 0
    withdrawn_cbbtc = 0
    events_count = 0
    start_block = default_start

    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                state = json.load(f)
                start_block = state.get("last_synced_block", start_block)
                collected_usdc = state.get("raw_collected_usdc", 0)
                collected_cbbtc = state.get("raw_collected_cbbtc", 0)
                withdrawn_usdc = state.get("withdrawn_usdc", 0)
                withdrawn_cbbtc = state.get("withdrawn_cbbtc", 0)
                events_count = state.get("events_count", 0)
                if "raw_collected_usdc" not in state:
                    print("Legacy state detected. Re-syncing from scratch...")
                    start_block = default_start
                    collected_usdc = collected_cbbtc = withdrawn_usdc = withdrawn_cbbtc = events_count = 0
        except:
            pass

    current_block = get_block_number()
    if current_block == 0:
        print("Failed to get current block number")
        return None

    if start_block >= current_block:
        print(f"Already synced up to block {current_block}.")
        start_block = current_block - 100

    total_blocks = current_block - start_block
    print(f"Scanning for events for NFT #{nft_id} from {start_block} to {current_block} ({total_blocks} blocks)...")

    # Build chunk list
    chunk_size = 10000
    chunks = []
    block = start_block
    while block <= current_block:
        end_block = min(block + chunk_size, current_block)
        chunks.append((block, end_block, nft_id))
        block = end_block + 1

    print(f"Processing {len(chunks)} chunks with parallel requests...")
    
    # Parallel fetch with 10 workers
    all_logs = []
    completed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_chunk = {executor.submit(fetch_chunk, chunk): chunk for chunk in chunks}
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                logs = future.result()
                all_logs.extend(logs)
                completed += 1
                pct = completed / len(chunks) * 100
                sys.stdout.write(f"\r  Progress: {completed}/{len(chunks)} chunks ({pct:.0f}%)")
                sys.stdout.flush()
            except Exception as e:
                print(f"\n  Error fetching chunk {chunk[0]}-{chunk[1]}: {e}")
                completed += 1

    print(f"\nFound {len(all_logs)} events.")

    # Sort logs by block number to process in order
    all_logs.sort(key=lambda x: int(x.get('blockNumber', '0x0'), 16))

    for log in all_logs:
        topic0 = log.get('topics', [])[0].lower()
        data_hex = log.get('data', '0x')[2:]

        if topic0 == COLLECT_TOPIC and len(data_hex) >= 192:
            amt0 = int(data_hex[64:128], 16)
            amt1 = int(data_hex[128:192], 16)
            collected_usdc += amt0 / 1e6
            collected_cbbtc += amt1 / 1e8
            events_count += 1
            print(f"  [Collect] {amt0/1e6:.4f} USDC + {amt1/1e8:.8f} cbBTC")

        elif topic0 == DECREASE_LIQ_TOPIC and len(data_hex) >= 192:
            amt0 = int(data_hex[64:128], 16)
            amt1 = int(data_hex[128:192], 16)
            withdrawn_usdc += amt0 / 1e6
            withdrawn_cbbtc += amt1 / 1e8
            events_count += 1
            print(f"  [DecreaseLiquidity] Withdrawn: {amt0/1e6:.4f} USDC + {amt1/1e8:.8f} cbBTC")

    true_fee_usdc = max(0, collected_usdc - withdrawn_usdc)
    true_fee_cbbtc = max(0, collected_cbbtc - withdrawn_cbbtc)

    print(f"\n--- Lifetime Totals ---")
    print(f"Raw Collected : {collected_usdc:.4f} USDC | {collected_cbbtc:.8f} cbBTC")
    print(f"Withdrawn     : {withdrawn_usdc:.4f} USDC | {withdrawn_cbbtc:.8f} cbBTC")
    print(f"True Fees     : {true_fee_usdc:.4f} USDC | {true_fee_cbbtc:.8f} cbBTC")
    print(f"-----------------------")

    result = {
        "nft_id": nft_id,
        "total_collected_usdc": true_fee_usdc,
        "total_collected_cbbtc": true_fee_cbbtc,
        "raw_collected_usdc": collected_usdc,
        "raw_collected_cbbtc": collected_cbbtc,
        "withdrawn_usdc": withdrawn_usdc,
        "withdrawn_cbbtc": withdrawn_cbbtc,
        "events_count": events_count,
        "last_synced_block": current_block,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return result

def main():
    if len(sys.argv) > 1:
        nft_id = int(sys.argv[1])
    else:
        nft_id = 4227642

    pool_dir = f"tools/pools/{nft_id}"
    os.makedirs(pool_dir, exist_ok=True)
    output_file = f"{pool_dir}/fees_data.json"

    data = fetch_fees(nft_id)
    if data:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {output_file}")

        with open("tools/fees_data.json", "w") as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
