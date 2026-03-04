import json
import datetime
import time
import os
import requests
import sys

def get_cbbtc_price(fallback=68000.0):
    """Fetch live cbBTC price from CoinGecko API"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=coinbase-wrapped-btc&vs_currencies=usd"
        res = requests.get(url, timeout=5)
        price = res.json().get('coinbase-wrapped-btc', {}).get('usd')
        if price:
            print(f"cbBTC price (CoinGecko): ${price:,.2f}")
            return float(price)
    except Exception as e:
        print(f"CoinGecko error: {e}")
    print(f"Using fallback price: ${fallback:,.2f}")
    return fallback

def main():
    # 1. NFT ID from arguments
    if len(sys.argv) < 2:
        print("Usage: python tools/update_history.py <nft_id>")
        return
    
    nft_id = sys.argv[1]
    pool_dir = f"tools/pools/{nft_id}"
    data_file = f"{pool_dir}/position_data.json"
    history_file = f"{pool_dir}/history.json"

    # 2. Read latest snapshot
    try:
        with open(data_file, "r") as f:
            snapshot = json.load(f)
    except FileNotFoundError:
        print(f"Error: {data_file} not found. Run fetch_pool_data.py {nft_id} first.")
        return

    # 3. Add Metadata (Time, Values)
    now = datetime.datetime.now()
    snapshot['timestamp'] = int(time.time())
    snapshot['date'] = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get live cbBTC price (fallback to price from position data)
    fallback_price = snapshot.get('price_cbbtc', 68000.0)
    price_cbbtc = get_cbbtc_price(fallback=fallback_price)
    
    snapshot['prices'] = {
        "USDC": 1.0,
        "cbBTC": price_cbbtc
    }

    # 4. Append to History
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    history.append(snapshot)

    # 5. Save
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)
    
    print(f"History updated for Pool {nft_id}. Total snapshots: {len(history)}")

    # 6. Legacy support (if it's the main pool)
    if nft_id == "4227642":
        with open("tools/history.json", "w") as f:
            json.dump(history, f, indent=2)

if __name__ == "__main__":
    main()
