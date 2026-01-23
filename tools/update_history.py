import json
import datetime
import time
import os

HISTORY_FILE = "tools/history.json"
DATA_FILE = "tools/position_data.json"

# Mock Prices for MVP (In prod, fetch from Coingecko)
PRICE_USDC = 1.0
PRICE_CBBTC = 98000.0 # TODO: Fetch live

def main():
    # 1. Read latest snapshot
    try:
        with open(DATA_FILE, "r") as f:
            snapshot = json.load(f)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found. Run fetch_pool_data.py first.")
        return

    # 2. Add Metadata (Time, Values)
    now = datetime.datetime.now()
    snapshot['timestamp'] = int(time.time())
    snapshot['date'] = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate Estimated USD Value (Liquidity is complex, approximating via Token Amounts if we had them)
    # Since fetch_pool_data.py doesn't decode Amount0/Amount1 yet (complex math), 
    # we will track Raw Liquidity and Unclaimed Fees for now.
    # Future improvement: Calculate Amount0/Amount1 using SqrtPrice.
    
    snapshot['prices'] = {
        "USDC": PRICE_USDC,
        "cbBTC": PRICE_CBBTC
    }

    # 3. Append to History
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    history.append(snapshot)

    # 4. Save
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    
    print(f"History updated. Total snapshots: {len(history)}")

if __name__ == "__main__":
    main()
