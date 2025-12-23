"""
Finnie Chat - Financial AI Assistant Frontend
Main Streamlit app with chat interface
"""
import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="💬 Finnie Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"  # Default user

# Sidebar
with st.sidebar:
    st.title("💬 Finnie Chat")
    st.markdown("---")
    
    # User settings
    st.subheader("Settings")
    st.session_state.user_id = st.text_input(
        "User ID", 
        value=st.session_state.user_id,
        help="Enter your user ID for portfolio tracking"
    )
    
    st.markdown("---")
    
    # System status
    st.subheader("System Status")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("🟢 Backend Connected")
        else:
            st.error("🔴 Backend Error")
    except:
        st.error("🔴 Backend Offline")
    
    st.markdown("---")
    
    # Clear conversation
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **Finnie Chat** is your AI-powered financial assistant with:
        
        - 💬 **Chat**: Ask financial questions
        - 📊 **Portfolio**: Track your investments
        - 📈 **Market**: Real-time market data
        
        Built with FastAPI + Streamlit
        """)

# Main chat interface
st.title("💬 Chat with Finnie")
st.markdown("Ask me about stocks, portfolio analysis, risk assessment, or financial concepts!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"_{message['timestamp']}_")

# Chat input
if prompt := st.chat_input("Ask about your portfolio, stocks, or financial concepts..."):
    # Add user message to chat
    timestamp = datetime.now().strftime("%I:%M %p")
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": timestamp
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"_{timestamp}_")
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call backend API
                response = requests.post(
                    f"{API_BASE_URL}/chat",
                    json={
                        "message": prompt,
                        "user_id": st.session_state.user_id,
                        "conversation_id": "default"
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "Sorry, I couldn't generate a response.")
                    
                    # Display response
                    st.markdown(reply)
                    response_time = datetime.now().strftime("%I:%M %p")
                    st.caption(f"_{response_time}_")
                    
                    # Add to session state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": reply,
                        "timestamp": response_time
                    })
                else:
                    error_msg = f"❌ Error: Backend returned status {response.status_code}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })
                    
            except requests.exceptions.ConnectionError:
                error_msg = "❌ Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
            except requests.exceptions.Timeout:
                error_msg = "⏱️ Request timed out. The server might be processing a complex query."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
            except Exception as e:
                error_msg = f"❌ Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })

# Example prompts
if not st.session_state.messages:
    st.markdown("### 💡 Try asking:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Portfolio Questions**\n\n- How is my portfolio diversified?\n- What's my risk level?\n- Analyze my holdings")
    
    with col2:
        st.info("📈 **Market Queries**\n\n- What's the price of AAPL?\n- Show me tech stock trends\n- Market overview today")
    
    with col3:
        st.info("🎓 **Learn Finance**\n\n- What is a dividend?\n- Explain P/E ratio\n- How do bonds work?")

# Footer
st.markdown("---")
st.caption("Finnie Chat v1.0 | Powered by FastAPI + OpenAI | Built with ❤️")
