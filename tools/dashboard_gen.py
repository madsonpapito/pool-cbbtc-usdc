import json
import math
import datetime

# Constants
# Token0: USDC (6 decimals) - 0x8335...
# Token1: cbBTC (8 decimals) - 0xcbb7...
ADDR_USDC = "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
ADDR_CBBTC = "0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf"

DECIMALS_USDC = 6
DECIMALS_CBBTC = 8

def main():
    try:
        with open("tools/position_data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: tools/position_data.json not found. Run fetch_pool_data.py first.")
        return

    # Detect which is which
    if data['token0'] == ADDR_USDC:
        symbol0, symbol1 = "USDC", "cbBTC"
        dec0, dec1 = DECIMALS_USDC, DECIMALS_CBBTC
    else:
        symbol0, symbol1 = "cbBTC", "USDC"
        dec0, dec1 = DECIMALS_CBBTC, DECIMALS_USDC

    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Liquidity Pool Dashboard</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background: #f0f2f5; }}
            .card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .metric {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .label {{ color: #666; }}
            .value {{ font-weight: bold; color: #111; }}
            .range {{ font-family: monospace; background: #eee; padding: 4px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Uniswap V3 Position</h1>
            <div class="metric">
                <span class="label">Pair</span>
                <span class="value">{symbol0} / {symbol1}</span>
            </div>
            <div class="metric">
                <span class="label">Fee Tier</span>
                <span class="value">{data['fee']} (0.05%)</span>
            </div>
            <div class="metric">
                <span class="label">Liquidity (Raw)</span>
                <span class="value">{data['liquidity']}</span>
            </div>
            <div class="metric">
                <span class="label">Tick Range</span>
                <span class="value range">[{data['tick_lower']} , {data['tick_upper']}]</span>
            </div>
            <div class="metric">
                <span class="label">Generated At</span>
                <span class="value">{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("dashboard.html", "w") as f:
        f.write(html)
    print("Dashboard generated: dashboard.html")

if __name__ == "__main__":
    main()
