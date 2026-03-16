import subprocess
import json
import time
import sys
import os

# Allow importing from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.providers.factory import ProviderFactory

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

def sync_pool(pool_config):
    nft_id = pool_config["nft_id"]
    exchange = pool_config.get("exchange", "uniswap_v3")
    label = pool_config.get("label", f"Pool #{nft_id}")
    
    print(f"\n{'='*50}")
    print(f"Syncing: {label} ({exchange} | NFT #{nft_id})")
    print(f"{'='*50}")

    try:
        provider = ProviderFactory.create(pool_config)
        
        # 1. Fetch position data
        print(f"--> Fetching position data via {exchange} provider...")
        pos_data = provider.fetch_position_data()
        
        if pos_data:
            pool_dir = f"tools/pools/{nft_id}"
            os.makedirs(pool_dir, exist_ok=True)
            with open(f"{pool_dir}/position_data.json", "w") as f:
                json.dump(pos_data, f, indent=2)
            print(f"    ✓ Position data saved to {pool_dir}/position_data.json")
        else:
            # Fallback to legacy script if provider returns nothing (for safety during migration)
            print(f"    ! Provider returned no data, falling back to legacy script...")
            run_script("fetch_pool_data.py", [nft_id])

        # 2. Fetch fees data
        # Note: Historical fee sync still uses scripts for now, will be moved to providers in STORY-004 fix
        if exchange == "uniswap_v3":
            run_script("fetch_collected_fees.py", [nft_id])
        else:
            print(f"    > Fee sync for {exchange} not yet fully implemented, skipping script.")

        # 3. Update history
        run_script("update_history.py", [nft_id])
        return True
        
    except Exception as e:
        print(f"!!! Error syncing {label}: {e}")
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
    
    # Sync each pool using the new provider architecture
    for pool in pools:
        sync_pool(pool)
    
    # 3. Generate multi-pool dashboard
    print(f"\n{'='*50}")
    print("Generating multi-pool dashboard...")
    print(f"{'='*50}")
    run_script("dashboard_gen_v3.py")
    
    elapsed = time.time() - start_time
    print(f"\nSync completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
