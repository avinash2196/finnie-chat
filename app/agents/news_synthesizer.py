"""News Synthesizer Agent

Summarizes and contextualizes financial news with:
- Tool: news fetcher (Alpha Vantage API via MCP server) + recency filter
- Output: bullet summary + "what it means" + citations + timestamp
- Compliance: refuses "what should I buy today?" without strong disclaimers
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
import re
import logging
from app.mcp.news import get_client as get_news_client
from app.observability import observability

logger = logging.getLogger(__name__)


def run(message: str, user_id: Optional[str] = None, max_sentences: Optional[int] = 3) -> str:
    """Synthesize and contextualize financial news.

    Output: bullet summary + "what it means" + citations + timestamp
    Must: refuse if user asks for "what should I buy today?" without disclaimers
    """
    if not message:
        return "Please provide a news snippet or ask about financial news (e.g., 'Summarize Apple earnings')"

    msg = message.lower()

    # COMPLIANCE GATE: Refuse buy/sell recommendations
    if any(kw in msg for kw in ["should i buy", "should i sell", "what should i buy today"]):
        return (
            "⚠️ **COMPLIANCE GATE**: I cannot recommend specific buy/sell actions.\n\n"
            "However, I can help you:\n"
            "- Summarize news and its market impact\n"
            "- Explain what the news means for your portfolio\n"
            "- Suggest educational resources on investment strategies\n\n"
            "**Disclaimer**: Always consult a licensed financial advisor before making investment decisions."
        )

    # Try MCP news fetch if tickers present
    # Extract potential tickers (1-5 uppercase letters)
    potential_tickers = re.findall(r"\b([A-Z]{1,5})\b", (message or "").upper())
    potential_tickers = [t for t in potential_tickers if t.isalpha()]
    
    # Filter out common English words that look like tickers
    COMMON_WORDS = {'SHOW', 'ME', 'WHAT', 'ARE', 'THE', 'FOR', 'NEWS', 'GIVE', 'GET', 'TELL', 
                    'ABOUT', 'LATEST', 'TODAY', 'NOW', 'MARKET', 'STOCK', 'STOCKS', 'ANY', 
                    'SOME', 'THIS', 'THAT', 'WITH', 'FROM', 'HAVE', 'HAS', 'HAD', 'WILL',
                    'CAN', 'COULD', 'SHOULD', 'WOULD', 'WHAT', 'WHERE', 'WHEN', 'WHO', 'HOW',
                    'ON', 'IN', 'AT', 'TO', 'OF', 'AND', 'OR', 'BUT', 'IF', 'THEN', 'ELSE'}
    tickers = [t for t in potential_tickers if t not in COMMON_WORDS]

    logger.info(f"[NEWS_AGENT] Extracted tickers: {tickers} (filtered from {potential_tickers})")

    articles: List = []
    client = get_news_client()
    
    if tickers:
        try:
            logger.info(f"[NEWS_AGENT] Calling MCP news client for {len(tickers)} tickers")
            articles = client.get_news(tickers, limit=max_sentences or 3)
            logger.info(f"[NEWS_AGENT] MCP returned {len(articles)} articles")
            observability.track_event("news_mcp_fetch", {"ticker_count": len(tickers), "article_count": len(articles)})
            
            # If ticker-specific search returns nothing, try general news
            if not articles:
                logger.info(f"[NEWS_AGENT] No articles for tickers, trying general news")
                articles = client.get_general_news(limit=max_sentences or 3)
                logger.info(f"[NEWS_AGENT] General news returned {len(articles)} articles")
                observability.track_event("news_mcp_general_fallback", {"original_ticker_count": len(tickers), "article_count": len(articles)})
        except Exception as e:
            logger.error(f"[NEWS_AGENT] MCP call failed: {e}")
            observability.track_event("news_mcp_failure", {"error": str(e)})
            articles = []
    else:
        # No tickers found - fetch general market headlines
        logger.info(f"[NEWS_AGENT] No tickers found, fetching general market headlines")
        try:
            articles = client.get_general_news(limit=max_sentences or 3)
            logger.info(f"[NEWS_AGENT] MCP returned {len(articles)} general headlines")
            observability.track_event("news_mcp_general_fetch", {"article_count": len(articles)})
        except Exception as e:
            logger.error(f"[NEWS_AGENT] MCP general news call failed: {e}")
            observability.track_event("news_mcp_general_failure", {"error": str(e)})
            articles = []

    if articles:
        logger.info(f"[NEWS_AGENT] Using MCP articles path")
        # Build summary from fetched articles
        bullets = []
        for a in articles[: (max_sentences or 3)]:
            title = (a.title or "Untitled").strip()
            src = f" ({a.source})" if a.source else ""
            tp = f" — {a.time_published}" if a.time_published else ""
            bullets.append(f"- {title}{src}{tp}")
        summary = "\n".join(bullets)
        cited = sorted({sym for a in articles for sym in (a.tickers or [])})
        ticker_str = ", ".join(cited[:5]) if cited else ", ".join(sorted(set(tickers[:3])))
        what_it_means = (
            "**What It Means**: "
            "Recent articles may shift sentiment and highlight risks/opportunities. "
            "Review relevance to your holdings and strategy."
        )
    else:
        logger.warning(f"[NEWS_AGENT] No MCP articles, using fallback text summarization")
        observability.track_event("news_fallback", {"ticker_count": len(tickers)})
        # Fallback: summarize provided text
        sentences = [s.strip() for s in (message or "").split('.') if s.strip()]
        if len(sentences) == 0:
            logger.warning(f"[NEWS_AGENT] No sentences extracted from message")
            return "No news content found. Please paste a news snippet or describe an event."
        summary_sentences = sentences[: (max_sentences or 3)]
        summary = ". ".join(summary_sentences) + "."
        ticker_str = ", ".join(sorted(set(tickers[:3]))) if tickers else "N/A"
        what_it_means = (
            "**What It Means**: "
            "This news could impact market sentiment, company valuations, and portfolio allocations. "
            "Consider whether this affects your holdings or investment strategy."
        )

    # Response with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    response = f"""
**News Summary**:
{summary}

{what_it_means}

**Citations**: {ticker_str}
**Timestamp**: {timestamp}

**Note**: If articles were fetched, they are via Alpha Vantage NEWS_SENTIMENT.
For latest market news, check Bloomberg, Reuters, or your brokerage.
"""
    return response.strip()
