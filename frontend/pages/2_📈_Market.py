"""
Market Tab - Market trends and stock screeners
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Market Trends - Finnie Chat",
    page_icon="📈",
    layout="wide"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

st.title("📈 Market Trends & Screeners")
st.markdown("Real-time market data and investment opportunities")

# Info banner
st.info("🚧 **Market analysis coming soon!** This feature is under development (Phase 4 - Weeks 9-10)")

st.markdown("---")

# Market overview metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="S&P 500",
        value="4,500",
        delta="+1.2%",
        help="S&P 500 Index (sample data)"
    )

with col2:
    st.metric(
        label="NASDAQ",
        value="14,200",
        delta="+1.8%",
        help="NASDAQ Composite (sample data)"
    )

with col3:
    st.metric(
        label="Dow Jones",
        value="35,000",
        delta="+0.9%",
        help="Dow Jones Industrial Average (sample data)"
    )

st.markdown("---")

# Tabs for different market views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔥 Heatmap", "🔍 Screeners", "📰 News"])

with tab1:
    st.subheader("Market Overview")
    st.write("**Coming Soon:** Real-time market indices and trends")
    
    # Placeholder line chart
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    sample_data = pd.DataFrame({
        'Date': dates,
        'S&P 500': 4300 + np.cumsum(np.random.randn(100) * 10),
        'NASDAQ': 13800 + np.cumsum(np.random.randn(100) * 15),
        'Dow Jones': 34500 + np.cumsum(np.random.randn(100) * 12)
    })
    
    fig = px.line(
        sample_data, 
        x='Date', 
        y=['S&P 500', 'NASDAQ', 'Dow Jones'],
        title='Sample Market Indices Performance',
        labels={'value': 'Index Value', 'variable': 'Index'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("_Sample data - Real market data coming in Phase 4_")

with tab2:
    st.subheader("Sector Heatmap")
    st.write("**Coming Soon:** Interactive sector performance heatmap")
    
    # Placeholder heatmap data
    sectors = ['Technology', 'Healthcare', 'Finance', 'Consumer', 'Energy', 
               'Materials', 'Utilities', 'Real Estate', 'Communications']
    performance = [2.5, 1.8, -0.5, 1.2, 3.1, -1.2, 0.8, -0.3, 1.5]
    
    fig = go.Figure(data=go.Bar(
        x=sectors,
        y=performance,
        marker_color=['green' if p > 0 else 'red' for p in performance]
    ))
    fig.update_layout(
        title='Sample Sector Performance Today',
        xaxis_title='Sector',
        yaxis_title='% Change',
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("_Sample data - Real sector data coming in Phase 4_")

with tab3:
    st.subheader("Stock Screeners")
    st.write("**Coming Soon:** Advanced stock screening tools")
    
    # Screener type selector
    screener_type = st.selectbox(
        "Select Screener Type",
        ["Dividend Stocks", "Growth Stocks", "Value Stocks", "Momentum Plays", "Sector Leaders"],
        help="Choose the type of stocks to screen"
    )
    
    st.markdown(f"### {screener_type} Screener")
    
    # Placeholder screener results
    if screener_type == "Dividend Stocks":
        st.dataframe({
            "Ticker": ["JNJ", "KO", "PG", "T", "VZ"],
            "Company": ["Johnson & Johnson", "Coca-Cola", "Procter & Gamble", "AT&T", "Verizon"],
            "Dividend Yield": ["2.8%", "3.1%", "2.5%", "7.2%", "6.8%"],
            "Payout Ratio": ["45%", "65%", "55%", "90%", "85%"],
            "Price": ["$165", "$58", "$148", "$18", "$38"]
        }, use_container_width=True)
    elif screener_type == "Growth Stocks":
        st.dataframe({
            "Ticker": ["NVDA", "TSLA", "AMD", "SHOP", "SQ"],
            "Company": ["NVIDIA", "Tesla", "AMD", "Shopify", "Block"],
            "YoY Growth": ["125%", "85%", "95%", "70%", "55%"],
            "P/E Ratio": ["65", "55", "48", "N/A", "N/A"],
            "Price": ["$485", "$245", "$145", "$68", "$75"]
        }, use_container_width=True)
    else:
        st.dataframe({
            "Ticker": ["AAPL", "MSFT", "GOOGL", "META", "AMZN"],
            "Company": ["Apple", "Microsoft", "Alphabet", "Meta", "Amazon"],
            "Price": ["$180", "$350", "$140", "$385", "$155"],
            "Change": ["+2.5%", "+1.8%", "+3.2%", "+1.5%", "+2.1%"],
            "Volume": ["85M", "32M", "28M", "18M", "45M"]
        }, use_container_width=True)
    
    st.caption("_Sample data - Real screeners coming in Phase 4_")

with tab4:
    st.subheader("Market News")
    st.write("**Coming Soon:** Latest financial news and analysis")
    
    # Placeholder news items
    st.markdown("""
    #### 📰 Latest Headlines
    
    🔴 **Sample News Item 1**  
    _Dec 22, 2025 - 10:30 AM_  
    Markets rally on positive economic data...
    
    🟢 **Sample News Item 2**  
    _Dec 22, 2025 - 09:15 AM_  
    Tech sector leads gains as AI stocks surge...
    
    🔵 **Sample News Item 3**  
    _Dec 22, 2025 - 08:00 AM_  
    Fed signals potential rate cuts in 2026...
    
    _Real news feed coming in Phase 4_
    """)

st.markdown("---")

# What's coming section
with st.expander("🔮 What's Coming in Phase 4"):
    st.markdown("""
    ### Market Trends Features (Weeks 9-10)
    
    ✅ **Real-Time Market Data**
    - Live index prices
    - Sector performance tracking
    - Top movers (gainers/losers)
    
    ✅ **Advanced Screeners**
    - Dividend yield screening
    - Growth stock identification
    - Value stock discovery
    - Momentum analysis
    - Sector leaders
    
    ✅ **Market Intelligence**
    - Strategy Agent integration
    - AI-powered stock recommendations
    - Trend analysis
    - Pattern recognition
    
    ✅ **Interactive Visualizations**
    - Real-time heatmaps
    - Correlation matrices
    - Performance charts
    - Sector breakdowns
    
    **Stay tuned!** 🚀
    """)

# Footer
st.caption("Market Trends Tab | Phase 4 Coming Soon")
