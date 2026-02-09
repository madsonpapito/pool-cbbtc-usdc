import os
import json
import shutil

def init_multipool():
    # 1. Ensure data/pools exists
    base_dir = "data/pools"
    os.makedirs(base_dir, exist_ok=True)
    
    # 2. Migrate Current Pool (4227642)
    current_id = 4227642
    current_dir = f"{base_dir}/{current_id}"
    os.makedirs(current_dir, exist_ok=True)
    
    files_to_migrate = [
        ("tools/config.json", "config.json"),
        ("tools/history.json", "history.json"),
        ("tools/fees_data.json", "fees_data.json"),
        ("tools/position_data.json", "position_data.json")
    ]
    
    print(f"Migrating Pool #{current_id}...")
    for src, dst_name in files_to_migrate:
        dst = f"{current_dir}/{dst_name}"
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  Copied {src} -> {dst}")
        else:
            print(f"  Skipped {src} (Not found)")
            
    # 3. Initialize New Pool (1345196)
    new_id = 1345196
    new_dir = f"{base_dir}/{new_id}"
    os.makedirs(new_dir, exist_ok=True)
    
    # Create default config for new pool
    new_config = {
        "nft_id": new_id,
        "total_invested_usd": 0.0,
        "deposit_date": "2026-02-09",
        "last_deposit_date": "2026-02-09",
        "last_deposit_amount": 0.0,
        "fees_collected_usd": 0.0,
        "initial_cbbtc_price": 0
    }
    
    config_path = f"{new_dir}/config.json"
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=4)
        print(f"Initialized New Pool #{new_id} at {config_path}")
    else:
        print(f"Pool #{new_id} already exists.")
        
    # 4. Create pools.json registry
    pools_registry = [
        {"nft_id": 4227642, "symbol": "USDC/cbBTC (Main)"},
        {"nft_id": 1345196, "symbol": "New Pool"}
    ]
    
    with open("tools/pools.json", "w") as f:
        json.dump(pools_registry, f, indent=4)
    print("Updated tools/pools.json registry.")

if __name__ == "__main__":
    init_multipool()
