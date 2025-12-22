"""
Portfolio Tab - Portfolio tracking and analysis
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Portfolio - Finnie Chat",
    page_icon="📊",
    layout="wide"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

# Get user ID from session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

st.title("📊 Portfolio Insights")
st.markdown("Track and analyze your investment portfolio")

# Info banner
st.info("🚧 **Portfolio tracking coming soon!** This feature is under development (Phase 3 - Weeks 6-8)")

st.markdown("---")

# Placeholder metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Value",
        value="$0",
        delta="+0%",
        help="Total portfolio value (coming soon)"
    )

with col2:
    st.metric(
        label="Holdings",
        value="0",
        delta="0 stocks",
        help="Number of holdings (coming soon)"
    )

with col3:
    st.metric(
        label="Diversification",
        value="N/A",
        help="Diversification score 0-100 (coming soon)"
    )

with col4:
    st.metric(
        label="Risk Level",
        value="N/A",
        help="Portfolio risk assessment (coming soon)"
    )

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3 = st.tabs(["📈 Holdings", "🎯 Allocation", "📊 Analysis"])

with tab1:
    st.subheader("Your Holdings")
    st.write("**Coming Soon:** View and manage your stock holdings")
    
    # Placeholder table
    st.dataframe({
        "Ticker": ["AAPL", "MSFT", "GOOGL"],
        "Shares": [10, 5, 8],
        "Purchase Price": ["$150.00", "$300.00", "$2,500.00"],
        "Current Price": ["$180.00", "$350.00", "$2,800.00"],
        "Gain/Loss": ["+$300", "+$250", "+$2,400"],
        "% Return": ["+20%", "+16.7%", "+12%"]
    }, use_container_width=True)
    
    st.caption("_Sample data - Database integration coming in Phase 3_")

with tab2:
    st.subheader("Asset Allocation")
    st.write("**Coming Soon:** Interactive pie chart of your portfolio allocation")
    
    # Placeholder pie chart
    fig = px.pie(
        values=[40, 30, 20, 10],
        names=['Technology', 'Healthcare', 'Finance', 'Consumer'],
        title='Sample Portfolio Allocation',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("_Sample data - Real allocation coming in Phase 3_")

with tab3:
    st.subheader("Portfolio Analysis")
    st.write("**Coming Soon:** AI-powered portfolio insights and recommendations")
    
    # Placeholder analysis cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📊 Concentration Risk
        **Status:** Coming Soon
        
        - Top holding concentration
        - Sector concentration
        - Rebalancing suggestions
        """)
    
    with col2:
        st.markdown("""
        #### ⚠️ Risk Metrics
        **Status:** Coming Soon
        
        - Portfolio volatility
        - Sharpe ratio
        - Beta vs market
        """)

st.markdown("---")

# What's coming section
with st.expander("🔮 What's Coming in Phase 3"):
    st.markdown("""
    ### Portfolio System Features (Weeks 6-8)
    
    ✅ **Database Integration**
    - PostgreSQL for persistent storage
    - Real-time holdings tracking
    - Transaction history
    
    ✅ **Holdings Management**
    - Add/remove stocks
    - Track purchase prices
    - Calculate gains/losses
    
    ✅ **Advanced Analysis**
    - Portfolio Coach Agent insights
    - Risk Profiler assessment
    - Diversification scoring
    - Rebalancing recommendations
    
    ✅ **Interactive Charts**
    - Allocation pie charts
    - Performance over time
    - Sector breakdown
    - Gain/loss visualization
    
    **Stay tuned!** 🚀
    """)

# Footer
st.caption("Portfolio Tab | Phase 3 Coming Soon")
