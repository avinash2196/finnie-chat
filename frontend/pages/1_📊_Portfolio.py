"""
Portfolio Tab - Portfolio tracking and analysis
"""
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

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

# Helper functions
def fetch_portfolio_data(user_id):
    """Fetch portfolio data from backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/portfolio", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            return None, "User not found. Click 'Create User' to get started."
        else:
            return None, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Backend connection error: {str(e)}"

def fetch_transactions(user_id):
    """Fetch transaction history from backend API"""
    try:
        # Show broader history by default
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/transactions?days=3650", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract transactions list from response
            return data.get('transactions', []), None
        else:
            return None, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Backend connection error: {str(e)}"

def fetch_allocation(user_id):
    """Fetch asset allocation from backend API"""
    try:
        response = requests.get(f"{API_BASE_URL}/users/{user_id}/allocation", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Backend connection error: {str(e)}"

def create_user(username, email):
    """Create a new user in the database"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users",
            json={"username": username, "email": email},
            timeout=5
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def sync_portfolio(user_id, provider):
    """Trigger portfolio sync from external provider"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users/{user_id}/sync",
            json={"provider": provider},
            timeout=10
        )
        return response.status_code == 200, response.json() if response.status_code == 200 else response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

st.title("📊 Portfolio Insights")
st.markdown("Track and analyze your investment portfolio")
st.caption(f"Active User: {st.session_state.user_id}")

# Sidebar controls
with st.sidebar:
    st.subheader("Portfolio Controls")
    user_id = st.text_input("User ID", value=st.session_state.user_id, key="portfolio_user_id")
    st.session_state.user_id = user_id
    
    st.markdown("---")
    
    # Sync controls
    st.subheader("Sync Portfolio")
    provider = st.selectbox("Provider", ["mock", "robinhood", "fidelity"])
    
    if st.button("🔄 Sync Now", type="primary"):
        with st.spinner("Syncing portfolio..."):
            success, result = sync_portfolio(user_id, provider)
            if success:
                st.success(f"✅ Synced {result.get('synced_items', 0)} items in {result.get('sync_time_ms', 0)}ms")
                st.rerun()
            else:
                st.error(f"❌ Sync failed: {result}")
    
    st.markdown("---")
    
    # User creation
    with st.expander("Create New User"):
        new_email = st.text_input("Email", value=f"{user_id}@example.com")
        new_username = st.text_input("Username", value=user_id)
        if st.button("Create User"):
            success, result = create_user(new_username, new_email)
            if success:
                st.success("✅ User created!")
                st.rerun()
            else:
                st.error(f"❌ {result}")

    st.markdown("---")
    st.caption("💡 Powered by Orchestrator, Market, Strategy, Portfolio Coach, Risk Profiler, Educator & Compliance Agents")
    with st.expander("ℹ️ Agents & Docs"):
        st.markdown("""
        - 🧭 **Orchestrator** — routes requests and composes answers
        - 🏦 **Market** — quotes, movers, sectors
        - 🧮 **Strategy** — screeners and ideas
        - 🎯 **Portfolio Coach** — improvement suggestions
        - 🔎 **Risk Profiler** — risk from holdings
        - 🎓 **Educator** — RAG-backed explanations
        - ✅ **Compliance** — safe outputs & disclaimers
        
        **Useful Links:**
        - [API Docs (FastAPI)](http://localhost:8000/docs)
        - [Streamlit App (Home)](http://localhost:8501)
        """)

# Fetch portfolio data
portfolio_data, error = fetch_portfolio_data(user_id)

if error:
    st.warning(f"⚠️ {error}")
    st.info("💡 Tip: Create a user and sync with the 'mock' provider to see sample data")
    st.stop()

if not portfolio_data:
    st.error("❌ No portfolio data available")
    st.stop()

st.markdown("---")

# Portfolio metrics
col1, col2, col3, col4 = st.columns(4)

total_value = portfolio_data.get('total_portfolio_value', 0)
total_gain = portfolio_data.get('total_gain_loss', 0)
total_gain_pct = portfolio_data.get('total_gain_loss_pct', 0)
num_holdings = len(portfolio_data.get('holdings', []))

with col1:
    st.metric(
        label="Total Value",
        value=f"${total_value:,.2f}",
        delta=f"{total_gain_pct:+.2f}%",
        help="Total portfolio value"
    )

with col2:
    st.metric(
        label="Total Gain/Loss",
        value=f"${total_gain:,.2f}",
        delta=f"${total_gain:+,.2f}",
        help="Total unrealized gain/loss"
    )

with col3:
    st.metric(
        label="Holdings",
        value=str(num_holdings),
        delta=f"{num_holdings} stocks",
        help="Number of holdings"
    )

with col4:
    diversification = "Good" if num_holdings >= 5 else "Low" if num_holdings >= 3 else "Poor"
    st.metric(
        label="Diversification",
        value=diversification,
        help="Diversification assessment based on number of holdings"
    )

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Holdings", "🎯 Allocation", "📊 Transactions", "📉 Performance", "⚙️ Manage"])

with tab1:
    st.subheader("Your Holdings")
    
    holdings = portfolio_data.get('holdings', [])
    total_portfolio = portfolio_data.get('total_value', 1)  # Avoid division by zero
    
    if holdings:
        # Create DataFrame for holdings
        holdings_df = pd.DataFrame([
            {
                "Ticker": h['ticker'],
                "Shares": h['quantity'],
                "Avg Price": f"${h['purchase_price']:.2f}",
                "Current Price": f"${h['current_price']:.2f}",
                "Total Value": f"${h['total_value']:.2f}",
                "Gain/Loss": f"${h['gain_loss']:.2f}",
                "% Return": f"{h['gain_loss_pct']:+.2f}%",
                "% of Portfolio": f"{(h['total_value'] / total_portfolio * 100):.1f}%"
            }
            for h in holdings
        ])
        
        # Display holdings table
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)
        
        # Holding details in expandable sections
        st.markdown("#### Holding Details")
        for h in holdings:
            gain_loss_color = "🟢" if h['gain_loss'] >= 0 else "🔴"
            with st.expander(f"{gain_loss_color} {h['ticker']} - ${h['total_value']:.2f} ({h['gain_loss_pct']:+.2f}%)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Shares", h['quantity'])
                    st.metric("Purchase Price", f"${h['purchase_price']:.2f}")
                with col2:
                    st.metric("Current Price", f"${h['current_price']:.2f}")
                    st.metric("Total Value", f"${h['total_value']:.2f}")
                with col3:
                    st.metric("Gain/Loss", f"${h['gain_loss']:.2f}", delta=f"{h['gain_loss_pct']:+.2f}%")
                    st.metric("% of Portfolio", f"{(h['total_value'] / total_portfolio * 100):.1f}%")
    else:
        st.info("No holdings found. Sync your portfolio to get started!")

with tab2:
    st.subheader("Asset Allocation")
    
    allocation_data, alloc_error = fetch_allocation(user_id)
    
    if allocation_data and allocation_data.get('allocation'):
        # Create pie chart from allocation response
        tickers = [a['ticker'] for a in allocation_data['allocation']]
        values = [a['value'] for a in allocation_data['allocation']]
        percentages = [a['percentage'] for a in allocation_data['allocation']]
        
        fig = px.pie(
            values=values,
            names=tickers,
            title='Portfolio Allocation by Holding',
            color_discrete_sequence=px.colors.qualitative.Set3,
            hover_data={'values': values},
            labels={'values': 'Value ($)'}
        )
        
        fig.update_traces(
            textposition='inside',
            texttemplate='%{label}<br>%{percent:.1%}',
            hovertemplate='<b>%{label}</b><br>Value: $%{value:,.2f}<br>Percentage: %{percent:.1%}<extra></extra>'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Allocation summary
        st.markdown("#### Allocation Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Portfolio Value", f"${allocation_data['total_value']:,.2f}")
            st.metric("Number of Holdings", len(allocation_data['allocation']))
        
        with col2:
            # Calculate concentration (largest holding percentage)
            max_concentration = max(percentages) if percentages else 0
            concentration_status = "⚠️ High" if max_concentration > 30 else "✅ Balanced"
            st.metric("Largest Position", f"{max_concentration:.1f}%")
            st.metric("Concentration Risk", concentration_status)
    else:
        st.info("No allocation data available. Add holdings to see allocation breakdown.")

with tab3:
    st.subheader("Transaction History")
    
    transactions_data, trans_error = fetch_transactions(user_id)
    
    if transactions_data:
        # Ensure transactions_data is a list
        if isinstance(transactions_data, list) and len(transactions_data) > 0:
            # Create DataFrame for transactions
            trans_df = pd.DataFrame([
                {
                    "Date": datetime.fromisoformat(t.get('date', t.get('timestamp', '')).replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M'),
                    "Type": t.get('type', t.get('transaction_type', '')),
                    "Ticker": t.get('ticker', ''),
                    "Quantity": t.get('quantity', 0),
                    "Price": f"${t.get('price', 0):.2f}",
                    "Total": f"${t.get('total', t.get('total_amount', 0)):.2f}"
                }
                for t in transactions_data
            ])
            
            st.dataframe(trans_df, use_container_width=True, hide_index=True)
            
            # Transaction summary
            st.markdown("#### Transaction Summary")
            col1, col2, col3 = st.columns(3)
            
            buys = [t for t in transactions_data if t.get('type', t.get('transaction_type')) == 'BUY']
            sells = [t for t in transactions_data if t.get('type', t.get('transaction_type')) == 'SELL']
            dividends = [t for t in transactions_data if t.get('type', t.get('transaction_type')) == 'DIVIDEND']
            
            with col1:
                st.metric("Total Transactions", len(transactions_data))
            with col2:
                st.metric("Buy Orders", len(buys))
                st.caption(f"Total: ${sum(t.get('total', t.get('total_amount', 0)) for t in buys):,.2f}")
            with col3:
                st.metric("Sell Orders", len(sells))
                st.caption(f"Total: ${sum(t.get('total', t.get('total_amount', 0)) for t in sells):,.2f}")
        else:
            st.info("No transactions found.")
    elif trans_error:
        st.error(f"Error loading transactions: {trans_error}")
    else:
        st.info("No transaction history available.")

with tab4:
    st.subheader("📉 Performance & Analytics")
    
    # Fetch analytics
    try:
        analytics_response = requests.get(f"{API_BASE_URL}/users/{user_id}/analytics", timeout=5)
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Analytics metrics
            st.markdown("#### Portfolio Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sharpe Ratio", f"{analytics.get('sharpe_ratio', 0):.2f}", 
                         help="Risk-adjusted return (higher is better)")
            with col2:
                st.metric("Volatility", f"{analytics.get('volatility', 0):.1f}%",
                         help="Annualized portfolio volatility")
            with col3:
                st.metric("Diversification", f"{analytics.get('diversification_score', 0):.1f}%",
                         help="Portfolio diversification score (higher is better)")
            with col4:
                st.metric("Largest Position", f"{analytics.get('largest_position', 0):.1f}%",
                         help="Percentage of largest holding")
            
            st.markdown("---")
            
            # Performance history chart
            perf_response = requests.get(f"{API_BASE_URL}/users/{user_id}/performance?days=30", timeout=5)
            if perf_response.status_code == 200:
                perf_data = perf_response.json()
                snapshots = perf_data.get('snapshots', [])
                
                if snapshots:
                    st.markdown("#### 30-Day Performance")
                    
                    # Create performance chart
                    import plotly.graph_objects as go
                    
                    dates = [s['date'][:10] for s in snapshots]
                    values = [s['value'] for s in snapshots]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=dates,
                        y=values,
                        mode='lines+markers',
                        name='Portfolio Value',
                        line=dict(color='#1f77b4', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(31, 119, 180, 0.1)'
                    ))
                    
                    fig.update_layout(
                        title="Portfolio Value Over Time",
                        xaxis_title="Date",
                        yaxis_title="Value ($)",
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Returns analysis
                    if len(snapshots) >= 2:
                        first_value = snapshots[0]['value']
                        last_value = snapshots[-1]['value']
                        change = last_value - first_value
                        change_pct = (change / first_value * 100) if first_value > 0 else 0
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("30-Day Change", f"${change:,.2f}", delta=f"{change_pct:+.2f}%")
                        with col2:
                            st.metric("Starting Value", f"${first_value:,.2f}")
                        with col3:
                            st.metric("Current Value", f"${last_value:,.2f}")
                else:
                    st.info("Performance history will appear after multiple syncs. Run periodic syncs to track performance over time.")
            else:
                st.warning("Could not load performance history")
        else:
            st.warning("Analytics not available. Ensure you have holdings and syncs.")
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

with tab5:
    st.subheader("⚙️ Manage Holdings")
    
    st.markdown("#### Add New Holding")
    
    with st.form("add_holding_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            ticker = st.text_input("Ticker Symbol", placeholder="AAPL").upper()
            quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.01)
        
        with col2:
            purchase_price = st.number_input("Purchase Price ($)", min_value=0.01, value=100.0, step=0.01)
            purchase_date = st.date_input("Purchase Date", value=datetime.now())
        
        submit = st.form_submit_button("➕ Add Holding", type="primary")
        
        if submit and ticker:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/users/{user_id}/holdings",
                    json={
                        "ticker": ticker,
                        "quantity": quantity,
                        "purchase_price": purchase_price,
                        "purchase_date": purchase_date.isoformat()
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    st.success(f"✅ Added {quantity} shares of {ticker}")
                    st.rerun()
                else:
                    st.error(f"Failed to add holding: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Manual sync section
    st.markdown("#### Update Prices")
    
    if st.button("🔄 Update Current Prices", help="Fetch latest prices for all holdings"):
        try:
            response = requests.post(
                f"{API_BASE_URL}/users/{user_id}/sync/prices",
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Updated prices for {result.get('updated_holdings', 0)} holdings")
                st.rerun()
            else:
                st.error("Failed to update prices")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.markdown("---")

# Footer with last update time
if portfolio_data:
    last_sync = portfolio_data.get('last_sync')
    if last_sync:
        st.caption(f"Last synced: {last_sync}")
    st.caption("Portfolio Tab | Connected to Database ✅")
    st.caption("💡 Powered by Orchestrator, Market, Strategy, Portfolio Coach, Risk Profiler, Educator & Compliance Agents")
