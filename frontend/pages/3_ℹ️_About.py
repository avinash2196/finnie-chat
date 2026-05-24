"""
About Page - Global overview and agents list
"""
import streamlit as st

st.set_page_config(page_title="â„¹ï¸ About", page_icon="â„¹ï¸", layout="wide")

st.title("â„¹ï¸ About Finnie Chat")
st.markdown("Finnie Chat is an AI-powered financial assistant built with FastAPI + Streamlit.")

st.markdown("---")

st.subheader("Agents (9 Specialized)")
st.markdown(
    """
- ðŸ§­ **Orchestrator** â€” intelligently routes requests to specialized agents
- ðŸŽ“ **Educator** â€” explains financial concepts via RAG-backed knowledge base
- ðŸ¦ **Market** â€” real-time quotes, market data, and trends
- ðŸŽ¯ **Portfolio Coach** â€” analyzes diversification and allocation
- ðŸ”Ž **Risk Profiler** â€” assesses portfolio risk and volatility
- ðŸ“ˆ **Strategy** â€” identifies investment opportunities (dividend, growth, value)
- ðŸŽ¯ **Goal Planning** â€” assists with financial goal-setting and retirement planning
- ðŸ“° **News Synthesizer** â€” summarizes and contextualizes financial news
- ðŸ’° **Tax Education** â€” explains tax concepts and account types
- âœ… **Compliance** â€” applies safety guardrails and regulatory disclaimers
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
