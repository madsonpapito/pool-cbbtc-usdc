import streamlit as st
import pandas as pd
import json
import datetime
import math
import os
import plotly.graph_objects as go
from tools.fetch_pool_data import fetch_data
from tools.fetch_collected_fees import fetch_fees

# Page Config
st.set_page_config(
    page_title="Liquidity Pool Tracker | USDC/cbBTC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Dark Theme
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Custom Cards */
    .dashboard-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 1rem;
        height: 100%;
        transition: transform 0.2s;
    }
    
    .dashboard-card:hover {
        border-color: #8b949e;
    }
    
    .card-title {
        color: #8b949e;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    
    .card-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e6edf3;
    }
    
    .card-sub {
        font-size: 0.8rem;
        color: #8b949e;
        margin-top: 0.5rem;
    }
    
    .positive { color: #3fb950; }
    .negative { color: #f85149; }
    
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# AUTO-RELOAD LOGIC (REMOVED - Not needed for stable version)
# ---------------------------------------------------------

# ---------------------------------------------------------
# MULTI-POOL LOGIC & SIDEBAR
# ---------------------------------------------------------

def load_pools_registry():
    try:
        with open("tools/pools.json", "r") as f:
            return json.load(f)
    except:
        # Fallback if registry missing
        return [{"nft_id": 4227642, "symbol": "USDC/cbBTC (Main)"}]

def get_pool_paths(nft_id):
    """Return paths for the specific pool ID"""
    base_dir = f"data/pools/{nft_id}"
    os.makedirs(base_dir, exist_ok=True)
    return {
        "config": f"{base_dir}/config.json",
        "position": f"{base_dir}/position_data.json",
        "fees": f"{base_dir}/fees_data.json",
        "history": f"{base_dir}/history.json"
    }

# SIDEBAR
st.sidebar.title("🥝 Liquidity Manager")

pools = load_pools_registry()
pool_options = {p['nft_id']: f"{p['symbol']} (#{p['nft_id']})" for p in pools}

# Session State for Selection
if 'selected_pool_id' not in st.session_state:
    st.session_state.selected_pool_id = pools[0]['nft_id']

selected_id = st.sidebar.selectbox(
    "Select Pool",
    options=list(pool_options.keys()),
    format_func=lambda x: pool_options[x],
    index=0
)

# Update session state if changed
if selected_id != st.session_state.selected_pool_id:
    st.session_state.selected_pool_id = selected_id
    # Force reload of data
    st.cache_data.clear()
    st.rerun()

current_nft_id = st.session_state.selected_pool_id
paths = get_pool_paths(current_nft_id)

st.sidebar.markdown("---")
st.sidebar.info(f"Viewing Data for Pool #{current_nft_id}")

# ---------------------------------------------------------
# DATA LOADING (Dynamic)
# ---------------------------------------------------------

@st.cache_data(ttl=60)
def load_data(pool_id):
    p = get_pool_paths(pool_id)
    
    # Load Config
    try:
        with open(p['config'], "r") as f: config = json.load(f)
    except: 
        # Attempt to load from tools/config.json if it matches ID (Migration fallback)
        try:
             with open("tools/config.json", "r") as f: 
                 base_conf = json.load(f)
                 if str(base_conf.get('nft_id')) == str(pool_id):
                     config = base_conf
                 else:
                     raise Exception
        except:
            config = {"nft_id": pool_id, "total_invested_usd": 0}

    # Load History
    try:
        with open(p['history'], "r") as f: history = json.load(f)
    except: 
        try:
             with open("tools/history.json", "r") as f: history = json.load(f) if str(config.get('nft_id')) == str(pool_id) else []
        except: history = []

    # Load Position
    try:
        with open(p['position'], "r") as f: pos = json.load(f)
    except: 
        try:
             with open("tools/position_data.json", "r") as f: pos = json.load(f)
        except: pos = {}

    # Load Fees
    try:
        with open(p['fees'], "r") as f: fees = json.load(f)
    except: 
        try:
             with open("tools/fees_data.json", "r") as f: fees = json.load(f)
        except: fees = {}
        
    return config, history, pos, fees

def sync_data(pool_id):
    p = get_pool_paths(pool_id)
    with st.spinner(f"Syncing Pool #{pool_id}..."):
        # Fetch NEW data
        pos_data = fetch_data(pool_id)
        fees_data_result = fetch_fees(pool_id, previous_data_path=p['fees'])
        
        if pos_data:
            with open(p['position'], "w") as f:
                json.dump(pos_data, f, indent=2)
            
            # Also update legacy tool/position_data.json if this is the DEFAULT pool
            # This keeps other scripts working if they look there
            if str(pool_id) == "4227642":
                with open("tools/position_data.json", "w") as f: json.dump(pos_data, f, indent=2)

        if fees_data_result:
            with open(p['fees'], "w") as f:
                json.dump(fees_data_result, f, indent=2)
                
            if str(pool_id) == "4227642":
                with open("tools/fees_data.json", "w") as f: json.dump(fees_data_result, f, indent=2)


        # History Snapshot
        try:
            with open(p['history'], "r") as f: history = json.load(f)
        except: history = []
        
        # Add snapshot logic here if needed (omitted for brevity, utilizing existing logic)
        # For now, we assume history is appended elsewhere or we replicate the logic:
        if pos_data:
            snapshot = {
                "timestamp": datetime.datetime.now().isoformat(),
                "value_usd": pos_data.get("value_usd", 0),
                "price_cbbtc": pos_data.get("price_cbbtc", 0)
            }
            history.append(snapshot)
            # Limit history
            if len(history) > 500: history = history[-500:]
            
            with open(p['history'], "w") as f: json.dump(history, f, indent=2)
            if str(pool_id) == "4227642":
                with open("tools/history.json", "w") as f: json.dump(history, f, indent=2)
                
    st.cache_data.clear()
    st.rerun()


# Load Data
config, history, pos, fees_data = load_data(current_nft_id)


# ---------------------------
# DASHBOARD LAYOUT
# ---------------------------

# Header
col_header_1, col_header_2 = st.columns([3, 1])

with col_header_1:
    st.title("🥝 Liquidity Manager v2.1")
    # Dynamic Title
    pool_info = next((p for p in pools if p['nft_id'] == current_nft_id), None)
    symbol = pool_info['symbol'] if pool_info else "Unknown"
    st.markdown(f"**Pool:** {symbol} | **NFT ID:** #{current_nft_id}")
    
with col_header_2:
    if st.button("🔄 Sync Data", use_container_width=True):
        sync_data(current_nft_id)

st.markdown("---")

if not pos:
    st.info("No data available. Please click Sync Data.")
else:
    # ---------------------------
    # METRIC CALCULATIONS
    # ---------------------------
    
    # 1. Invested & PnL
    total_assets_usd = pos.get("value_usd", 0)
    initial_invested = config.get("total_invested_usd", 318.65)
    
    # Fees Collected (USDC + cbBTC value)
    collected_usdc = fees_data.get("total_collected_usdc", 0)
    collected_cbbtc = fees_data.get("total_collected_cbbtc", 0)
    current_cbbtc_price = pos.get("price_cbbtc", 0)
    
    fees_collected_value = collected_usdc + (collected_cbbtc * current_cbbtc_price)
    
    unclaimed_fees_usd = pos.get("fees_usd", 0)
    total_fees_earned = fees_collected_value + unclaimed_fees_usd
    
    total_pnl = (total_assets_usd + fees_collected_value) - initial_invested
    roi_pct = (total_pnl / initial_invested) * 100 if initial_invested > 0 else 0
    
    # 2. APR Calculation
    # Days since deposit
    deposit_date_str = config.get("deposit_date", "2025-11-24")
    try:
        deposit_date = datetime.datetime.strptime(deposit_date_str, "%Y-%m-%d")
    except:
        deposit_date = datetime.datetime.now() # Fallback

    days_active = (datetime.datetime.now() - deposit_date).days
    if days_active < 1: days_active = 1
    
    fee_apr = (total_fees_earned / initial_invested) * (365 / days_active) * 100 if initial_invested > 0 else 0
    
    # Total APR (incl IL/Price action) => Just annualized ROI
    total_apr = roi_pct * (365 / days_active)

    # 3. Impermanent Loss (Approximate)
    # IL Formula based on price ratio
    initial_price = config.get("initial_cbbtc_price", 0)
    if initial_price > 0:
        price_ratio = current_cbbtc_price / initial_price
        sqrt_ratio = math.sqrt(price_ratio)
        il_pct = (2 * sqrt_ratio / (1 + price_ratio) - 1) * 100
    else:
        il_pct = 0

    # HODL Value (Assuming 50/50 split at deposit)
    # If we had exact initial amounts, we should store them in config.json
    # For now, derive from total_invested and initial price
    initial_usdc_est = initial_invested * 0.5
    initial_btc_est = (initial_invested * 0.5) / initial_price if initial_price > 0 else 0
    
    hodl_value = initial_usdc_est + (initial_btc_est * current_cbbtc_price)
    
    # IL Value in USD (Position Value - HODL Value)
    impermanent_loss = total_assets_usd - hodl_value


    # ---------------------------
    # CARD GENERATOR
    # ---------------------------
    # ---------------------------
    # CARD GENERATOR
    # ---------------------------
    def card(title, value, sub=None, positive=None, tooltip=None):
        color_class = "positive" if positive is True else "negative" if positive is False else ""
        sub_html = f"<div class='card-sub {color_class}'>{sub}</div>" if sub else ""
        title_attr = f"title='{tooltip}'" if tooltip else ""
        return f"""
        <div class="dashboard-card" {title_attr}>
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
            {sub_html}
        </div>
        """

    # ROW 1: MAIN STATS
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(card("Pooled Assets", f"${total_assets_usd:,.2f}", f"{days_active:.1f} Days Active"), unsafe_allow_html=True)
    with c2: st.markdown(card("Total PnL", f"${total_pnl:,.2f}", f"{roi_pct:+.2f}% ROI", positive=roi_pct>0), unsafe_allow_html=True)
    with c3: st.markdown(card("Fee APR (Fee Only)", f"{fee_apr:.2f}%", "Lifetime Avg", positive=True), unsafe_allow_html=True)
    with c4: st.markdown(card("Total APR (Incl. Price)", f"{total_apr:.2f}%", "ROI Annualized", positive=total_apr>0), unsafe_allow_html=True)

    # ROW 2: STRATEGY PERFORMANCE
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(card("ROI", f"{roi_pct:+.2f}%", f"${total_pnl:,.2f}"), unsafe_allow_html=True)
    with c2: st.markdown(card("Impermanent Loss", f"{il_pct:.2f}%", f"${impermanent_loss:.2f} USD", positive=False), unsafe_allow_html=True)
    with c3: st.markdown(card("Total Fees Earned", f"${total_fees_earned:,.2f}", "Collected + Pending", positive=True), unsafe_allow_html=True)
    with c4: st.markdown(card("LP vs HODL", f"${impermanent_loss + fees_collected_value:,.2f}", "Advantage", positive=(impermanent_loss + fees_collected_value)>0), unsafe_allow_html=True)

    # ROW 3: PRICE DETAILS
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(card("cbBTC Price", f"${current_cbbtc_price:,.0f}", "Current Market"), unsafe_allow_html=True)
    with c2: st.markdown(card("Initial Investment", f"${initial_invested:,.2f}", "Principal"), unsafe_allow_html=True)
    with c3: st.markdown(card("Position Age", f"{days_active:.1f} Days", f"Since {deposit_date_str}"), unsafe_allow_html=True)
    with c4: st.markdown(card("Deposit Date", f"{deposit_date_str}", "Start Date"), unsafe_allow_html=True)
    
    # ROW 4: RANGE & INFO
    c1, c2, c3, c4 = st.columns(4)
    min_price = pos.get("price_lower", 0)
    max_price = pos.get("price_upper", 0)
    in_range = pos.get("in_range", False)
    range_emoji = "🟢" if in_range else "🔴"
    
    # Token Balances Display
    sym0 = pos.get("symbol0", "USDC")
    amt0 = pos.get("amount0", 0)
    sym1 = pos.get("symbol1", "cbBTC")
    amt1 = pos.get("amount1", 0)
    
    if sym0 == "USDC":
         balance_str = f"{amt0:.2f} USDC\n{amt1:.5f} cbBTC"
    else:
         balance_str = f"{amt0:.5f} cbBTC\n{amt1:.2f} USDC"
    
    # Improve Max Price formatting
    max_p_display = f"{max_price:,.0f}" if max_price < 1e9 else "∞"
    
    with c1: st.markdown(card("Initial cbBTC Price", f"${config.get('initial_cbbtc_price', 0):,.0f}", "Avg Entry"), unsafe_allow_html=True)
    with c2: st.markdown(card("Token Balances", balance_str, "In Pool"), unsafe_allow_html=True)
    with c3: st.markdown(card("Price Range", f"{min_price:,.0f}", f"Min Price"), unsafe_allow_html=True)
    with c4: st.markdown(card(f"{range_emoji} Range Status", max_p_display, "Max Price"), unsafe_allow_html=True)


    # ---------------------------
    # PERFORMANCE SUMMARY
    # ---------------------------
    st.markdown("---")
    st.markdown("### 📊 Performance Summary")
    
    # Projections
    daily_fee = total_fees_earned / max(days_active, 1)
    weekly_fee = daily_fee * 7
    monthly_fee = daily_fee * 30
    yearly_fee = daily_fee * 365
    
    # ROI Calcs
    daily_roi = (daily_fee / initial_invested) * 100 if initial_invested > 0 else 0
    weekly_roi = (weekly_fee / initial_invested) * 100 if initial_invested > 0 else 0
    monthly_roi = (monthly_fee / initial_invested) * 100 if initial_invested > 0 else 0
    yearly_roi = (yearly_fee / initial_invested) * 100 if initial_invested > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(card("Daily Fee Income", f"${daily_fee:,.2f}", "Est. Daily Fee", tooltip=f"Return: {daily_roi:.4f}% of Invested"), unsafe_allow_html=True)
    with c2: st.markdown(card("Weekly Fee Income", f"${weekly_fee:,.2f}", "Est. Weekly Fee", tooltip=f"Return: {weekly_roi:.4f}% of Invested"), unsafe_allow_html=True)
    with c3: st.markdown(card("Monthly Fee", f"${monthly_fee:,.2f}", "Est. Monthly", tooltip=f"Return: {monthly_roi:.2f}% of Invested"), unsafe_allow_html=True)
    with c4: st.markdown(card("Yearly Fee", f"${yearly_fee:,.2f}", "Est. Yearly", tooltip=f"Return: {yearly_roi:.2f}% of Invested"), unsafe_allow_html=True)


    # CHART
    st.markdown("---")
    if history:
        df = pd.DataFrame(history)
        # Use 'date' instead of 'timestamp' if 'timestamp' is unreliable/missing
        if 'date' in df.columns:
             df['ts_chart'] = pd.to_datetime(df['date'])
        else:
             df['ts_chart'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['ts_chart'], y=df['value_usd'], mode='lines', name='Value', line=dict(color='#238636', width=2)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#8b949e'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#21262d')
        )
        st.plotly_chart(fig, use_container_width=True)
