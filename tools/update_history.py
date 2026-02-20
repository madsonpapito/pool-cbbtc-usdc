import json
import datetime
import time
import os
import requests

HISTORY_FILE = "tools/history.json"
DATA_FILE = "tools/position_data.json"

PRICE_USDC = 1.0

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
    
    # Get live cbBTC price (fallback to price from position data)
    fallback_price = snapshot.get('price_cbbtc', 68000.0)
    price_cbbtc = get_cbbtc_price(fallback=fallback_price)
    
    snapshot['prices'] = {
        "USDC": PRICE_USDC,
        "cbBTC": price_cbbtc
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
