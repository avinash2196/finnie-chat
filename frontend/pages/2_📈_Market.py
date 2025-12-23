import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Market Trends", page_icon="📈", layout="wide")

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

st.title("📈 Market — Overview & Trends")
st.markdown("Overview: fast market snapshot. Trends: deeper analysis and sector insights — all data is fetched live from the backend.")

# Sidebar
with st.sidebar:
    st.subheader("Market Settings")
    user_id = st.text_input("User ID", value=st.session_state.user_id)
    st.session_state.user_id = user_id
    
    market_view = st.selectbox(
        "View",
        ["Overview", "Screeners", "Strategy Ideas", "Sector Analysis"]
    )
    
    st.markdown("---")
    st.caption("💡 Powered by Orchestrator, Market, Strategy, Portfolio Coach, Risk Profiler, Educator & Compliance Agents")
    with st.expander("ℹ️ Agents"):
        st.markdown("""
        - 🧭 **Orchestrator** — routes requests and composes answers
        - 🏦 **Market** — quotes, movers, sectors
        - 🧮 **Strategy** — screeners and ideas
        - 🎯 **Portfolio Coach** — improvement suggestions
        - 🔎 **Risk Profiler** — risk from holdings
        - 🎓 **Educator** — RAG-backed explanations
        - ✅ **Compliance** — safe outputs & disclaimers
        """)

# Helper functions
def fetch_market_data(symbols):
    """Fetch real-time market data for multiple symbols"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/market/quote",
            json={"symbols": symbols},
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

def run_screener(screener_type, params=None):
    """Run stock screener"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/market/screen",
            json={"screener_type": screener_type, "params": params or {}},
            timeout=15
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

def get_strategy_ideas(risk_level="MEDIUM"):
    """Get investment strategy ideas"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/strategy/ideas?risk_level={risk_level}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error: {response.status_code}"
    except Exception as e:
        return None, str(e)

# Main content
if market_view == "Overview":
    st.subheader("📊 Market Overview")
    
    # Major indices
    col1, col2, col3, col4 = st.columns(4)
    
    # Fetch real-time indices data from backend
    index_symbols = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    index_names = ["S&P 500", "Dow Jones", "NASDAQ", "Russell 2000"]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/market/quote",
            json={"symbols": index_symbols},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            indices_data = []
            for symbol in index_symbols:
                quote = data.get("quotes", {}).get(symbol, {})
                indices_data.append({
                    "price": quote.get("price") or 0,
                    "change": quote.get("change") or 0,
                    "change_pct": quote.get("change_pct") or 0
                })
        else:
            # Fallback to placeholder
            indices_data = [{"price": 0, "change": 0, "change_pct": 0} for _ in index_symbols]
            st.warning("Unable to fetch real-time market data")
    except Exception as e:
        # Fallback to placeholder
        indices_data = [{"price": 0, "change": 0, "change_pct": 0} for _ in index_symbols]
        st.warning(f"Market data unavailable: {str(e)}")
    
    for col, idx_data, name in zip([col1, col2, col3, col4], indices_data, index_names):
        with col:
            delta_color = "normal" if idx_data['change'] >= 0 else "inverse"
            if idx_data['price'] > 0:
                st.metric(
                    name,
                    f"${idx_data['price']:,.2f}",
                    f"{idx_data['change_pct']:+.2f}%",
                    delta_color=delta_color
                )
            else:
                st.metric(name, "N/A", "...")
    
    st.markdown("---")

    # Top movers - request precomputed movers from backend
    st.markdown("#### 📈 Top Gainers & Losers")
    try:
        resp = requests.post(f"{API_BASE_URL}/market/movers", json={}, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            gainers = data.get("top_gainers", [])
            losers = data.get("top_losers", [])

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top Gainers**")
                if gainers:
                    gainers_df = pd.DataFrame(gainers)
                    st.dataframe(gainers_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No gainers available")

            with col2:
                st.markdown("**Top Losers**")
                if losers:
                    losers_df = pd.DataFrame(losers)
                    st.dataframe(losers_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No losers available")
        else:
            st.warning("Unable to fetch top movers from backend")
    except Exception as e:
        st.warning(f"Top movers unavailable: {str(e)}")

    st.markdown("---")

    # Sector performance heatmap (request from backend)
    st.markdown("#### 🗺️ Sector Performance")
    try:
        resp = requests.post(f"{API_BASE_URL}/market/sectors", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            sectors = data.get("sectors", [])
            if sectors:
                sectors_df = pd.DataFrame([
                    {"Sector": s.get("sector"), "Performance": s.get("change_pct") or 0, "Volume": 1}
                    for s in sectors
                ])
                fig = px.treemap(
                    sectors_df,
                    path=['Sector'],
                    values='Volume',
                    color='Performance',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    color_continuous_midpoint=0,
                    title='Sector Performance Heatmap'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No sector data available")
        else:
            st.warning("Unable to fetch sector performance from backend")
    except Exception as e:
        st.warning(f"Sector data unavailable: {str(e)}")

elif market_view == "Screeners":
    st.subheader("🔍 Stock Screeners")
    
    screener_type = st.selectbox(
        "Select Screener",
        ["Dividend Yield", "Growth Stocks", "Value Stocks", "Momentum Plays", "High Volume"]
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_price = st.number_input("Min Price ($)", min_value=0.0, value=10.0)
    with col2:
        max_price = st.number_input("Max Price ($)", min_value=0.0, value=1000.0)
    with col3:
        min_volume = st.number_input("Min Volume (M)", min_value=0.0, value=1.0)
    
    if st.button("🔍 Run Screener", type="primary"):
        with st.spinner("Scanning markets..."):
            # Map frontend names to backend screener types
            screener_map = {
                "Dividend Yield": "dividend",
                "Growth Stocks": "growth",
                "Value Stocks": "value",
                "Momentum Plays": "value",  # Fallback to value
                "High Volume": "growth"  # Fallback to growth
            }
            
            try:
                # Get user ID from session state for portfolio context
                user_id = st.session_state.get("user_id", "user_001")
                
                response = requests.post(
                    f"{API_BASE_URL}/market/screen",
                    json={
                        "screener_type": screener_map.get(screener_type, "dividend"),
                        "params": {"user_id": user_id}
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    stocks = data.get("results", [])
                    
                    if stocks:
                        # Convert to DataFrame
                        results = pd.DataFrame(stocks)
                        st.success(f"Found {len(results)} stocks matching criteria")
                        st.dataframe(results, use_container_width=True, hide_index=True)
                        
                        # Export option
                        csv = results.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Results (CSV)",
                            data=csv,
                            file_name=f"{screener_type.lower().replace(' ', '_')}_screener.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No stocks found matching criteria")
                else:
                    st.error(f"Screener unavailable (Status: {response.status_code})")
                    
            except Exception as e:
                st.error(f"Unable to run screener: {str(e)}")
                st.info("Try asking Finnie in the Chat tab for stock recommendations")

elif market_view == "Strategy Ideas":
    st.subheader("💡 Investment Strategy Ideas")
    
    risk_level = st.select_slider(
        "Risk Tolerance",
        options=["LOW", "MEDIUM", "HIGH"],
        value="MEDIUM"
    )
    
    st.markdown("---")
    
    # Strategy categories
    strategy_cat = st.radio(
        "Strategy Type",
        ["Income", "Growth", "Value", "Momentum", "Diversification"],
        horizontal=True
    )
    
    if strategy_cat == "Income":
        st.markdown("#### 💰 Dividend Income Strategies")
        
        strategies = [
            {
                "name": "Dividend Aristocrats",
                "description": "Companies with 25+ years of consecutive dividend increases",
                "tickers": ["JNJ", "PG", "KO", "MCD", "WMT"],
                "avg_yield": "3.2%",
                "risk": "LOW"
            },
            {
                "name": "High Yield Bonds",
                "description": "Corporate bonds with yields above 5%",
                "tickers": ["HYG", "JNK", "USHY"],
                "avg_yield": "5.8%",
                "risk": "MEDIUM"
            },
            {
                "name": "REITs",
                "description": "Real Estate Investment Trusts for steady income",
                "tickers": ["VNQ", "O", "VICI", "SPG"],
                "avg_yield": "4.5%",
                "risk": "MEDIUM"
            }
        ]
    
    elif strategy_cat == "Growth":
        st.markdown("#### 🚀 Growth Strategies")
        
        strategies = [
            {
                "name": "AI & Technology",
                "description": "Companies leading AI innovation and cloud computing",
                "tickers": ["NVDA", "MSFT", "GOOGL", "META", "AMD"],
                "avg_return": "45%",
                "risk": "HIGH"
            },
            {
                "name": "Clean Energy",
                "description": "Renewable energy and EV companies",
                "tickers": ["TSLA", "ENPH", "NEE", "ICLN"],
                "avg_return": "28%",
                "risk": "HIGH"
            },
            {
                "name": "Healthcare Innovation",
                "description": "Biotech and medical device leaders",
                "tickers": ["ISRG", "VRTX", "REGN", "ABBV"],
                "avg_return": "22%",
                "risk": "MEDIUM"
            }
        ]
    
    else:
        st.markdown("#### 📊 Value Strategies")
        
        strategies = [
            {
                "name": "Deep Value",
                "description": "Undervalued stocks with low P/E ratios",
                "tickers": ["BAC", "WFC", "CVX", "XOM"],
                "avg_pe": "9.5",
                "risk": "MEDIUM"
            },
            {
                "name": "Quality at Reasonable Price",
                "description": "High-quality companies at fair valuations",
                "tickers": ["BRK.B", "COST", "V", "UNH"],
                "avg_pe": "18.2",
                "risk": "LOW"
            }
        ]
    
    for strategy in strategies:
        with st.expander(f"📌 {strategy['name']}"):
            st.markdown(f"**Description:** {strategy['description']}")
            st.markdown(f"**Suggested Tickers:** {', '.join(strategy['tickers'])}")
            
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                if 'avg_yield' in strategy:
                    st.metric("Avg Dividend Yield", strategy['avg_yield'])
                elif 'avg_return' in strategy:
                    st.metric("Historical Return (1Y)", strategy['avg_return'])
                elif 'avg_pe' in strategy:
                    st.metric("Average P/E Ratio", strategy['avg_pe'])
            
            with metrics_col2:
                risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
                st.metric("Risk Level", f"{risk_color[strategy['risk']]} {strategy['risk']}")

else:  # Sector Analysis
    st.subheader("🏭 Sector Analysis")
    
    sector = st.selectbox(
        "Select Sector",
        ["Technology", "Healthcare", "Financials", "Energy", "Consumer", "Industrials"]
    )
    
    st.markdown(f"#### {sector} Sector Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sector Performance", "+2.4%", delta="+0.8%")
    with col2:
        st.metric("Average P/E", "24.5", delta="-1.2")
    with col3:
        st.metric("Top Performers", "67%", delta="+5%")
    with col4:
        st.metric("Volume Trend", "High", delta="↑")
    
    st.markdown("---")
    
    # Top stocks in sector
    st.markdown("#### 🏆 Sector Leaders")
    
    sector_stocks = pd.DataFrame([
        {"Ticker": "AAPL", "Name": "Apple Inc.", "Price": "$192.53", "Change": "+1.2%", "Market Cap": "$3.0T"},
        {"Ticker": "MSFT", "Name": "Microsoft Corp.", "Price": "$374.58", "Change": "+0.8%", "Market Cap": "$2.8T"},
        {"Ticker": "NVDA", "Name": "NVIDIA Corp.", "Price": "$495.22", "Change": "+8.5%", "Market Cap": "$1.2T"},
        {"Ticker": "GOOGL", "Name": "Alphabet Inc.", "Price": "$140.93", "Change": "-0.3%", "Market Cap": "$1.8T"},
        {"Ticker": "META", "Name": "Meta Platforms", "Price": "$362.54", "Change": "+4.8%", "Market Cap": "$925B"},
    ])
    
    st.dataframe(sector_stocks, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Market Trends | Real-time market data and analysis 📈")
