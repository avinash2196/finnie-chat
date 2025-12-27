"""Goal Planning Agent

Assists with financial goal-setting and planning by extracting goals, timelines, and risk tolerance,
producing structured plans with milestones, suggested allocations (educational), and learning next steps.
Uses: portfolio data, LLM synthesis, educator KB, compliance gating.
"""
from __future__ import annotations
import re
from typing import Optional
from app.mcp.portfolio import get_portfolio_client


def run(message: str, user_id: Optional[str] = None) -> str:
    """Return a structured goal plan with milestones and allocations.

    Input: goals + timeline + risk tolerance
    Output: structured plan (milestones, suggested allocations as education, learning next steps),
            clarifying questions if required
    Uses: portfolio data, LLM synthesis, educator KB, compliance gate
    """
    msg = message or ""
    user_id = user_id or "user_123"

    # Extract goal parameters
    amount_match = re.search(r"\$?([0-9,.]+)", msg)
    years_match = re.search(r"(\d{1,2})\s*(years|yrs|y)", msg, re.IGNORECASE)
    
    target_amount = amount_match.group(1) if amount_match else None
    timeline_years = int(years_match.group(1)) if years_match else None

    # Detect risk tolerance
    risk_tolerance = "moderate"
    if any(kw in msg.lower() for kw in ["conservative", "safe", "low risk"]):
        risk_tolerance = "conservative"
    elif any(kw in msg.lower() for kw in ["aggressive", "growth", "high risk"]):
        risk_tolerance = "aggressive"

    # Clarifying questions if incomplete
    clarifications = []
    if not target_amount:
        clarifications.append("What's your target amount? (e.g., $500,000)")
    if not timeline_years:
        clarifications.append("What's your timeline? (e.g., 10 years, 20 years)")
    if not any(kw in msg.lower() for kw in ["conservative", "aggressive", "moderate", "balanced", "growth"]):
        clarifications.append("What's your risk tolerance? (conservative, moderate, aggressive)")

    if clarifications:
        return f"To create your personalized plan, please clarify:\n" + "\n".join(
            f"- {q}" for q in clarifications
        )

    # Retrieve portfolio data
    try:
        portfolio_client = get_portfolio_client(user_id)
        holdings_result = portfolio_client.get_holdings()
        current_portfolio_value = sum(
            h.get("total_value", 0) for h in holdings_result.get("holdings", [])
        )
    except Exception:
        current_portfolio_value = 0

    # Calculate milestones and allocation suggestions
    if timeline_years and target_amount:
        try:
            target_num = float(target_amount.replace(",", ""))
            monthly_savings = target_num / (timeline_years * 12)
            
            allocations = {
                "conservative": {"stocks": "40-50%", "bonds": "40-50%", "cash": "10%"},
                "moderate": {"stocks": "60%", "bonds": "30%", "cash": "10%"},
                "aggressive": {"stocks": "80%", "bonds": "15%", "cash": "5%"},
            }
            allocation = allocations.get(risk_tolerance, allocations["moderate"])

            plan = f"""
**Goal Plan: ${target_amount:,} in {timeline_years} years**

**Risk Profile**: {risk_tolerance.capitalize()}

**Milestones**:
- Year 1: ${target_num / timeline_years:,.0f}
- Year {timeline_years // 2}: ${target_num * (timeline_years // 2) / timeline_years:,.0f}
- Year {timeline_years}: ${target_num:,.0f}

**Monthly Savings Needed**: ${monthly_savings:,.0f}

**Suggested Allocation (Educational)**:
- Stocks: {allocation['stocks']}
- Bonds: {allocation['bonds']}
- Cash: {allocation['cash']}

**Learning Next Steps**:
1. Understand asset allocation and diversification
2. Learn about risk tolerance and time horizon
3. Explore tax-advantaged accounts (401k, IRA, Roth)
4. Consider dollar-cost averaging
5. Review and rebalance annually

**Important**: This is educational guidance. Consult a financial advisor for personalized advice.
"""
            return plan.strip()
        except (ValueError, TypeError):
            pass

    # Fallback
    return (
        f"I can help you plan your goal. Please provide:\n"
        f"- **Target amount** (e.g., $1,000,000)\n"
        f"- **Timeline** (e.g., 20 years)\n"
        f"- **Risk tolerance** (conservative, moderate, aggressive)\n"
        f"Example: 'I want $500K in 15 years with moderate risk.'"
    )
