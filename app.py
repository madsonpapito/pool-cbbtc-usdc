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
        font-size: 1.8rem;
        font-weight: 700;
        font-family: 'SF Mono', 'Segoe UI Mono', 'Roboto Mono', monospace;
    }

    .card-sub {
        font-size: 0.8rem;
        margin-top: 0.2rem;
    }

    .text-green { color: #2ea043 !important; }
    .text-red { color: #da3633 !important; }
    .text-gray { color: #8b949e !important; }
    .bg-badge {
        background-color: rgba(56, 139, 253, 0.15);
        color: #58a6ff;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        border: 1px solid rgba(56, 139, 253, 0.4);
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
    
    /* Plotly Chart Container */
    .chart-container {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1rem;
    }

</style>
""", unsafe_allow_html=True)

# Helper Functions
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
            snapshot = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "value_usd": pos_data['value_usd'],
                "fees_usd": pos_data['fees_usd'],
                "price_cbbtc": pos_data['price_cbbtc']
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
    
    tooltip_attr = f'title="{tooltip}"' if tooltip else ""
    
    st.markdown(f"""
    <div class="dashboard-card" {tooltip_attr}>
        <div class="card-title">{title}</div>
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

    # Data Processing
    symbol0, symbol1 = pos.get('symbol0', 'USDC'), pos.get('symbol1', 'cbBTC')
    amount0, amount1 = pos.get('amount0', 0), pos.get('amount1', 0)
    value_usd = pos.get('value_usd', 0)
    price_cbbtc = pos.get('price_cbbtc', 0)
    price_lower, price_upper = pos.get('price_lower', 0), pos.get('price_upper', 0)
    in_range = pos.get('in_range', False)
    
    unclaimed_0 = pos.get('unclaimed_0', 0) / 1e6
    unclaimed_1 = pos.get('unclaimed_1', 0) / 1e8
    collected_usdc = fees_data.get('total_collected_usdc', 0)
    collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
    
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    fees_pending_value = (unclaimed_0 * 1.0) + (unclaimed_1 * price_cbbtc)
    total_fees = fees_pending_value + fees_collected_value
    
    total_invested = config.get("total_invested_usd", 119.16)
    initial_price = config.get("initial_cbbtc_price", 88685)
    deposit_date_str = config.get("deposit_date", "2025-11-24")
    
    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    deposit_dt = datetime.datetime.strptime(deposit_date_str, "%Y-%m-%d")
    days_active = (datetime.datetime.now() - deposit_dt).days + 1
    
    fee_apr = calculate_fee_apr(total_fees, total_invested, days_active)
    total_apr = (roi_percent / days_active) * 365 if days_active > 0 else 0
    
    initial_btc = (total_invested * 0.5) / initial_price
    initial_usdc = total_invested * 0.5
    hodl_value = (initial_btc * price_cbbtc) + initial_usdc
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
        <p style="color: #8b949e; margin-top: 5px; font-size: 0.9rem;">Targeting {price_lower:,.0f} - {price_upper:,.0f} {symbol0}/{symbol1}</p>
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

    # --- KPI Grid ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Pooled Value", f"${value_usd:,.2f}", f"{days_active} Days Active", "gray")
    with col2:
        pnl_color = "green" if net_pnl >= 0 else "red"
        metric_card("Net PnL", f"${net_pnl:,.2f}", f"{roi_percent:+.2f}% ROI", pnl_color)
    with col3:
        metric_card("Total APR", f"{total_apr:.1f}%", f"Fee APR: {fee_apr:.1f}%", "green")
    with col4:
        metric_card("Total Fees", f"${total_fees:,.2f}", f"Pending: ${fees_pending_value:,.2f}", "green", 
                    f"Collected: ${fees_collected_value:,.2f}")

    # --- Main Content: Chart & Details ---
    row2_col1, row2_col2 = st.columns([2, 1])
    
    with row2_col1:
        st.markdown('<div class="dashboard-card" style="height: 400px; padding: 10px;">', unsafe_allow_html=True)
        st.markdown('<div class="card-title" style="padding-left: 10px;">Performance Curve</div>', unsafe_allow_html=True)
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            # Gradient fill area
            fig.add_trace(go.Scatter(
                x=df['date'], y=df['value_usd'],
                mode='lines',
                name='Value',
                line=dict(color='#2ea043', width=2),
                fill='tozeroy',
                fillcolor='rgba(46, 160, 67, 0.1)'
            ))
            
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=350,
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#8b949e')),
                yaxis=dict(showgrid=True, gridcolor='#30363d', zeroline=False, tickfont=dict(color='#8b949e')),
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No history data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col2:
        # Asset Breakdown Card
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="card-title">Asset Breakdown</div>
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #8b949e;">{symbol0}</span>
                    <span style="font-family: monospace;">{amount0:,.2f}</span>
                </div>
                <div style="height: 4px; background: #30363d; border-radius: 2px; overflow: hidden; margin-bottom: 15px;">
                    <div style="width: 50%; height: 100%; background: #2775ca;"></div>
                </div>
                
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #8b949e;">{symbol1}</span>
                    <span style="font-family: monospace;">{amount1:,.6f}</span>
                </div>
                <div style="height: 4px; background: #30363d; border-radius: 2px; overflow: hidden; margin-bottom: 15px;">
                    <div style="width: 50%; height: 100%; background: #8c4eee;"></div>
                </div>
            </div>
            
            <div style="border-top: 1px solid #30363d; margin: 15px 0; padding-top: 15px;">
                 <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #8b949e; font-size: 0.8rem;">LP vs HODL</span>
                    <span style="color: {'#2ea043' if lp_vs_hodl >= 0 else '#da3633'}; font-family: monospace;">${lp_vs_hodl:+.2f}</span>
                </div>
                 <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8b949e; font-size: 0.8rem;">Current Price</span>
                    <span style="font-family: monospace;">${price_cbbtc:,.0f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- Yield Projections ---
    avg_daily = total_fees / days_active if days_active > 0 else 0
    projections = {
        "Daily": avg_daily,
        "Weekly": avg_daily * 7,
        "Monthly": avg_daily * 30
    }
    
    st.markdown("### Yield Projections")
    p1, p2, p3 = st.columns(3)
    cols = [p1, p2, p3]
    for i, (period, val) in enumerate(projections.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; text-align: center;">
                <div style="color: #8b949e; font-size: 0.8rem; text-transform: uppercase;">{period}</div>
                <div style="color: #2ea043; font-size: 1.2rem; font-weight: bold; margin-top: 5px;">${val:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
