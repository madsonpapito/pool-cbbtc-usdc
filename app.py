import streamlit as st
import pandas as pd
import json
import datetime
import math
import plotly.graph_objects as go
from tools.fetch_pool_data import fetch_data
from tools.fetch_collected_fees import fetch_fees

# Page Config
st.set_page_config(
    page_title="Liquidity Pool Tracker | USDC/cbBTC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
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
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .card-value {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        font-family: 'SF Mono', 'Segoe UI Mono', 'Roboto Mono', monospace;
    }

    .card-sub {
        font-size: 0.8rem;
        margin-top: 0.2rem;
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .text-green { color: #2ea043 !important; }
    .text-red { color: #da3633 !important; }
    .text-gray { color: #8b949e !important; }
    .text-blue { color: #58a6ff !important; }
    
    .bg-badge {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        border: 1px solid rgba(56, 139, 253, 0.4);
    }
    
    /* Tooltip container */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted #8b949e; 
        cursor: help;
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #1f2428;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
        border: 1px solid #30363d;
        font-size: 0.75rem;
        font-weight: normal;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    /* Button Styling */
    .stButton button {
        background-color: #238636;
        color: white;
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #2ea043;
        border-color: rgba(240, 246, 252, 0.1);
    }

</style>
""", unsafe_allow_html=True)

# Helper Functions
def calculate_impermanent_loss(current_price, entry_price):
    if entry_price <= 0: return 0
    price_ratio = current_price / entry_price
    if price_ratio <= 0: return 0
    sqrt_ratio = math.sqrt(price_ratio)
    # IL = (2 * sqrt(P) / (1 + P)) - 1
    il = (2 * sqrt_ratio / (1 + price_ratio)) - 1
    return il * 100

def calculate_fee_apr(total_fees, position_value, days_active):
    if position_value <= 0 or days_active <= 0: return 0
    daily_rate = (total_fees / position_value) / days_active
    apr = daily_rate * 365 * 100
    return apr

@st.cache_data(ttl=600)
def load_data():
    try:
        with open("tools/config.json", "r") as f: config = json.load(f)
    except: config = {}
    
    try:
        with open("tools/history.json", "r") as f: history = json.load(f)
    except: history = []

    try:
        with open("tools/position_data.json", "r") as f: pos = json.load(f)
        with open("tools/fees_data.json", "r") as f: fees = json.load(f)
    except:
        pos = {}
        fees = {}
        
    return config, history, pos, fees

def sync_data():
    with st.spinner("Syncing data from blockchain..."):
        pos_data = fetch_data()
        fees_data = fetch_fees()
        if pos_data:
            try:
                with open("tools/history.json", "r") as f: history = json.load(f)
            except: history = []
            
            # Use safe defaults if keys missing
            val_usd = pos_data.get('value_usd', 0)
            fees_usd = pos_data.get('fees_usd', 0)
            price_c = pos_data.get('price_cbbtc', 0)

            snapshot = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "value_usd": val_usd,
                "fees_usd": fees_usd,
                "price_cbbtc": price_c
            }
            history.append(snapshot)
            with open("tools/history.json", "w") as f: json.dump(history, f, indent=2)
            st.cache_data.clear()
            st.rerun()

# --- Custom Card Component ---
def metric_card(title, value, sub_value=None, sub_color="green", tooltip=None):
    sub_html = ""
    if sub_value:
        color_class = f"text-{sub_color}"
        sub_html = f'<div class="card-sub {color_class}">{sub_value}</div>'
    
    # HTML tooltip if provided
    tooltip_html = ""
    if tooltip:
        tooltip_html = f"""<div class="tooltip">ℹ️<span class="tooltiptext">{tooltip}</span></div>"""
        
    st.markdown(f"""
<div class="dashboard-card">
<div style="display: flex; justify-content: space-between; align-items: start;">
<div class="card-title">{title}</div>
{tooltip_html}
</div>
<div class="card-value">{value}</div>
{sub_html}
</div>
""", unsafe_allow_html=True)

# Main App
def main():
    config, history, pos, fees_data = load_data()
    
    if not pos:
        st.warning("No data found. Click 'Sync Data'.")
        if st.button("Sync Data"): sync_data()
        return

    # --- Data Extraction ---
    symbol0, symbol1 = pos.get('symbol0', 'USDC'), pos.get('symbol1', 'cbBTC')
    amount0, amount1 = pos.get('amount0', 0), pos.get('amount1', 0)
    value_usd = pos.get('value_usd', 0)
    price_cbbtc = pos.get('price_cbbtc', 0)
    price_lower, price_upper = pos.get('price_lower', 0), pos.get('price_upper', 0)
    in_range = pos.get('in_range', False)
    liquidity = pos.get('liquidity', 0)
    
    unclaimed_0 = pos.get('unclaimed_0', 0) / 1e6
    unclaimed_1 = pos.get('unclaimed_1', 0) / 1e8
    
    collected_usdc = fees_data.get('total_collected_usdc', 0)
    collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
    
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    fees_pending_value = (unclaimed_0 * 1.0) + (unclaimed_1 * price_cbbtc)
    total_fees = fees_pending_value + fees_collected_value
    
    total_invested = config.get("total_invested_usd", 118.65)
    initial_price = config.get("initial_cbbtc_price", 88685)
    deposit_date_str = config.get("deposit_date", "2025-11-24")
    # FIX: Default to None to ensure fallback to string date if key missing
    deposit_ts = config.get("deposit_timestamp", None) 
    
    # Precise days active
    try:
        if deposit_ts:
            start_dt = datetime.datetime.fromtimestamp(deposit_ts)
        else:
            # Parse string date
            start_dt = datetime.datetime.strptime(deposit_date_str, "%Y-%m-%d")
        
        diff = datetime.datetime.now() - start_dt
        days_active = diff.total_seconds() / 86400
    except:
        days_active = 1
    
    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    fee_apr = calculate_fee_apr(total_fees, total_invested, days_active)
    total_apr = (roi_percent / days_active) * 365 if days_active > 0 else 0
    
    # IL and HODL
    initial_btc = (total_invested * 0.5) / initial_price
    initial_usdc = total_invested * 0.5
    hodl_value = (initial_btc * price_cbbtc) + initial_usdc
    
    # Divergence Loss (Value vs HODL excluding fees)
    divergence_loss = value_usd - hodl_value
    il_percent = (divergence_loss / hodl_value) * 100 if hodl_value > 0 else 0
    
    # LP vs HODL (Total Advantage)
    lp_vs_hodl = (value_usd + total_fees) - hodl_value

    # --- Header Section ---
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"""
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #2775ca, #8c4eee);"></div>
<h1 style="margin: 0; font-size: 1.5rem;">{symbol0} / <span style="color: #2ea043;">{symbol1}</span></h1>
<span class="bg-badge">Uniswap V3</span>
</div>
<p style="color: #8b949e; margin-top: 5px; font-size: 0.9rem;">Targeting {price_upper:,.0f} - {price_lower:,.0f} {symbol0}/{symbol1}</p>
""", unsafe_allow_html=True)
    with c2:
        status_color = "#2ea043" if in_range else "#da3633"
        status_text = "IN RANGE" if in_range else "OUT OF RANGE"
        st.markdown(f"""
<div style="text-align: right; margin-bottom: 10px;">
<span style="color: {status_color}; font-weight: bold; font-family: monospace; border: 1px solid {status_color}; padding: 4px 8px; border-radius: 4px;">● {status_text}</span>
</div>
""", unsafe_allow_html=True)
        if st.button("🔄 Sync Data", use_container_width=True):
            sync_data()

    st.markdown("---")

    # =========================================================================
    # ROW 1: Key Metrics
    # Pooled Assets, Total PnL, Fee APR, Total APR
    # =========================================================================
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        metric_card("Pooled Assets", f"${value_usd:,.2f}", f"{days_active:.1f} Days Active", "gray")
    with r1c2:
        pnl_color = "green" if net_pnl >= 0 else "red"
        metric_card("Total PnL", f"${net_pnl:,.2f}", f"{roi_percent:+.2f}% ROI", pnl_color)
    with r1c3:
        metric_card("Fee APR (Fee Only)", f"{fee_apr:.2f}%", "Lifetime Avg", "blue")
    with r1c4:
        metric_card("Total APR (Incl. Price)", f"{total_apr:.2f}%", f"ROI annualized", "green")

    # =========================================================================
    # ROW 2: Detailed Performance
    # ROI, Impermanent Loss, Total Fees Earned, LP vs HODL
    # =========================================================================
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        metric_card("ROI", f"{roi_percent:+.2f}%", f"${net_pnl:+.2f}", "green" if roi_percent>=0 else "red")
    with r2c2:
        metric_card("Impermanent Loss", f"{il_percent:.2f}%", f"${divergence_loss:.2f} USD", "red")
    with r2c3:
        # Tooltip for fees breakdown
        fees_tooltip = f"Collected: ${fees_collected_value:,.2f} | Pending: ${fees_pending_value:,.2f}"
        metric_card("Total Fees Earned", f"${total_fees:,.2f}", "Collected + Pending", "green", tooltip=fees_tooltip)
    with r2c4:
        color_lphp = "green" if lp_vs_hodl >= 0 else "red"
        metric_card("LP vs HODL", f"${lp_vs_hodl:+.2f}", "Advantage", color_lphp)

    # =========================================================================
    # ROW 3: Market & Position Info
    # cbBTC Price, Initial Investment, Position Age, Deposit Date
    # =========================================================================
    r3c1, r3c2, r3c3, r3c4 = st.columns(4)
    with r3c1:
        metric_card("cbBTC Price", f"${price_cbbtc:,.0f}", "Current Market", "blue")
    with r3c2:
        metric_card("Initial Investment", f"${total_invested:,.2f}", "Principal", "gray")
    with r3c3:
        metric_card("Position Age", f"{days_active:.1f} Days", f"Since {deposit_date_str}", "gray")
    with r3c4:
        metric_card("Deposit Date", deposit_date_str, "Start Date", "gray")

    # =========================================================================
    # ROW 4: Extra Details / Tokens
    # Initial cbBTC Price, Token Balances, Price Range
    # =========================================================================
    r4c1, r4c2, r4c3 = st.columns([1, 1, 2])
    with r4c1:
        metric_card("Initial cbBTC Price", f"${initial_price:,.0f}", "Avg Entry", "gray")
    with r4c2:
        # Token Balances
        balance_str = f"{amount0:.2f} USDC<br>{amount1:.5f} cbBTC"
        st.markdown(f"""
<div class="dashboard-card">
<div class="card-title">Token Balances</div>
<div class="card-value" style="font-size: 1.1rem; line-height: 1.5;">{amount0:,.2f} <span style="font-size: 0.8em; color: #8b949e;">USDC</span></div>
<div class="card-value" style="font-size: 1.1rem; line-height: 1.5;">{amount1:,.5f} <span style="font-size: 0.8em; color: #8b949e;">cbBTC</span></div>
</div>
""", unsafe_allow_html=True)
    with r4c3:
        # Price Range visual
        st.markdown(f"""
<div class="dashboard-card">
<div class="card-title">Price Range</div>
<div style="display: flex; justify-content: space-between; margin-top: 10px;">
<div style="text-align: left;">
<div style="color: #8b949e; font-size: 0.8rem;">Min Price</div>
<div style="font-family: monospace; font-size: 1.2rem;">{price_upper:,.0f}</div>
</div>
<div style="align-self: center; font-weight: bold; color: #58a6ff;">⟷</div>
<div style="text-align: right;">
<div style="color: #8b949e; font-size: 0.8rem;">Max Price</div>
<div style="font-family: monospace; font-size: 1.2rem;">{price_lower:,.0f}</div>
</div>
</div>
<div style="margin-top: 10px; background: #30363d; height: 6px; border-radius: 3px; position: relative;">
<!-- Marker for current price could go here if normalized -->
</div>
</div>
""", unsafe_allow_html=True)

    # =========================================================================
    # ROW 5: Chart
    # =========================================================================
    st.markdown("### Value History")
    if history:
        df = pd.DataFrame(history)
        df['date'] = pd.to_datetime(df['date'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['value_usd'],
            mode='lines',
            name='Value',
            line=dict(color='#2ea043', width=2),
            fill='tozeroy',
            fillcolor='rgba(46, 160, 67, 0.1)'
        ))
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#8b949e')),
            yaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False, tickfont=dict(color='#8b949e')),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No history data available.")

    # =========================================================================
    # ROW 6: Performance Summary (Yield Projections)
    # =========================================================================
    avg_daily = total_fees / days_active if days_active > 0 else 0
    projections = {
        "Daily": avg_daily,
        "Weekly": avg_daily * 7,
        "Monthly": avg_daily * 30,
        "Yearly": avg_daily * 365
    }

    st.markdown("### Performance Summary (Projected Yield)")
    c_proj = st.columns(4)
    periods = ["Daily", "Weekly", "Monthly", "Yearly"]
    
    for i, period in enumerate(periods):
        val = projections[period]
        # Calculate percent of total investment
        pct = (val / total_invested * 100) if total_invested > 0 else 0
        
        # Tooltip with %
        tooltip_txt = f"{pct:.2f}% of Initial Investment"
        
        with c_proj[i]:
            # Custom card for this
            st.markdown(f"""
<div class="dashboard-card tooltip" style="text-align: center;">
<div class="card-title">{period}</div>
<div style="color: #2ea043; font-size: 1.4rem; font-weight: bold; margin-top: 5px;">${val:,.2f}</div>
<span class="tooltiptext">{tooltip_txt}</span>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
