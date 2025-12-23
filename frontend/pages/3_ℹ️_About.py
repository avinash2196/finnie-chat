"""
About Page - Global overview and agents list
"""
import streamlit as st

st.set_page_config(page_title="ℹ️ About", page_icon="ℹ️", layout="wide")

st.title("ℹ️ About Finnie Chat")
st.markdown("Finnie Chat is an AI-powered financial assistant built with FastAPI + Streamlit.")

st.markdown("---")

st.subheader("Agents")
st.markdown(
    """
- 🧭 **Orchestrator** — routes requests and composes answers
- 🏦 **Market** — quotes, movers, sectors
- 🧮 **Strategy** — screeners and investment ideas
- 🎯 **Portfolio Coach** — improvement suggestions
- 🔎 **Risk Profiler** — risk analysis from holdings
- 🎓 **Educator** — RAG-backed explanations
- ✅ **Compliance** — safe outputs & disclaimers
    """
)

st.subheader("System Overview")
st.markdown(
    """
- Backend: FastAPI + SQLAlchemy (SQLite dev)
- Frontend: Streamlit multipage UI
- Data: Portfolio DB, MCP servers (market, portfolio)
- Analytics: Sharpe ratio, volatility, diversification
- RAG: TF-IDF retrieval with verification
    """
)

st.subheader("Documentation Links")
st.markdown(
    """
- [API Docs (FastAPI)](http://localhost:8000/docs)
- [Architecture](https://github.com/your-org/your-repo/blob/main/ARCHITECTURE.md)
- [Implementation Guide](https://github.com/your-org/your-repo/blob/main/finnie-chat/IMPLEMENTATION_GUIDE.md)
- [Database Guide](https://github.com/your-org/your-repo/blob/main/finnie-chat/DATABASE_GUIDE.md)
- [Feature Summary](https://github.com/your-org/your-repo/blob/main/finnie-chat/FEATURE_COMPLETION_SUMMARY.md)
    """
)

st.markdown("---")
st.caption("Finnie Chat | Orchestrator + 6 Specialized Agents")
