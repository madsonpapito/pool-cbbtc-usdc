import json
import datetime
import math

POSITION_FILE = "tools/position_data.json"
HISTORY_FILE = "tools/history.json"
CONFIG_FILE = "tools/config.json"
FEES_FILE = "tools/fees_data.json"
OUTPUT_FILE = "index.html"

def calculate_impermanent_loss(price_ratio):
    """
    Calculate Impermanent Loss based on price change ratio.
    """
    if price_ratio <= 0: return 0
    sqrt_ratio = math.sqrt(price_ratio)
    il = 2 * sqrt_ratio / (1 + price_ratio) - 1
    return il * 100

def calculate_fee_apr(total_fees, position_value, days_active):
    """
    Calculate Fee APR (annualized return from fees only)
    """
    if position_value <= 0 or days_active <= 0: return 0
    daily_rate = (total_fees / position_value) / days_active
    apr = daily_rate * 365 * 100
    return apr

def main():
    # Load Data
    try:
        with open(POSITION_FILE, "r") as f: pos = json.load(f)
        with open(HISTORY_FILE, "r") as f: history = json.load(f)
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except FileNotFoundError as e:
        print(f"Missing file: {e}")
        return

    # Load Automated Fees (Optional)
    collected_usdc = 0.0
    collected_cbbtc = 0.0
    try:
        with open(FEES_FILE, "r") as f:
            fees_data = json.load(f)
            collected_usdc = fees_data.get('total_collected_usdc', 0)
            collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
            print(f"Loaded automated fees: {collected_usdc} USDC, {collected_cbbtc} cbBTC")
    except FileNotFoundError:
        print("Fees data not found, using manual config if available.")
        collected_usdc = config.get("fees_collected_usd", 0.0) # Fallback

    # Real values
    value_usd = pos.get('value_usd', 0)
    fees_usd = pos.get('fees_usd', 0) # Pending
    amount0 = pos.get('amount0', 0)
    amount1 = pos.get('amount1', 0)
    symbol0 = pos.get('symbol0', 'Token0')
    symbol1 = pos.get('symbol1', 'Token1')
    in_range = pos.get('in_range', False)
    price_cbbtc = pos.get('price_cbbtc', 0)
    price_lower = pos.get('price_lower', 0)
    price_upper = pos.get('price_upper', 0)
    price_current = pos.get('price_current', 0)
    
    # Config values
    total_invested = config.get("total_invested_usd", 69.06)
    deposit_date = config.get("deposit_date", "2025-11-24")
    nft_id = config.get("nft_id", 4227642)
    initial_cbbtc_price = config.get("initial_cbbtc_price", 97000)
    
    # Calculate Collected Fees Value (at current price)
    # USDC is stable (1.0), cbBTC is price_cbbtc
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    
    # Pending fees from unclaimed tokens
    unclaimed_0 = pos.get('unclaimed_0', 0)  # Raw USDC (6 decimals)
    unclaimed_1 = pos.get('unclaimed_1', 0)  # Raw cbBTC (8 decimals)
    pending_usdc = unclaimed_0 / 1e6
    pending_cbbtc = unclaimed_1 / 1e8
    fees_usd = (pending_usdc * 1.0) + (pending_cbbtc * price_cbbtc)
    
    # Total fees (Collected + Pending)
    total_fees = fees_usd + fees_collected_value
    
    # Calculate Position Age
    deposit_dt = datetime.datetime.strptime(deposit_date, "%Y-%m-%d")
    now = datetime.datetime.now()
    position_age_days = (now - deposit_dt).days + (now - deposit_dt).seconds / 86400
    
    # Calculate PnL and ROI
    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    # APRs
    fee_apr = calculate_fee_apr(total_fees, total_invested, position_age_days)
    total_apr = (roi_percent / position_age_days) * 365 if position_age_days > 0 else 0
    
    # IL
    price_ratio = price_cbbtc / initial_cbbtc_price if initial_cbbtc_price > 0 else 1
    il_percent = calculate_impermanent_loss(price_ratio)
    
    # LP vs HODL
    initial_btc = (total_invested * 0.5) / initial_cbbtc_price
    initial_usdc = total_invested * 0.5
    hodl_value = (initial_btc * price_cbbtc) + initial_usdc
    lp_vs_hodl = (value_usd + total_fees) - hodl_value
    
    # History for value chart
    dates = [h.get('date', '').split(" ")[0] for h in history] if history else [now.strftime("%Y-%m-%d")]
    values = [h.get('value_usd', value_usd) if 'value_usd' in h else value_usd for h in history] if history else [value_usd]
    
    # Status
    range_status = "🟢 In Range" if in_range else "🔴 Out of Range"
    range_class = "text-green-400" if in_range else "text-red-400"

    # Projections
    daily_fee = total_fees / max(position_age_days, 1)
    weekly_fee = daily_fee * 7
    monthly_fee = daily_fee * 30
    yearly_fee = daily_fee * 365
    
    daily_roi = (daily_fee / total_invested) * 100 if total_invested > 0 else 0
    weekly_roi = (weekly_fee / total_invested) * 100 if total_invested > 0 else 0
    monthly_roi = (monthly_fee / total_invested) * 100 if total_invested > 0 else 0
    yearly_roi = (yearly_fee / total_invested) * 100 if total_invested > 0 else 0

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Liquidity Tracker | {symbol0}/{symbol1}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ background-color: #0b0e11; color: #c9d1d9; font-family: 'Inter', sans-serif; }}
        .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }}
        .text-accent {{ color: #2ea043; }}
        .text-danger {{ color: #da3633; }}
        .text-warning {{ color: #d29922; }}
        .gradient-border {{ background: linear-gradient(135deg, #2ea043, #1f6feb); padding: 2px; border-radius: 14px; }}
        .gradient-border-inner {{ background: #161b22; border-radius: 12px; }}
    </style>
</head>
<body class="p-6 max-w-7xl mx-auto">

    <!-- Header -->
    <div class="flex justify-between items-center mb-8">
        <div>
            <h1 class="text-2xl font-bold text-white">Liquidity Pool Tracker: <span class="text-blue-400">{symbol0}/{symbol1}</span></h1>
            <p class="text-sm text-gray-500">NFT #{nft_id} | Base Network | Uniswap V3</p>
        </div>
        <div class="flex items-center gap-4">
             <button id="syncBtn" onclick="syncData()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync Data
            </button>
            <span class="{range_class} text-sm font-medium">{range_status}</span>
            <span class="text-gray-500 text-sm">{now.strftime("%Y-%m-%d %H:%M")}</span>
        </div>
    </div>

    <!-- KPI Cards Row 1 - Main Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
        <div class="gradient-border">
            <div class="gradient-border-inner p-5">
                <p class="text-gray-500 text-xs mb-1">Pooled Assets</p>
                <p class="text-2xl font-bold text-white">${value_usd:,.2f}</p>
            </div>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Total PnL</p>
            <p class="text-2xl font-bold {'text-accent' if net_pnl >= 0 else 'text-danger'}">
                {'+' if net_pnl >= 0 else ''}${net_pnl:,.2f}
            </p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Fee APR</p>
            <p class="text-2xl font-bold text-yellow-400">{fee_apr:.2f}%</p>
            <p class="text-xs text-gray-500">From fees only</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Total APR</p>
            <p class="text-2xl font-bold {'text-accent' if total_apr >= 0 else 'text-danger'}">{total_apr:.2f}%</p>
            <p class="text-xs text-gray-500">Incl. value change</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">ROI</p>
            <p class="text-2xl font-bold {'text-accent' if roi_percent >= 0 else 'text-danger'}">
                {'+' if roi_percent >= 0 else ''}{roi_percent:.2f}%
            </p>
        </div>
    </div>

    <!-- KPI Cards Row 2 - IL & Fees -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Impermanent Loss</p>
            <p class="text-2xl font-bold {'text-danger' if il_percent < -0.5 else 'text-warning' if il_percent < 0 else 'text-accent'}">
                {il_percent:+.2f}%
            </p>
            <p class="text-xs text-gray-500">Price ratio: {price_ratio:.2f}x</p>
        </div>
        <div class="card p-5" title="Collected: {collected_usdc:.4f} USDC + {collected_cbbtc:.8f} cbBTC&#10;Pending: {pending_usdc:.4f} USDC + {pending_cbbtc:.8f} cbBTC">
            <p class="text-gray-500 text-xs mb-1">Total Fees Earned</p>
            <div class="flex items-baseline gap-2">
                 <p class="text-2xl font-bold text-yellow-400">${total_fees:,.2f}</p>
                 <span class="text-xs text-gray-500">(All Time)</span>
            </div>
            <div class="text-xs text-gray-500 mt-1 flex flex-col">
                <span>collected: <span class="text-gray-300">${fees_collected_value:,.2f}</span></span>
                 <span>pending: <span class="text-gray-300">${fees_usd:,.2f}</span></span>
            </div>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">LP vs HODL</p>
            <p class="text-2xl font-bold {'text-accent' if lp_vs_hodl >= 0 else 'text-danger'}">
                {'+' if lp_vs_hodl >= 0 else ''}${lp_vs_hodl:,.2f}
            </p>
            <p class="text-xs text-gray-500">HODL value: ${hodl_value:,.2f}</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">cbBTC Price</p>
            <p class="text-2xl font-bold text-white">${price_cbbtc:,.0f}</p>
            <p class="text-xs {'text-accent' if price_ratio >= 1 else 'text-danger'}">
                {'+' if price_ratio >= 1 else ''}{((price_ratio - 1) * 100):.1f}% since deposit
            </p>
        </div>
    </div>

    <!-- KPI Cards Row 3 - Position Info -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Initial Investment</p>
            <p class="text-xl font-bold text-white">${total_invested:,.2f}</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Position Age</p>
            <p class="text-xl font-bold text-white">{position_age_days:.1f} days</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Deposit Date</p>
            <p class="text-xl font-bold text-white">{deposit_date}</p>
        </div>
        <div class="card p-5">
            <p class="text-gray-500 text-xs mb-1">Initial cbBTC Price</p>
            <p class="text-xl font-bold text-white">${initial_cbbtc_price:,.0f}</p>
        </div>
    </div>

    <!-- Token Balances & Range -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        <div class="card p-5">
            <h3 class="text-sm text-gray-400 mb-4">Token Balances</h3>
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <span class="text-gray-300">{symbol0}</span>
                    <span class="font-mono text-xl text-white">{amount0:,.6f}</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-300">{symbol1}</span>
                    <span class="font-mono text-xl text-white">{amount1:,.8f}</span>
                </div>
            </div>
        </div>
        <div class="card p-5">
            <h3 class="text-sm text-gray-400 mb-4">Price Range (cbBTC/USDC)</h3>
            <div class="space-y-3">
                <div class="flex justify-between">
                    <span class="text-gray-300">MIN</span>
                    <span class="font-mono text-cyan-400">${price_lower:,.2f}</span>
                </div>
                <div class="flex justify-between">
                    <span class="text-gray-300">MAX</span>
                    <span class="font-mono text-cyan-400">${price_upper:,.2f}</span>
                </div>
                <div class="flex justify-between pt-2 border-t border-gray-700">
                    <span class="text-gray-300">Current Price</span>
                    <span class="font-mono {'text-green-400' if in_range else 'text-red-400'}">${price_current:,.2f}</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Chart -->
    <div class="card p-6 mb-8">
        <h3 class="text-sm font-semibold text-gray-300 mb-4">Value History</h3>
        <canvas id="valueChart" height="100"></canvas>
    </div>
    
    <!-- Summary Card -->
    <div class="card p-6 mb-4">
        <h3 class="text-sm font-semibold text-gray-300 mb-4">📊 Performance Summary</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div title="Return: {daily_roi:.4f}% of Invested">
                <p class="text-gray-500 text-xs">Daily Fee Income</p>
                <p class="text-white font-mono text-lg">${daily_fee:,.4f}</p>
            </div>
            <div title="Return: {weekly_roi:.4f}% of Invested">
                <p class="text-gray-500 text-xs">Weekly Fee Income</p>
                <p class="text-white font-mono text-lg">${weekly_fee:,.4f}</p>
            </div>
            <div title="Return: {monthly_roi:.2f}% of Invested">
                <p class="text-gray-500 text-xs">Est. Monthly Fees</p>
                <p class="text-white font-mono text-lg">${monthly_fee:,.2f}</p>
            </div>
            <div title="Return: {yearly_roi:.2f}% of Invested">
                <p class="text-gray-500 text-xs">Est. Yearly Fees</p>
                <p class="text-white font-mono text-lg">${yearly_fee:,.2f}</p>
            </div>
        </div>
    </div>

    <!-- Sync Logic -->
    <script>
        async function syncData() {{
            const btn = document.getElementById('syncBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = 'Syncing...';
            btn.disabled = true;
            btn.classList.add('opacity-75', 'cursor-not-allowed');

            try {{
                const response = await fetch('/api/sync', {{ method: 'POST' }});
                const data = await response.json();
                
                if (data.success) {{
                    alert('Sync complete! Refreshing page...');
                    window.location.reload();
                }} else {{
                    alert('Error: ' + data.message);
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    btn.classList.remove('opacity-75', 'cursor-not-allowed');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                alert('Connection failed. Make sure server.py is running.');
                btn.innerHTML = originalText;
                btn.disabled = false;
                btn.classList.remove('opacity-75', 'cursor-not-allowed');
            }}
        }}

        new Chart(document.getElementById('valueChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [{{
                    label: 'Value USD',
                    data: {json.dumps(values)},
                    borderColor: '#2ea043',
                    backgroundColor: 'rgba(46, 160, 67, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ grid: {{ color: '#21262d' }} }},
                    x: {{ grid: {{ display: false }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generated with correct values: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
