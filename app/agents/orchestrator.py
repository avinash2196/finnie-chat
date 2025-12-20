import json
from app.llm import call_llm
from app.intent import classify_intent
from app.agents.educator import run as educator_run
from app.agents.market import run as market_run
from app.agents.risk_profiler import run as risk_profiler_run
from app.agents.portfolio_coach import run as portfolio_coach_run
from app.agents.strategy import run as strategy_run
from app.agents.compliance import run as compliance_run
from app.mcp.portfolio import get_portfolio_client


# LLM PLANNER PROMPT
# -------------------------
PLANNER_PROMPT = """
You are an AI orchestrator for a financial AI assistant.

Your job:
- Decide which agents must be called to answer the user question safely.
- Consider conversation history for context.

Available agents:
- EducatorAgent: Explains financial concepts using trusted knowledge (RAG)
- MarketAgent: Fetches live market data (stocks, prices, trends)
- RiskProfilerAgent: Analyzes portfolio risk and volatility
- PortfolioCoachAgent: Analyzes diversification and allocation
- StrategyAgent: Identifies investment opportunities (dividend/growth/value)
- ComplianceAgent: Final safety and disclaimer check (must always be last)

Rules:
- For ASK_CONCEPT: EducatorAgent is REQUIRED
- For ASK_MARKET: MarketAgent is REQUIRED
- For ASK_PORTFOLIO (diversification, allocation, analysis): PortfolioCoachAgent
- For ASK_RISK (volatility, risk assessment): RiskProfilerAgent
- For ASK_STRATEGY (investment opportunities, screening): StrategyAgent
- For questions combining multiple topics, use multiple agents
- ComplianceAgent must always be last
- Use conversation history to provide context-aware responses

Respond ONLY in valid JSON:
{
  "plan": ["EducatorAgent", "MarketAgent", "ComplianceAgent"]
}
"""


# MAIN ORCHESTRATION FUNCTION
# --------------------------------
def handle_message(message: str, conversation_context: str = "", user_id: str = "user_123"):
    """
    Full agentic orchestration with support for all 6 agents and Portfolio MCP.
    
    Args:
        message: Current user message
        conversation_context: Recent conversation history for context-aware responses
        user_id: User identifier for portfolio data (default: demo user)
    """

    # 1. Intent + Risk classification (LLM-based)
    intent, risk = classify_intent(message)

    # 2. Ask LLM to plan which agents to use (with context)
    context_info = f"Conversation history:\n{conversation_context}\n\n" if conversation_context else ""
    plan_json = call_llm(
        system_prompt=PLANNER_PROMPT,
        user_prompt=f"{context_info}User message: {message}\nIntent: {intent}",
        temperature=0
    )

    try:
        plan = json.loads(plan_json)["plan"]
    except Exception:
        # Fail safe: default to appropriate agent based on intent
        if intent == "ASK_CONCEPT":
            plan = ["EducatorAgent", "ComplianceAgent"]
        elif intent == "ASK_MARKET":
            plan = ["MarketAgent", "ComplianceAgent"]
        elif intent == "ASK_PORTFOLIO":
            plan = ["PortfolioCoachAgent", "ComplianceAgent"]
        elif intent == "ASK_RISK":
            plan = ["RiskProfilerAgent", "ComplianceAgent"]
        elif intent == "ASK_STRATEGY":
            plan = ["StrategyAgent", "ComplianceAgent"]
        else:
            plan = ["EducatorAgent", "ComplianceAgent"]

    # 3. Get user's portfolio data (for portfolio agents)
    portfolio_client = get_portfolio_client(user_id)
    portfolio_result = portfolio_client.get_holdings()
    holdings_dict = portfolio_result.get('holdings', {})

    # 4. Execute agents in plan
    context = {}

    for step in plan:
        if step == "EducatorAgent":
            context["educator"] = educator_run(message)

        elif step == "MarketAgent":
            context["market"] = market_run(message)

        elif step == "RiskProfilerAgent":
            # Risk Profiler analyzes volatility and Sharpe ratio
            context["risk_analysis"] = risk_profiler_run(message, user_id=user_id)

        elif step == "PortfolioCoachAgent":
            # Portfolio Coach analyzes diversification and allocation
            context["portfolio_analysis"] = portfolio_coach_run(message, user_id=user_id)

        elif step == "StrategyAgent":
            # Strategy agent identifies opportunities (dividend/growth/value)
            # Auto-detect strategy type from message
            strategy_type = "balanced"  # default
            if "dividend" in message.lower():
                strategy_type = "dividend"
            elif "growth" in message.lower():
                strategy_type = "growth"
            elif "value" in message.lower():
                strategy_type = "value"
            
            context["strategy"] = strategy_run(message, strategy_type=strategy_type, user_id=user_id)

    # 5. HARD GUARD: For ASK_CONCEPT, RAG MUST exist
    if intent == "ASK_CONCEPT":
        if not context.get("educator"):
            return (
                "I don't have enough trusted information to answer that right now.",
                intent,
                risk
            )

    # 6. LLM SYNTHESIS (STRICTLY GROUNDED)
    synthesis_prompt = f"""
You are a financial AI assistant with access to multiple specialized agents.

You MUST follow these rules:
- Use ONLY the information provided below.
- Do NOT add new concepts.
- Do NOT generalize beyond what agents provided.
- Do NOT use outside knowledge.
- If information is missing, say: "I don't have enough information."
- Consider conversation history to provide coherent, context-aware responses.
- Synthesize multiple agent outputs into a single coherent response.

Conversation history:
{conversation_context or "(No prior conversation)"}

Available information:

Trusted educator information:
{context.get("educator") or "(Not requested)"}

Market data:
{context.get("market") or "(Not requested)"}

Portfolio analysis:
{context.get("portfolio_analysis") or "(Not requested)"}

Risk analysis:
{context.get("risk_analysis") or "(Not requested)"}

Strategy recommendations:
{context.get("strategy") or "(Not requested)"}

User question:
{message}

Provide a clear, beginner-friendly response synthesizing all available information.
"""

    draft_response = call_llm(
        system_prompt="You explain finance concepts clearly and safely using only provided information.",
        user_prompt=synthesis_prompt,
        temperature=0.3
    )

    # 7. Compliance Agent (always last)
    final_response = compliance_run(draft_response, risk)

    return final_response, intent, risk

