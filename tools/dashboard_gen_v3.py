import json
import datetime
import math

POSITION_FILE = "tools/position_data.json"
HISTORY_FILE = "tools/history.json"
CONFIG_FILE = "tools/config.json"
FEES_FILE = "tools/fees_data.json"
OUTPUT_FILE = "index.html"

def calculate_hodl_value(initial_investment, initial_price, current_price):
    """
    Calculate HODL value assuming 50/50 split at entry.
    """
    if initial_price <= 0: return initial_investment
    
    # 50% kept in USD, 50% bought in Token1 (cbBTC)
    usd_part = initial_investment / 2
    token_part_amt = usd_part / initial_price
    
    current_val = usd_part + (token_part_amt * current_price)
    return current_val

def main():
    # Load Data
    try:
        with open(POSITION_FILE, "r") as f: pos = json.load(f)
        with open(HISTORY_FILE, "r") as f: history = json.load(f)
        with open(CONFIG_FILE, "r") as f: config = json.load(f)
    except FileNotFoundError as e:
        print(f"Missing file: {e}")
        return

    # Load Automated Fees
    collected_usdc = 0.0
    collected_cbbtc = 0.0
    try:
        with open(FEES_FILE, "r") as f:
            fees_data = json.load(f)
            collected_usdc = fees_data.get('total_collected_usdc', 0)
            collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
    except FileNotFoundError:
        collected_usdc = config.get("fees_collected_usd", 0.0)

    # Values
    value_usd = pos.get('value_usd', 0)
    amount0 = pos.get('amount0', 0)
    amount1 = pos.get('amount1', 0)
    symbol0 = pos.get('symbol0', 'Token0')
    symbol1 = pos.get('symbol1', 'Token1')
    in_range = pos.get('in_range', False)
    price_cbbtc = pos.get('price_cbbtc', 0)
    price_lower = pos.get('price_lower', 0)
    price_upper = pos.get('price_upper', 0)
    price_current = pos.get('price_current', 0)
    
    # Config
    total_invested = config.get("total_invested_usd", 0)
    deposit_date = config.get("deposit_date", "2025-01-01")
    nft_id = config.get("nft_id", 0)
    initial_cbbtc_price = config.get("initial_cbbtc_price", 1)
    
    # Fees Calculation
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    
    unclaimed_0 = pos.get('unclaimed_0', 0) 
    unclaimed_1 = pos.get('unclaimed_1', 0)
    pending_usdc = unclaimed_0 / 1e6
    pending_cbbtc = unclaimed_1 / 1e8
    fees_pending_value = (pending_usdc * 1.0) + (pending_cbbtc * price_cbbtc)
    
    total_fees = fees_pending_value + fees_collected_value
    
    # Metrics
    deposit_dt = datetime.datetime.strptime(deposit_date, "%Y-%m-%d")
    now = datetime.datetime.now()
    position_age_days = (now - deposit_dt).days + (now - deposit_dt).seconds / 86400
    if position_age_days < 0.001: position_age_days = 0.001

    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    # APRs
    daily_yield = (total_fees / total_invested) if total_invested > 0 else 0
    daily_yield_rate = daily_yield / position_age_days
    fee_apr = daily_yield_rate * 365 * 100
    
    total_return_rate = (net_pnl / total_invested) / position_age_days if total_invested > 0 else 0
    total_apr = total_return_rate * 365 * 100
    
    # Impermanent Loss (Value vs HODL)
    hodl_value = calculate_hodl_value(total_invested, initial_cbbtc_price, price_cbbtc)
    
    # IL is the difference between current pool value (excluding fees) and HODL value
    # Expressed as a percentage of HODL value
    il_abs = value_usd - hodl_value
    il_percent = (il_abs / hodl_value) * 100 if hodl_value > 0 else 0
    
    # LP vs HODL (Net)
    # This includes fees
    lp_vs_hodl = (value_usd + total_fees) - hodl_value
    
    price_ratio = price_cbbtc / initial_cbbtc_price if initial_cbbtc_price > 0 else 1

    # Chart Data Preparation (Aggregate by Day) - UPDATED LOGIC
    chart_data = {}
    
    # Initial point (Deposit)
    # Assumption: At deposit, value = total_invested
    chart_data[deposit_date] = total_invested
    
    if history:
        for h in history:
            d = h.get('date', '').split(" ")[0]
            val = h.get('value_usd', 0)
            if d and val > 0:
                chart_data[d] = val
    
    # Ensure current value is the last point
    chart_data[now.strftime("%Y-%m-%d")] = value_usd
    
    sorted_dates = sorted(chart_data.keys())
    values = [chart_data[d] for d in sorted_dates]
    
    # Projections
    daily_fee = total_fees / position_age_days
    weekly_fee = daily_fee * 7
    monthly_fee = daily_fee * 30
    yearly_fee = daily_fee * 365
    
    daily_roi = (daily_fee / total_invested) * 100 if total_invested > 0 else 0
    weekly_roi = daily_roi * 7
    monthly_roi = daily_roi * 30
    yearly_roi = daily_roi * 365

    # Ranges
    range_status = "🟢 In Range" if in_range else "🔴 Out of Range"
    range_class = "text-green-400" if in_range else "text-red-400"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Liquidity Manager v2.1</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #0b0e11; color: #c9d1d9; font-family: 'Inter', sans-serif; }}
        .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }}
        .text-accent {{ color: #2ea043; }}
        .text-danger {{ color: #da3633; }}
        .text-warning {{ color: #d29922; }}
        .gradient-border {{ background: linear-gradient(135deg, #2ea043, #1f6feb); padding: 1px; border-radius: 13px; }}
        .gradient-border-inner {{ background: #161b22; border-radius: 12px; height: 100%; }}
        
        /* Tooltip container */
        .tooltip {{ position: relative; display: inline-block; cursor: help; }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 140px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%; /* Position above */
            left: 50%;
            margin-left: -70px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.75rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .tooltip:hover .tooltiptext {{ visibility: visible; opacity: 1; }}
    </style>
</head>
<body class="p-4 md:p-8 max-w-7xl mx-auto">

    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
            <div class="flex items-center gap-3">
                <span class="text-4xl">🥝</span>
                <h1 class="text-3xl font-bold text-white">Liquidity Manager v2.1</h1>
            </div>
            <p class="text-sm text-gray-500 mt-1">Pool: {symbol0}/{symbol1} (Main) | NFT ID: #{nft_id}</p>
        </div>
        
        <div class="flex items-center gap-4">
             <button id="syncBtn" onclick="syncData()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync Data
            </button>
            <div class="text-right">
                <div class="{range_class} font-bold text-sm tracking-wide">{range_status}</div>
                <div class="text-gray-600 text-xs">{now.strftime("%Y-%m-%d %H:%M")}</div>
            </div>
        </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        
        <!-- Pooled Assets -->
        <div class="gradient-border col-span-1">
            <div class="gradient-border-inner p-5 flex flex-col justify-between">
                <div>
                    <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Pooled Assets</p>
                    <p class="text-3xl font-bold text-white mt-2">${value_usd:,.2f}</p>
                </div>
                <p class="text-xs text-gray-400 mt-2">{position_age_days:.1f} Days Active</p>
            </div>
        </div>

        <!-- Total PnL -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Total PnL</p>
            <p class="text-3xl font-bold {'text-accent' if net_pnl >= 0 else 'text-danger'} mt-2">
                {'+' if net_pnl >= 0 else ''}${net_pnl:,.2f}
            </p>
            <p class="text-xs {'text-accent' if roi_percent >= 0 else 'text-danger'} mt-2">
                {roi_percent:+.2f}% ROI
            </p>
        </div>

        <!-- Fee APR -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Fee APR (Fee Only)</p>
            <p class="text-3xl font-bold text-white mt-2">{fee_apr:.2f}%</p>
            <p class="text-xs text-gray-400 mt-2">Lifetime Avg</p>
        </div>

        <!-- Total APR -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Total APR (incl. Price)</p>
            <p class="text-3xl font-bold {'text-accent' if total_apr >= 0 else 'text-danger'} mt-2">{total_apr:.2f}%</p>
            <p class="text-xs text-danger mt-2">ROI Annualized</p>
        </div>
        
        <!-- Row 2 -->
        
        <!-- ROI -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">ROI</p>
            <p class="text-3xl font-bold {'text-white' if roi_percent >=0 else 'text-white'} mt-2">
                {roi_percent:+.2f}%
            </p>
             <p class="text-xs text-gray-500 mt-2">${net_pnl:.2f}</p>
        </div>
        
        <!-- Impermanent Loss -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Impermanent Loss</p>
            <p class="text-3xl font-bold {'text-danger' if il_percent < -0.01 else 'text-gray-300'} mt-2">
                {il_percent:.2f}%
            </p>
            <p class="text-xs text-danger mt-2">${il_abs:,.2f} USD</p>
        </div>

        <!-- Total Fees -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Total Fees Earned</p>
            <p class="text-3xl font-bold text-yellow-400 mt-2">${total_fees:,.2f}</p>
            <p class="text-xs text-accent mt-2">Collected + Pending</p>
        </div>
        
        <!-- LP vs HODL -->
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">LP vs HODL</p>
            <p class="text-3xl font-bold {'text-accent' if lp_vs_hodl >= 0 else 'text-danger'} mt-2">
                {'+' if lp_vs_hodl >= 0 else ''}${lp_vs_hodl:,.2f}
            </p>
            <p class="text-xs text-accent mt-2">Advantage</p>
        </div>

        <!-- Row 3 -->

        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">cbBTC Price</p>
            <p class="text-2xl font-bold text-white mt-2">${price_cbbtc:,.0f}</p>
            <p class="text-xs text-gray-500 mt-2">Current Market</p>
        </div>
        
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Initial Investment</p>
            <p class="text-2xl font-bold text-white mt-2">${total_invested:,.2f}</p>
            <p class="text-xs text-gray-500 mt-2">Principal</p>
        </div>
        
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Position Age</p>
            <p class="text-2xl font-bold text-white mt-2">{position_age_days:.1f} Days</p>
            <p class="text-xs text-gray-500 mt-2">Since {deposit_date}</p>
        </div>
        
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Deposit Date</p>
            <p class="text-2xl font-bold text-white mt-2">{deposit_date}</p>
            <p class="text-xs text-gray-500 mt-2">Start Date</p>
        </div>

        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Initial cbBTC Price</p>
            <p class="text-2xl font-bold text-white mt-2">${initial_cbbtc_price:,.0f}</p>
            <p class="text-xs text-gray-500 mt-2">Avg Entry</p>
        </div>

        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Token Balances</p>
            <p class="text-xl font-bold text-white mt-2">{amount0:,.2f} USDC</p>
            <p class="text-xs text-gray-500 mt-1">{amount1:,.5f} cbBTC</p>
        </div>
        
        <div class="card p-5">
            <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Price Range</p>
            <p class="text-2xl font-bold text-white mt-2">{price_lower:,.0f}</p>
            <p class="text-xs text-gray-500 mt-2">Min Price</p>
        </div>
        
        <div class="card p-5">
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full {'bg-green-500' if in_range else 'bg-red-500'}"></span>
                <p class="text-gray-500 text-xs uppercase font-semibold tracking-wider">Range Status</p>
            </div>
            <p class="text-2xl font-bold text-white mt-2">{price_upper:,.0f}</p>
            <p class="text-xs text-gray-500 mt-2">Max Price</p>
        </div>
    </div>
    
    <!-- Chart -->
    <div class="mb-8">
        <canvas id="valueChart" height="80" style="max-height: 400px;"></canvas>
    </div>

    <!-- Performance Summary (Tooltips Added) -->
    <div class="card p-6 mb-8">
        <h3 class="text-sm font-semibold text-white mb-6 flex items-center gap-2">
            📊 Performance Summary
        </h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
            <div class="tooltip">
                <p class="text-gray-500 text-xs mb-1">Daily Fee Income</p>
                <p class="text-white font-mono text-xl font-bold">${daily_fee:,.4f}</p>
                <span class="tooltiptext">{daily_roi:.4f}% of Invested</span>
            </div>
            
            <div class="tooltip">
                <p class="text-gray-500 text-xs mb-1">Weekly Fee Income</p>
                <p class="text-white font-mono text-xl font-bold">${weekly_fee:,.4f}</p>
                <span class="tooltiptext">{weekly_roi:.4f}% of Invested</span>
            </div>
            
            <div class="tooltip">
                <p class="text-gray-500 text-xs mb-1">Est. Monthly Fees</p>
                <p class="text-white font-mono text-xl font-bold">${monthly_fee:,.2f}</p>
                <span class="tooltiptext">{monthly_roi:.2f}% of Invested</span>
            </div>
            
            <div class="tooltip">
                <p class="text-gray-500 text-xs mb-1">Est. Yearly Fees</p>
                <p class="text-white font-mono text-xl font-bold">${yearly_fee:,.2f}</p>
                <span class="tooltiptext">{yearly_roi:.2f}% of Invested</span>
            </div>
        </div>
    </div>

    <!-- Sync Script -->
    <script>
        async function syncData() {{
            const btn = document.getElementById('syncBtn');
            const originalText = btn.innerHTML;
            
            const isVercel = !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1');
            
            if (isVercel) {{
                alert('Sync de dados somente localmente via python.');
                return;
            }}
            
            btn.innerHTML = 'Syncing...';
            btn.disabled = true;
            btn.classList.add('opacity-75', 'cursor-not-allowed');

            try {{
                const response = await fetch('/api/sync', {{ method: 'POST' }});
                const data = await response.json();
                
                if (data.success) {{
                    window.location.reload();
                }} else {{
                    alert('Error: ' + data.message);
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    btn.classList.remove('opacity-75', 'cursor-not-allowed');
                }}
            }} catch (error) {{
                console.error('Error:', error);
                alert('Connection failed. Server running?');
                btn.innerHTML = originalText;
                btn.disabled = false;
                btn.classList.remove('opacity-75', 'cursor-not-allowed');
            }}
        }}

        // Chart
        const ctx = document.getElementById('valueChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(46, 160, 67, 0.2)');
        gradient.addColorStop(1, 'rgba(46, 160, 67, 0.0)');

        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(sorted_dates)},
                datasets: [{{
                    label: 'Position Value (USD)',
                    data: {json.dumps(values)},
                    borderColor: '#2ea043',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#161b22',
                        titleColor: '#8b949e',
                        bodyColor: '#c9d1d9',
                        borderColor: '#30363d',
                        borderWidth: 1
                    }}
                }},
                scales: {{
                    y: {{
                        grid: {{ color: '#21262d' }},
                        ticks: {{ color: '#8b949e' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#8b949e', maxTicksLimit: 10 }}
                    }}
                }},
                interaction: {{
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
