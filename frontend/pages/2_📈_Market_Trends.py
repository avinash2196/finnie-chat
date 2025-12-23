import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Market Trends", page_icon="📈", layout="wide")

# API Configuration: prefer env var, fallback to localhost
API_BASE_URL = os.getenv("API_BASE_URL") or "http://localhost:8000"

# Session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

st.title("📈 Market Trends & Analysis")
st.markdown("Discover market opportunities and investment ideas")

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
    indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]
    index_names = ["S&P 500", "Dow Jones", "NASDAQ", "Russell 2000"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Mock data for indices (replace with actual API call)
    mock_indices = [
        {"symbol": "^GSPC", "price": 4783.45, "change": 0.75, "change_pct": 0.016},
        {"symbol": "^DJI", "price": 37305.16, "change": -45.23, "change_pct": -0.012},
        {"symbol": "^IXIC", "price": 14813.92, "change": 123.45, "change_pct": 0.084},
        {"symbol": "^RUT", "price": 2027.07, "change": 12.34, "change_pct": 0.061},
    ]
    
    for col, idx_data, name in zip([col1, col2, col3, col4], mock_indices, index_names):
        with col:
            delta_color = "normal" if idx_data['change'] >= 0 else "inverse"
            st.metric(
                name,
                f"${idx_data['price']:,.2f}",
                f"{idx_data['change_pct']:+.2f}%",
                delta_color=delta_color
            )
    
    st.markdown("---")
    
    # Top movers
    st.markdown("#### 📈 Top Gainers & Losers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top Gainers**")
        gainers = pd.DataFrame([
            {"Ticker": "NVDA", "Price": "$495.22", "Change": "+8.5%"},
            {"Ticker": "AMD", "Price": "$142.87", "Change": "+6.2%"},
            {"Ticker": "TSLA", "Price": "$248.42", "Change": "+5.1%"},
            {"Ticker": "META", "Price": "$362.54", "Change": "+4.8%"},
            {"Ticker": "AMZN", "Price": "$151.94", "Change": "+3.9%"},
        ])
        st.dataframe(gainers, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Top Losers**")
        losers = pd.DataFrame([
            {"Ticker": "INTC", "Price": "$43.21", "Change": "-5.3%"},
            {"Ticker": "BA", "Price": "$210.45", "Change": "-4.7%"},
            {"Ticker": "DIS", "Price": "$92.18", "Change": "-3.2%"},
            {"Ticker": "NFLX", "Price": "$478.33", "Change": "-2.8%"},
            {"Ticker": "PYPL", "Price": "$62.52", "Change": "-2.1%"},
        ])
        st.dataframe(losers, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Sector performance heatmap
    st.markdown("#### 🗺️ Sector Performance")
    
    sectors_data = {
        'Sector': ['Technology', 'Healthcare', 'Financials', 'Energy', 'Industrials', 
                   'Consumer Disc.', 'Materials', 'Real Estate', 'Utilities', 'Telecom'],
        'Performance': [2.4, 1.2, -0.5, 3.1, 0.8, -1.2, 1.5, -0.8, 0.3, 0.6],
        'Volume': [100, 85, 120, 95, 78, 88, 72, 65, 55, 60]
    }
    
    sectors_df = pd.DataFrame(sectors_data)
    
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
            # Mock screener results
            if screener_type == "Dividend Yield":
                results = pd.DataFrame([
                    {"Ticker": "VZ", "Price": "$38.45", "Div Yield": "6.8%", "P/E": "8.2", "Market Cap": "$161B"},
                    {"Ticker": "T", "Price": "$15.92", "Div Yield": "6.5%", "P/E": "7.1", "Market Cap": "$114B"},
                    {"Ticker": "MO", "Price": "$42.18", "Div Yield": "8.2%", "P/E": "9.4", "Market Cap": "$75B"},
                    {"Ticker": "ABBV", "Price": "$158.43", "Div Yield": "3.9%", "P/E": "35.2", "Market Cap": "$280B"},
                    {"Ticker": "PFE", "Price": "$28.92", "Div Yield": "5.8%", "P/E": "10.1", "Market Cap": "$163B"},
                ])
            elif screener_type == "Growth Stocks":
                results = pd.DataFrame([
                    {"Ticker": "NVDA", "Price": "$495.22", "Rev Growth": "126%", "EPS Growth": "288%", "Market Cap": "$1.22T"},
                    {"Ticker": "AVGO", "Price": "$892.45", "Rev Growth": "47%", "EPS Growth": "65%", "Market Cap": "$413B"},
                    {"Ticker": "AMD", "Price": "$142.87", "Rev Growth": "54%", "EPS Growth": "112%", "Market Cap": "$231B"},
                    {"Ticker": "PLTR", "Price": "$18.45", "Rev Growth": "21%", "EPS Growth": "145%", "Market Cap": "$39B"},
                    {"Ticker": "SNOW", "Price": "$182.34", "Rev Growth": "36%", "EPS Growth": "N/A", "Market Cap": "$57B"},
                ])
            else:
                results = pd.DataFrame([
                    {"Ticker": "BAC", "Price": "$32.45", "P/E": "10.2", "P/B": "1.1", "Market Cap": "$251B"},
                    {"Ticker": "WFC", "Price": "$47.89", "P/E": "11.5", "P/B": "1.2", "Market Cap": "$172B"},
                    {"Ticker": "C", "Price": "$51.23", "P/E": "9.8", "P/B": "0.7", "Market Cap": "$95B"},
                    {"Ticker": "JPM", "Price": "$167.54", "P/E": "10.9", "P/B": "1.6", "Market Cap": "$482B"},
                    {"Ticker": "GS", "Price": "$382.19", "P/E": "12.3", "P/B": "1.4", "Market Cap": "$128B"},
                ])
            
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
