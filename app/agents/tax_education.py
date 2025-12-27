"""Tax Education Agent

Provides retrieval-only education on account types and tax concepts.
Must: ask clarifying jurisdiction (US vs other) OR default to US with clear disclaimer.
"""
from __future__ import annotations
from typing import Optional
from app.rag.store import query_rag

# US Tax Education Knowledge Base (retrieval-only)
TAX_KB_US = {
    "ira": {
        "title": "Traditional IRA",
        "description": "Individual Retirement Account (Traditional): Tax-deferred contributions (may be deductible), grows tax-free, taxed on withdrawal.",
        "limits": "2024: $7,000/year ($8,000 if age 50+)",
        "best_for": "Those who want to defer taxes now and expect lower tax bracket in retirement."
    },
    "roth": {
        "title": "Roth IRA",
        "description": "Roth IRA: After-tax contributions, grows tax-free, qualified withdrawals are 100% tax-free.",
        "limits": "2024: $7,000/year ($8,000 if age 50+). Income limits apply.",
        "best_for": "Those expecting higher income/tax bracket in retirement."
    },
    "401k": {
        "title": "401(k) Plan",
        "description": "Employer-sponsored retirement plan. Traditional: pre-tax contributions. Roth 401(k): after-tax contributions.",
        "limits": "2024: $23,500/year ($31,000 if age 50+)",
        "best_for": "Maximize employer match first, then consider Roth IRA or traditional 401(k)."
    },
    "hsa": {
        "title": "Health Savings Account (HSA)",
        "description": "Triple tax advantage: deductible contributions, tax-free growth, tax-free withdrawals for qualified medical expenses.",
        "limits": "2024: $4,150 (individual) / $8,300 (family)",
        "best_for": "High-deductible health plan (HDHP) holders seeking tax-advantaged savings."
    },
    "capital gains": {
        "title": "Capital Gains Tax",
        "short_term": "Short-term gains (held <1 year): taxed as ordinary income (10-37% federal, depending on bracket)",
        "long_term": "Long-term gains (held >1 year): preferential rates (0%, 15%, or 20% federal)",
        "best_for": "Hold investments >1 year to qualify for lower long-term capital gains rates."
    },
    "tax-loss harvesting": {
        "title": "Tax-Loss Harvesting",
        "description": "Selling securities at a loss to offset capital gains and reduce taxable income.",
        "rules": "Wash-sale rule: cannot repurchase same/substantially identical security within 30 days.",
        "best_for": "Year-end portfolio rebalancing and tax optimization."
    }
}


def run(message: str, user_id: Optional[str] = None) -> str:
    """Provide tax education on account types and concepts (retrieval-only, US-focused).

    Must: ask clarifying jurisdiction (US vs other) OR default to US with clear disclaimer.

    Args:
        message: User query on tax topics
        user_id: User ID (optional)

    Returns:
        Educational information on requested tax topic, with jurisdiction disclaimer
    """
    msg = (message or "").lower()

    # Check for jurisdiction indicators
    is_non_us = any(kw in msg for kw in ["canada", "uk", "japan", "australia", "europe", "non-us", "international"])

    # If non-US, ask for clarification
    if is_non_us:
        return (
            "📍 **Jurisdiction Notice**: Tax rules vary significantly by country.\n\n"
            "I'm trained on **US tax concepts** (IRAs, 401(k)s, capital gains, etc.).\n\n"
            "For non-US tax advice, please consult a tax professional in your jurisdiction.\n"
            "Still want general US tax education? I can help with that."
        )

    # First, query Chroma/TFIDF RAG store for trusted sources
    rag_docs = query_rag(message)

    # Search hardcoded US knowledge base for matches
    msg_lower = msg.lower()
    for key, details in TAX_KB_US.items():
        if key in msg_lower:
            response = f"""
**{details.get('title', key.upper())}**

{details.get('description', 'Educational information not available.')}
"""
            if "limits" in details:
                response += f"\n**Contribution Limits**: {details['limits']}"
            if "short_term" in details:
                response += f"\n**Short-term**: {details['short_term']}"
            if "long_term" in details:
                response += f"\n**Long-term**: {details['long_term']}"
            if "best_for" in details:
                response += f"\n**Best For**: {details['best_for']}"
            if "rules" in details:
                response += f"\n**Rules**: {details['rules']}"

            # Include trusted sources from RAG, if available
            if rag_docs and len(rag_docs) > 0 and "No documents available" not in rag_docs[0]:
                response += "\n\n**Trusted Sources (RAG)**:\n" + "\n".join(f"- {d}" for d in rag_docs[:3])

            response += f"""

📍 **Jurisdiction**: United States (US tax law)
**⚠️ Disclaimer**: This is educational information only. For personalized tax advice, consult a tax professional or CPA.
"""
            return response.strip()

    # No match found
    # No direct match found; provide US-focused overview with RAG sources
    # Prepare trusted sources text without using backslashes inside f-string expressions
    sources_text = (
        "\n".join(f"- {d}" for d in rag_docs[:3]) if rag_docs else "- Ingest KB first (data/finance_kb.txt)"
    )

    return f"""
📍 **Tax Education (US-Focused)**

I can explain these US tax concepts:
- **Accounts**: IRA, Roth IRA, 401(k), HSA
- **Taxation**: Capital gains (short-term vs long-term), tax-loss harvesting
- **Strategies**: Tax-efficient investing, account selection

Asking about: "{message.strip()}"

I didn't find a match. Try asking about:
- "What is a Roth IRA?"
- "How are capital gains taxed?"
- "What's the difference between IRA and 401k?"

**Trusted Sources (RAG)**:
{sources_text}

**⚠️ Disclaimer**: This is educational only. Consult a tax professional for personalized advice.
"""
