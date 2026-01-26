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

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
        color: white;
    }
    .metric-label { font-size: 0.8em; color: #8b949e; }
    .metric-value { font-size: 1.8em; font-weight: bold; color: white; }
    .text-green { color: #2ea043; }
    .text-red { color: #da3633; }
    .text-yellow { color: #d29922; }
    div[data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif;
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

@st.cache_data(ttl=600)  # Cache for 10 minutes to avoid RPC spam unless sync is clicked
def load_data():
    # Load config
    try:
        with open("tools/config.json", "r") as f:
            config = json.load(f)
    except:
        config = {}
    
    # Load history
    try:
        with open("tools/history.json", "r") as f:
            history = json.load(f)
    except:
        history = []

    # Get latest data (try loading local files first)
    try:
        with open("tools/position_data.json", "r") as f:
            pos = json.load(f)
        with open("tools/fees_data.json", "r") as f:
            fees = json.load(f)
    except:
        pos = {}
        fees = {}
        
    return config, history, pos, fees

# Sync Action
def sync_data():
    with st.spinner("Syncing data from blockchain..."):
        # 1. Fetch Pool Data
        pos_data = fetch_data()
        
        # 2. Fetch Fees
        fees_data = fetch_fees()
        
        # 3. Update History
        if pos_data:
            try:
                with open("tools/history.json", "r") as f:
                    history = json.load(f)
            except:
                history = []
                
            snapshot = {
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "value_usd": pos_data['value_usd'],
                "fees_usd": pos_data['fees_usd'],
                "price_cbbtc": pos_data['price_cbbtc']
            }
            history.append(snapshot)
            with open("tools/history.json", "w") as f:
                json.dump(history, f, indent=2)
                
            # Reload everything
            st.cache_data.clear()
            st.rerun()

# Main App
def main():
    config, history, pos, fees_data = load_data()
    
    # Check if we have data
    if not pos:
        st.warning("No data found. Click 'Sync Data' to fetch initial data.")
        if st.button("Sync Data"):
            sync_data()
        return

    # Computed Values
    symbol0 = pos.get('symbol0', 'USDC')
    symbol1 = pos.get('symbol1', 'cbBTC')
    amount0 = pos.get('amount0', 0)
    amount1 = pos.get('amount1', 0)
    value_usd = pos.get('value_usd', 0)
    fees_usd_pending = pos.get('fees_usd', 0)
    price_cbbtc = pos.get('price_cbbtc', 0)
    price_lower = pos.get('price_lower', 0)
    price_upper = pos.get('price_upper', 0)
    price_current = pos.get('price_current', 0)
    in_range = pos.get('in_range', False)
    
    # Unclaimed Breakdown
    unclaimed_0 = pos.get('unclaimed_0', 0) / 1e6
    unclaimed_1 = pos.get('unclaimed_1', 0) / 1e8
    
    # Automated Fees
    collected_usdc = fees_data.get('total_collected_usdc', 0)
    collected_cbbtc = fees_data.get('total_collected_cbbtc', 0)
    fees_collected_value = (collected_usdc * 1.0) + (collected_cbbtc * price_cbbtc)
    
    # Pending Value Calculation (Recalculate to be precise)
    fees_pending_value = (unclaimed_0 * 1.0) + (unclaimed_1 * price_cbbtc)
    
    # Total Fees
    total_fees = fees_pending_value + fees_collected_value
    
    # Config Params
    total_invested = config.get("total_invested_usd", 119.16)
    initial_price = config.get("initial_cbbtc_price", 88685)
    deposit_date_str = config.get("deposit_date", "2025-11-24")
    
    # Derived Metrics
    net_pnl = value_usd - total_invested + total_fees
    roi_percent = (net_pnl / total_invested) * 100 if total_invested > 0 else 0
    
    deposit_dt = datetime.datetime.strptime(deposit_date_str, "%Y-%m-%d")
    days_active = (datetime.datetime.now() - deposit_dt).days + 1
    
    fee_apr = calculate_fee_apr(total_fees, total_invested, days_active)
    total_apr = (roi_percent / days_active) * 365 if days_active > 0 else 0
    
    price_ratio = price_cbbtc / initial_price if initial_price > 0 else 1
    il_percent = calculate_impermanent_loss(price_ratio)
    
    initial_btc = (total_invested * 0.5) / initial_price
    initial_usdc = total_invested * 0.5
    hodl_value = (initial_btc * price_cbbtc) + initial_usdc
    lp_vs_hodl = (value_usd + total_fees) - hodl_value

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"Liquidity Pool Tracker: {symbol0}/{symbol1}")
        st.caption(f"NFT #{config.get('nft_id')} | Base Network | Uniswap V3")
    with col2:
        status_color = "green" if in_range else "red"
        st.markdown(f"#### Status: :{status_color}[{'In Range' if in_range else 'Out of Range'}]")
        if st.button("🔄 Sync Data", type="primary"):
            sync_data()

    # KPI Row 1
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Pooled Assets", f"${value_usd:,.2f}")
    c2.metric("Total PnL", f"${net_pnl:,.2f}", delta=f"{net_pnl:,.2f}")
    c3.metric("Fee APR", f"{fee_apr:.2f}%")
    c4.metric("Total APR", f"{total_apr:.2f}%")
    c5.metric("ROI", f"{roi_percent:.2f}%", delta=f"{roi_percent:.2f}%")
    
    st.divider()
    
    # KPI Row 2
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Impermanent Loss", f"{il_percent:.2f}%", help=f"Price Ratio: {price_ratio:.2f}x")
    
    fees_tooltip = f"""
    Collected: {collected_usdc:.4f} USDC + {collected_cbbtc:.8f} cbBTC
    Pending: {unclaimed_0:.4f} USDC + {unclaimed_1:.8f} cbBTC
    """
    c2.metric("Total Fees Earned", f"${total_fees:,.2f}", help=fees_tooltip)
    
    c3.metric("LP vs HODL", f"${lp_vs_hodl:,.2f}", delta=f"{lp_vs_hodl:,.2f}", help=f"HODL Value: ${hodl_value:,.2f}")
    c4.metric("cbBTC Price", f"${price_cbbtc:,.0f}", delta=f"{(price_cbbtc/initial_price - 1)*100:.1f}%")
    
    st.divider()

    # Analysis Section
    col_chart, col_details = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Value History")
        if history:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df['date'], y=df['value_usd'], mode='lines+markers', name='Value', line=dict(color='#2ea043')))
            fig.update_layout(
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                font=dict(color='white'),
                margin=dict(l=20, r=20, t=20, b=20),
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No history data yet.")

    with col_details:
        st.subheader("Position Details")
        st.text(f"Deposit Date: {deposit_date_str}")
        st.text(f"Age: {days_active} days")
        st.text(f"Initial Investment: ${total_invested:,.2f}")
        st.text(f"Initial Price: ${initial_price:,.0f}")
        
        st.subheader("Token Balances")
        st.text(f"{symbol0}: {amount0:.6f}")
        st.text(f"{symbol1}: {amount1:.8f}")
        
        st.subheader("Range")
        st.text(f"Min: {price_lower:,.2f}")
        st.text(f"Max: {price_upper:,.2f}")
        st.caption("cbBTC/USDC")

if __name__ == "__main__":
    main()
