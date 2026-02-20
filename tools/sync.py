import subprocess
import json
import time
import sys
import os

POOLS_FILE = "tools/pools.json"

def run_script(script_name, args=None):
    cmd = [sys.executable, f"tools/{script_name}"]
    if args:
        cmd.extend([str(a) for a in args])
    
    print(f"--- Running {script_name} {' '.join(str(a) for a in (args or []))} ---")
    try:
        result = subprocess.run(cmd, check=True, text=True)
        print(f"--- {script_name} completed ---")
        return True
    except subprocess.CalledProcessError as e:
        print(f"!!! Error running {script_name}: {e}")
        return False

def main():
    start_time = time.time()
    
    # Load pools registry
    try:
        with open(POOLS_FILE, "r") as f:
            pools_data = json.load(f)
        pools = pools_data.get("pools", [])
    except FileNotFoundError:
        print(f"Error: {POOLS_FILE} not found.")
        sys.exit(1)
    
    print(f"Found {len(pools)} pools to sync.\n")
    
    # Sync each pool
    for pool in pools:
        nft_id = pool["nft_id"]
        label = pool.get("label", f"Pool #{nft_id}")
        print(f"\n{'='*50}")
        print(f"Syncing: {label} (NFT #{nft_id})")
        print(f"{'='*50}")
        
        # 1. Fetch position data
        if not run_script("fetch_pool_data.py", [nft_id]):
            print(f"Skipping pool {nft_id} due to error.")
            continue
        
        # 2. Fetch collected fees
        run_script("fetch_collected_fees.py", [nft_id])
    
    # 3. Generate multi-pool dashboard
    print(f"\n{'='*50}")
    print("Generating multi-pool dashboard...")
    print(f"{'='*50}")
    run_script("dashboard_gen_v3.py")
    
    elapsed = time.time() - start_time
    print(f"\nSync completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
