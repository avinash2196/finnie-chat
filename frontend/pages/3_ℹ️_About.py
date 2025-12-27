"""
About Page - Global overview and agents list
"""
import streamlit as st

st.set_page_config(page_title="ℹ️ About", page_icon="ℹ️", layout="wide")

st.title("ℹ️ About Finnie Chat")
st.markdown("Finnie Chat is an AI-powered financial assistant built with FastAPI + Streamlit.")

st.markdown("---")

st.subheader("Agents (9 Specialized)")
st.markdown(
    """
- 🧭 **Orchestrator** — intelligently routes requests to specialized agents
- 🎓 **Educator** — explains financial concepts via RAG-backed knowledge base
- 🏦 **Market** — real-time quotes, market data, and trends
- 🎯 **Portfolio Coach** — analyzes diversification and allocation
- 🔎 **Risk Profiler** — assesses portfolio risk and volatility
- 📈 **Strategy** — identifies investment opportunities (dividend, growth, value)
- 🎯 **Goal Planning** — assists with financial goal-setting and retirement planning
- 📰 **News Synthesizer** — summarizes and contextualizes financial news
- 💰 **Tax Education** — explains tax concepts and account types
- ✅ **Compliance** — applies safety guardrails and regulatory disclaimers
    """
)

st.subheader("System Overview")
st.markdown(
    """
- **Backend**: FastAPI with multi-agent orchestration + enterprise observability (Arize AI, LangSmith)
- **Frontend**: Streamlit multipage UI (Chat, Portfolio, Market Trends, About)
- **Database**: SQLAlchemy ORM with SQLite (dev) or PostgreSQL (production)
- **Data Sources**: Portfolio DB, MCP servers (market, portfolio), yFinance API
- **Analytics**: Sharpe ratio, volatility, diversification scoring
- **RAG**: TF-IDF retrieval with source attribution and verification
- **LLM Gateway**: Multi-provider (OpenAI primary, Gemini/Anthropic fallback) with caching
    """
)

st.subheader("Documentation Links")
st.markdown(
    """
- [API Docs (FastAPI)](http://localhost:8000/docs)
- [Architecture](https://github.com/avinash2196/finnie-chat/blob/main/docs/architecture/ARCHITECTURE.md)
- [Implementation Guide](https://github.com/avinash2196/finnie-chat/blob/main/docs/implementation/IMPLEMENTATION_GUIDE.md)
- [Database Guide](https://github.com/avinash2196/finnie-chat/blob/main/docs/architecture/DATABASE_GUIDE.md)
- [Observability Guide](https://github.com/avinash2196/finnie-chat/blob/main/docs/architecture/OBSERVABILITY.md)
    """
)

st.markdown("---")
st.caption("Finnie Chat | Orchestrator + 9 Specialized Agents | Enterprise-Ready Financial AI")
