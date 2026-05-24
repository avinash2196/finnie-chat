"""
Finnie Chat - Financial AI Assistant Frontend
Main Streamlit app with chat interface
"""
import streamlit as st
import requests
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="ðŸ’¬ Finnie Chat",
    page_icon="ðŸ’¬",
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
    st.title("ðŸ’¬ Finnie Chat")
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
            st.success("ðŸŸ¢ Backend Connected")
        else:
            st.error("ðŸ”´ Backend Error")
    except:
        st.error("ðŸ”´ Backend Offline")

    st.markdown("---")

    # Clear conversation
    if st.button("ðŸ—‘ï¸ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    # About
    with st.expander("â„¹ï¸ About"):
        st.markdown("""
        **Finnie Chat** is your AI-powered financial assistant.

        Core Pages:
        - ðŸ’¬ **Chat**: Ask financial questions
        - ðŸ“Š **Portfolio**: Track your investments
        - ðŸ“ˆ **Market**: Real-time market data

        Agents:
        - ðŸ§­ **Orchestrator** â€” intent routing and agent selection
        - ðŸ¦ **Market** â€” live quotes and market intel
        - ðŸ§® **Strategy** â€” screeners and investment ideas
        - ðŸŽ¯ **Portfolio Coach** â€” improvement suggestions
        - ðŸ”Ž **Risk Profiler** â€” risk assessment from holdings
        - ðŸŽ“ **Educator** â€” concept explanations via RAG
        - âœ… **Compliance** â€” safe outputs and disclaimers

        Built with FastAPI + Streamlit
        """)

    st.markdown("---")
    with st.expander("â„¹ï¸ Agents & Docs"):
        st.markdown("""
        - ðŸ§­ **Orchestrator** â€” routes requests and composes answers
        - ðŸ¦ **Market** â€” quotes, movers, sectors
        - ðŸ§® **Strategy** â€” screeners and ideas
        - ðŸŽ¯ **Portfolio Coach** â€” improvement suggestions
        - ðŸ”Ž **Risk Profiler** â€” risk from holdings
        - ðŸŽ“ **Educator** â€” RAG-backed explanations
        - âœ… **Compliance** â€” safe outputs & disclaimers

        **Useful Links:**
        - [API Docs (FastAPI)](http://localhost:8000/docs)
        - [Streamlit App (Home)](http://localhost:8501)
        - [Streamlit Docs](https://docs.streamlit.io)
        - [FastAPI Docs](https://fastapi.tiangolo.com)
        """)

# Main chat interface
st.title("ðŸ’¬ Chat with Finnie")
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
                    error_msg = f"âŒ Error: Backend returned status {response.status_code}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%I:%M %p")
                    })

            except requests.exceptions.ConnectionError:
                error_msg = "âŒ Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
            except requests.exceptions.Timeout:
                error_msg = "â±ï¸ Request timed out. The server might be processing a complex query."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })
            except Exception as e:
                error_msg = f"âŒ Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%I:%M %p")
                })

# Example prompts
if not st.session_state.messages:
    st.markdown("### ðŸ’¡ Try asking:")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.info("ðŸ“Š **Portfolio**\n\n- How diversified am I?\n- What's my risk level?\n- Rebalance suggestions")

    with col2:
        st.info("ðŸ“ˆ **Market**\n\n- AAPL stock price?\n- Tech trends today?\n- Market movers?")

    with col3:
        st.info("ðŸŽ“ **Learn**\n\n- What is a dividend?\n- Explain P/E ratio\n- How do bonds work?")

    with col4:
        st.info("ðŸŽ¯ **Goals**\n\n- Retire in 20 years\n- Save $500K goal\n- Plan my finances")

    with col5:
        st.info("ðŸ“° **News**\n\n- Summarize earnings\n- Market headlines\n- News impact?")

    with col6:
        st.info("ðŸ’° **Tax**\n\n- What's a Roth IRA?\n- Capital gains tax?\n- Account types?")

# Footer
st.markdown("---")
st.caption("Finnie Chat v1.0 | Powered by FastAPI + OpenAI | Built with â¤ï¸")
