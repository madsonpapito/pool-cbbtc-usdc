import json
import datetime
import math
import os

POOLS_FILE = "tools/pools.json"
OUTPUT_FILE = "index.html"

def calculate_impermanent_loss(price_ratio):
    if price_ratio <= 0: return 0
    sqrt_ratio = math.sqrt(price_ratio)
    il = 2 * sqrt_ratio / (1 + price_ratio) - 1
    return il * 100

def calculate_fee_apr(total_fees, position_value, days_active):
    if position_value <= 0 or days_active <= 0: return 0
    daily_rate = (total_fees / position_value) / days_active
    apr = daily_rate * 365 * 100
    return apr

def load_pool_data(nft_id):
    """Load all data for a single pool"""
    pool_dir = f"tools/pools/{nft_id}"
    
    try:
        with open(f"{pool_dir}/position_data.json", "r") as f: pos = json.load(f)
    except FileNotFoundError:
        print(f"  Warning: No position data for pool {nft_id}")
        return None
    
    try:
        with open(f"{pool_dir}/config.json", "r") as f: config = json.load(f)
    except FileNotFoundError:
        config = {}
    
    try:
        with open(f"{pool_dir}/fees_data.json", "r") as f: fees_data = json.load(f)
    except FileNotFoundError:
        fees_data = {}
    
    try:
        with open(f"{pool_dir}/history.json", "r") as f: history = json.load(f)
    except FileNotFoundError:
        history = []
    
    return {"pos": pos, "config": config, "fees": fees_data, "history": history}

def calc_metrics(pool_entry, pool_data):
    """Calculate all metrics for a pool"""
    pos = pool_data["pos"]
    config = pool_data["config"]
    fees_data = pool_data["fees"]
    history = pool_data["history"]
    
    nft_id = pool_entry["nft_id"]
    
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
    
    # Config values (from pools.json or per-pool config)
    total_invested = pool_entry.get("total_invested_usd", config.get("total_invested_usd", 0))
    deposit_date = pool_entry.get("deposit_date", config.get("deposit_date", "2025-01-01"))
    initial_cbbtc_price = pool_entry.get("initial_cbbtc_price", config.get("initial_cbbtc_price", 97000))
    
    # Fees
    collected_usdc = fees_data.get('total_collected_usdc', 0)
    collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    
    unclaimed_0 = pos.get('unclaimed_0', 0)
    unclaimed_1 = pos.get('unclaimed_1', 0)
    pending_usdc = unclaimed_0 / 1e6
    pending_cbbtc = unclaimed_1 / 1e8
    fees_usd = (pending_usdc * 1.0) + (pending_cbbtc * price_cbbtc)
    total_fees = fees_usd + fees_collected_value
    
    # Position Age
    deposit_dt = datetime.datetime.strptime(deposit_date, "%Y-%m-%d")
    now = datetime.datetime.now()
    position_age_days = (now - deposit_dt).days + (now - deposit_dt).seconds / 86400
    
    # PnL / ROI
    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    # APRs
    fee_apr = calculate_fee_apr(total_fees, total_invested, position_age_days)
    total_apr = (roi_percent / position_age_days) * 365 if position_age_days > 0 else 0
    
    # IL
    price_ratio = price_cbbtc / initial_cbbtc_price if initial_cbbtc_price > 0 else 1
    il_percent = calculate_impermanent_loss(price_ratio)
    
    # LP vs HODL
    initial_btc = (total_invested * 0.5) / initial_cbbtc_price if initial_cbbtc_price > 0 else 0
    initial_usdc = total_invested * 0.5
    hodl_value = (initial_btc * price_cbbtc) + initial_usdc
    lp_vs_hodl = (value_usd + total_fees) - hodl_value
    
    # Projections
    daily_fee = total_fees / max(position_age_days, 1)
    
    # History for chart
    dates = [h.get('date', '').split(" ")[0] for h in history] if history else [now.strftime("%Y-%m-%d")]
    values = [h.get('value_usd', value_usd) for h in history] if history else [value_usd]
    
    return {
        "nft_id": nft_id,
        "symbol0": symbol0, "symbol1": symbol1,
        "value_usd": value_usd, "amount0": amount0, "amount1": amount1,
        "in_range": in_range, "price_cbbtc": price_cbbtc,
        "price_lower": price_lower, "price_upper": price_upper, "price_current": price_current,
        "total_invested": total_invested, "deposit_date": deposit_date,
        "initial_cbbtc_price": initial_cbbtc_price,
        "fees_collected_value": fees_collected_value, "fees_usd": fees_usd,
        "total_fees": total_fees, "collected_usdc": collected_usdc, "collected_cbbtc": collected_cbbtc,
        "pending_usdc": pending_usdc, "pending_cbbtc": pending_cbbtc,
        "position_age_days": position_age_days,
        "net_pnl": net_pnl, "roi_percent": roi_percent,
        "fee_apr": fee_apr, "total_apr": total_apr,
        "il_percent": il_percent, "price_ratio": price_ratio,
        "hodl_value": hodl_value, "lp_vs_hodl": lp_vs_hodl,
        "daily_fee": daily_fee,
        "weekly_fee": daily_fee * 7, "monthly_fee": daily_fee * 30, "yearly_fee": daily_fee * 365,
        "dates": dates, "values": values,
        "label": pool_entry.get("label", f"Pool #{nft_id}")
    }

def generate_pool_html(m, pool_index):
    """Generate HTML content section for one pool"""
    range_status = "🟢 In Range" if m['in_range'] else "🔴 Out of Range"
    range_class = "text-green-400" if m['in_range'] else "text-red-400"
    now = datetime.datetime.now()
    
    daily_roi = (m['daily_fee'] / m['total_invested']) * 100 if m['total_invested'] > 0 else 0
    weekly_roi = (m['weekly_fee'] / m['total_invested']) * 100 if m['total_invested'] > 0 else 0
    monthly_roi = (m['monthly_fee'] / m['total_invested']) * 100 if m['total_invested'] > 0 else 0
    yearly_roi = (m['yearly_fee'] / m['total_invested']) * 100 if m['total_invested'] > 0 else 0
    
    display = "block" if pool_index == 0 else "none"
    
    return f"""
    <div id="pool-{m['nft_id']}" class="pool-content" style="display: {display};">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
            <div>
                <h2 class="text-xl font-bold text-white">{m['symbol0']}/{m['symbol1']} <span class="text-sm text-gray-500">NFT #{m['nft_id']}</span></h2>
                <p class="text-sm text-gray-500">Base Network | Uniswap V3 | Fee: 0.05%</p>
            </div>
            <div class="flex items-center gap-3">
                <span class="{range_class} text-sm font-medium">{range_status}</span>
            </div>
        </div>

        <!-- KPI Row 1 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div class="gradient-border"><div class="gradient-border-inner p-5">
                <p class="text-gray-500 text-xs mb-1">Pooled Assets</p>
                <p class="text-2xl font-bold text-white">${m['value_usd']:,.2f}</p>
                <p class="text-xs text-gray-500">{m['position_age_days']:.1f} Days Active</p>
            </div></div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Total PnL</p>
                <p class="text-2xl font-bold {'text-accent' if m['net_pnl'] >= 0 else 'text-danger'}">
                    {'+' if m['net_pnl'] >= 0 else ''}${m['net_pnl']:,.2f}
                </p>
                <p class="text-xs {'text-accent' if m['roi_percent'] >= 0 else 'text-danger'}">{m['roi_percent']:+.2f}% ROI</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Fee APR</p>
                <p class="text-2xl font-bold text-yellow-400">{m['fee_apr']:.2f}%</p>
                <p class="text-xs text-gray-500">From fees only</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Total APR</p>
                <p class="text-2xl font-bold {'text-accent' if m['total_apr'] >= 0 else 'text-danger'}">{m['total_apr']:.2f}%</p>
                <p class="text-xs text-gray-500">Incl. value change</p>
            </div>
        </div>

        <!-- KPI Row 2 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Impermanent Loss</p>
                <p class="text-2xl font-bold {'text-danger' if m['il_percent'] < -0.5 else 'text-warning' if m['il_percent'] < 0 else 'text-accent'}">
                    {m['il_percent']:+.2f}%
                </p>
                <p class="text-xs text-gray-500">Price ratio: {m['price_ratio']:.2f}x</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Total Fees Earned</p>
                <div class="flex items-baseline gap-2">
                    <p class="text-2xl font-bold text-yellow-400">${m['total_fees']:,.2f}</p>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                    <span>collected: <span class="text-gray-300">${m['fees_collected_value']:,.2f}</span></span> |
                    <span>pending: <span class="text-gray-300">${m['fees_usd']:,.2f}</span></span>
                </div>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">LP vs HODL</p>
                <p class="text-2xl font-bold {'text-accent' if m['lp_vs_hodl'] >= 0 else 'text-danger'}">
                    {'+' if m['lp_vs_hodl'] >= 0 else ''}${m['lp_vs_hodl']:,.2f}
                </p>
                <p class="text-xs text-gray-500">HODL: ${m['hodl_value']:,.2f}</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">cbBTC Price</p>
                <p class="text-2xl font-bold text-white">${m['price_cbbtc']:,.0f}</p>
                <p class="text-xs {'text-accent' if m['price_ratio'] >= 1 else 'text-danger'}">
                    {'+' if m['price_ratio'] >= 1 else ''}{((m['price_ratio'] - 1) * 100):.1f}% since deposit
                </p>
            </div>
        </div>

        <!-- KPI Row 3 -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Initial Investment</p>
                <p class="text-xl font-bold text-white">${m['total_invested']:,.2f}</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Position Age</p>
                <p class="text-xl font-bold text-white">{m['position_age_days']:.1f} days</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Deposit Date</p>
                <p class="text-xl font-bold text-white">{m['deposit_date']}</p>
            </div>
            <div class="card p-5">
                <p class="text-gray-500 text-xs mb-1">Initial cbBTC Price</p>
                <p class="text-xl font-bold text-white">${m['initial_cbbtc_price']:,.0f}</p>
            </div>
        </div>

        <!-- Token Balances & Range -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="card p-5">
                <h3 class="text-sm text-gray-400 mb-4">Token Balances</h3>
                <div class="space-y-3">
                    <div class="flex justify-between items-center">
                        <span class="text-gray-300">{m['symbol0']}</span>
                        <span class="font-mono text-xl text-white">{m['amount0']:,.6f}</span>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-gray-300">{m['symbol1']}</span>
                        <span class="font-mono text-xl text-white">{m['amount1']:,.8f}</span>
                    </div>
                </div>
            </div>
            <div class="card p-5">
                <h3 class="text-sm text-gray-400 mb-4">Price Range (cbBTC/USDC)</h3>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-300">MIN</span>
                        <span class="font-mono text-cyan-400">${m['price_upper']:,.0f}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-300">MAX</span>
                        <span class="font-mono text-cyan-400">${m['price_lower']:,.0f}</span>
                    </div>
                    <div class="flex justify-between pt-2 border-t border-gray-700">
                        <span class="text-gray-300">Current Price</span>
                        <span class="font-mono {'text-green-400' if m['in_range'] else 'text-red-400'}">${m['price_current']:,.0f}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Chart -->
        <div class="card p-6 mb-6">
            <h3 class="text-sm font-semibold text-gray-300 mb-4">Value History</h3>
            <canvas id="chart-{m['nft_id']}" height="100"></canvas>
        </div>

        <!-- Projections -->
        <div class="card p-6 mb-4">
            <h3 class="text-sm font-semibold text-gray-300 mb-4">📊 Projected Yield</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div title="Return: {daily_roi:.4f}%">
                    <p class="text-gray-500 text-xs">Daily</p>
                    <p class="text-white font-mono text-lg">${m['daily_fee']:,.4f}</p>
                </div>
                <div title="Return: {weekly_roi:.4f}%">
                    <p class="text-gray-500 text-xs">Weekly</p>
                    <p class="text-white font-mono text-lg">${m['weekly_fee']:,.4f}</p>
                </div>
                <div title="Return: {monthly_roi:.2f}%">
                    <p class="text-gray-500 text-xs">Monthly</p>
                    <p class="text-white font-mono text-lg">${m['monthly_fee']:,.2f}</p>
                </div>
                <div title="Return: {yearly_roi:.2f}%">
                    <p class="text-gray-500 text-xs">Yearly</p>
                    <p class="text-white font-mono text-lg">${m['yearly_fee']:,.2f}</p>
                </div>
            </div>
        </div>
    </div>
    """

def main():
    # Load pools registry
    try:
        with open(POOLS_FILE, "r") as f:
            pools_data = json.load(f)
        pools = pools_data.get("pools", [])
    except FileNotFoundError:
        print(f"Error: {POOLS_FILE} not found.")
        return
    
    print(f"Generating dashboard for {len(pools)} pools...")
    
    # Calculate metrics for each pool
    all_metrics = []
    for pool_entry in pools:
        nft_id = pool_entry["nft_id"]
        data = load_pool_data(nft_id)
        if data:
            m = calc_metrics(pool_entry, data)
            all_metrics.append(m)
            print(f"  Pool #{nft_id}: ${m['value_usd']:,.2f} | {'In Range' if m['in_range'] else 'OUT OF RANGE'}")
    
    if not all_metrics:
        print("No pool data found!")
        return
    
    # Calculate portfolio totals
    total_value = sum(m['value_usd'] for m in all_metrics)
    total_pnl = sum(m['net_pnl'] for m in all_metrics)
    total_invested_all = sum(m['total_invested'] for m in all_metrics)
    total_fees_all = sum(m['total_fees'] for m in all_metrics)
    
    now = datetime.datetime.now()
    
    # Generate sidebar items
    sidebar_items = ""
    for i, m in enumerate(all_metrics):
        active_class = "sidebar-active" if i == 0 else ""
        status_dot = "🟢" if m['in_range'] else "🔴"
        pnl_color = "text-accent" if m['net_pnl'] >= 0 else "text-danger"
        sidebar_items += f"""
        <div class="sidebar-item {active_class}" onclick="switchPool('{m['nft_id']}', this)" data-pool="{m['nft_id']}">
            <div class="flex justify-between items-center mb-1">
                <span class="text-sm font-medium text-white">{status_dot} #{m['nft_id']}</span>
                <span class="text-xs text-gray-500">{'In Range' if m['in_range'] else 'Out'}</span>
            </div>
            <div class="text-xs text-gray-400 mb-2">{m['symbol0']}/{m['symbol1']} 0.05%</div>
            <div class="flex justify-between items-center">
                <span class="text-sm font-bold text-white">${m['value_usd']:,.2f}</span>
                <span class="text-xs {pnl_color}">{'+' if m['net_pnl'] >= 0 else ''}${m['net_pnl']:,.2f}</span>
            </div>
        </div>
        """
    
    # Generate pool content sections
    pool_sections = ""
    for i, m in enumerate(all_metrics):
        pool_sections += generate_pool_html(m, i)
    
    # Generate chart init scripts
    chart_scripts = ""
    for m in all_metrics:
        chart_scripts += f"""
        charts['{m['nft_id']}'] = new Chart(document.getElementById('chart-{m['nft_id']}'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(m['dates'])},
                datasets: [{{
                    label: 'Value USD',
                    data: {json.dumps(m['values'])},
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
        """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Pool Tracker | USDC/cbBTC</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', sans-serif; }}
        body {{ background-color: #0b0e11; color: #c9d1d9; margin: 0; }}
        .card {{ background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; }}
        .text-accent {{ color: #2ea043; }}
        .text-danger {{ color: #da3633; }}
        .text-warning {{ color: #d29922; }}
        .gradient-border {{ background: linear-gradient(135deg, #2ea043, #1f6feb); padding: 2px; border-radius: 14px; }}
        .gradient-border-inner {{ background: #161b22; border-radius: 12px; }}
        
        /* Layout */
        .app-layout {{ display: flex; min-height: 100vh; }}
        
        /* Sidebar */
        .sidebar {{
            width: 280px;
            min-width: 280px;
            background: #0d1117;
            border-right: 1px solid #21262d;
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }}
        .sidebar-header {{
            padding: 8px 12px;
            margin-bottom: 8px;
        }}
        .sidebar-item {{
            padding: 12px 14px;
            border-radius: 10px;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s ease;
        }}
        .sidebar-item:hover {{
            background: #161b22;
            border-color: #30363d;
        }}
        .sidebar-active {{
            background: #161b22 !important;
            border-color: #1f6feb !important;
            box-shadow: 0 0 0 1px rgba(31, 111, 235, 0.3);
        }}
        .sidebar-divider {{
            height: 1px;
            background: #21262d;
            margin: 12px 0;
        }}
        .sidebar-portfolio {{
            background: linear-gradient(135deg, rgba(31, 111, 235, 0.1), rgba(46, 160, 67, 0.1));
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 14px;
        }}
        
        /* Main Content */
        .main-content {{
            flex: 1;
            padding: 24px 32px;
            max-width: 1200px;
        }}
        
        @media (max-width: 768px) {{
            .app-layout {{ flex-direction: column; }}
            .sidebar {{ width: 100%; min-width: 100%; height: auto; position: relative; flex-direction: row; overflow-x: auto; }}
            .sidebar-item {{ min-width: 200px; }}
            .main-content {{ padding: 16px; }}
        }}
    </style>
</head>
<body>
    <div class="app-layout">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <h1 class="text-lg font-bold text-white">📊 Pool Tracker</h1>
                <p class="text-xs text-gray-500 mt-1">{now.strftime("%Y-%m-%d %H:%M")}</p>
            </div>
            
            <!-- Portfolio Summary -->
            <div class="sidebar-portfolio">
                <p class="text-xs text-gray-400 mb-1">Portfolio Total</p>
                <p class="text-xl font-bold text-white">${total_value:,.2f}</p>
                <div class="flex justify-between mt-2">
                    <div>
                        <p class="text-xs text-gray-500">PnL</p>
                        <p class="text-sm font-medium {'text-accent' if total_pnl >= 0 else 'text-danger'}">{'+' if total_pnl >= 0 else ''}${total_pnl:,.2f}</p>
                    </div>
                    <div>
                        <p class="text-xs text-gray-500">Fees</p>
                        <p class="text-sm font-medium text-yellow-400">${total_fees_all:,.2f}</p>
                    </div>
                </div>
            </div>
            
            <div class="sidebar-divider"></div>
            <p class="text-xs text-gray-500 px-2 mb-1">POSITIONS ({len(all_metrics)})</p>
            
            <!-- Pool Items -->
            {sidebar_items}
            
            <div class="sidebar-divider"></div>
            
            <!-- Sync Button -->
            <button id="syncBtn" onclick="syncData()" class="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition flex items-center justify-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync All Pools
            </button>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            {pool_sections}
        </div>
    </div>

    <script>
        const charts = {{}};
        
        function switchPool(nftId, element) {{
            // Hide all pool content
            document.querySelectorAll('.pool-content').forEach(el => el.style.display = 'none');
            // Show selected pool
            document.getElementById('pool-' + nftId).style.display = 'block';
            
            // Update sidebar active state
            document.querySelectorAll('.sidebar-item').forEach(el => el.classList.remove('sidebar-active'));
            element.classList.add('sidebar-active');
            
            // Resize chart (needed after display change)
            if (charts[nftId]) {{
                setTimeout(() => charts[nftId].resize(), 50);
            }}
        }}

        async function syncData() {{
            const btn = document.getElementById('syncBtn');
            const isVercel = !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1');
            
            if (isVercel) {{
                alert('Sync só funciona localmente.\\nPara atualizar no Vercel:\\n1. python tools/sync.py\\n2. git push');
                return;
            }}
            
            btn.innerHTML = 'Syncing...';
            btn.disabled = true;
            btn.classList.add('opacity-75');

            try {{
                const response = await fetch('/api/sync', {{ method: 'POST' }});
                const data = await response.json();
                if (data.success) {{
                    alert('Sync complete!');
                    window.location.reload();
                }} else {{
                    alert('Error: ' + data.message);
                }}
            }} catch (error) {{
                alert('Connection failed. Make sure server.py is running.');
            }}
            btn.innerHTML = 'Sync All Pools';
            btn.disabled = false;
            btn.classList.remove('opacity-75');
        }}

        // Initialize charts
        {chart_scripts}
    </script>
</body>
</html>
    """
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nDashboard generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
