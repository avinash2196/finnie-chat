import asyncio
import json
import logging
from app.llm import call_llm
from app.observability import observability
from app.intent import classify_intent
from app.agents.educator import run as educator_run
from app.agents.market import run as market_run
from app.agents.risk_profiler import run as risk_profiler_run
from app.agents.portfolio_coach import run as portfolio_coach_run
from app.agents.strategy import run as strategy_run
from app.agents.compliance import run as compliance_run
from app.agents.goal_planning import run as goal_planning_run
from app.agents.news_synthesizer import run as news_synthesizer_run
from app.agents.tax_education import run as tax_education_run
from app.mcp.portfolio import get_portfolio_client as _get_portfolio_client


def get_portfolio_client(user_id: str):
    """Compatibility wrapper retained for tests that patch this symbol."""
    return _get_portfolio_client(user_id)


async def acall_llm(system_prompt: str, user_prompt: str, temperature: float = 0.0):
    """Async compatibility wrapper over synchronous call_llm."""
    return await asyncio.to_thread(
        call_llm,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
    )


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
- GoalPlanningAgent: Assists with financial goal-setting and planning
- NewsSynthesizerAgent: Summarizes and contextualizes financial news
- TaxEducationAgent: Explains tax concepts and account types

Rules:
- For ASK_CONCEPT: EducatorAgent is REQUIRED
- For ASK_MARKET: MarketAgent is REQUIRED
- For ASK_PORTFOLIO (diversification, allocation, analysis): PortfolioCoachAgent
- For ASK_RISK (volatility, risk assessment): RiskProfilerAgent
- For ASK_STRATEGY (investment opportunities, screening): StrategyAgent
- For ASK_GOAL (goal planning, retirement targets): GoalPlanningAgent
- For ASK_NEWS (summarize news or market commentary): NewsSynthesizerAgent
- For ASK_TAX (tax questions, account types): TaxEducationAgent
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
def handle_message(message: str, conversation_context: str = "", user_id: str = "user_123", root_run_id: str | None = None):
    """Sync/async-compatible entry point.

    - In async contexts, returns a coroutine and should be awaited.
    - In sync contexts, runs the coroutine to completion and returns the tuple.
    """
    try:
        asyncio.get_running_loop()
        return _handle_message_async(
            message,
            conversation_context=conversation_context,
            user_id=user_id,
            root_run_id=root_run_id,
        )
    except RuntimeError:
        return asyncio.run(
            _handle_message_async(
                message,
                conversation_context=conversation_context,
                user_id=user_id,
                root_run_id=root_run_id,
            )
        )


async def _handle_message_async(message: str, conversation_context: str = "", user_id: str = "user_123", root_run_id: str | None = None):
    """
    Full agentic orchestration with support for all 6 agents and Portfolio MCP.

    Args:
        message: Current user message
        conversation_context: Recent conversation history for context-aware responses
        user_id: User identifier for portfolio data (default: demo user)
    """

    # 1. Intent + Risk classification (LLM-based)
    # LangSmith child run: IntentClassifier
    run_intent_id = observability.start_langsmith_run(
        name="IntentClassifier",
        run_type="chain",
        inputs={"message": message},
        parent_run_id=root_run_id,
        tags=["intent", "classifier"],
    )
    intent, risk = classify_intent(message)
    observability.end_langsmith_run(
        run_id=run_intent_id,
        outputs={"intent": intent, "risk": risk},
        metadata_update={"request_type": intent},
    )

    # 2. Ask LLM to plan which agents to use (with context)
    context_info = f"Conversation history:\n{conversation_context}\n\n" if conversation_context else ""
    # Ask LLM to plan which agents to use (with context). Use a safe fallback if LLM is unavailable.
    # LangSmith child run: AgentRouter
    run_router_id = observability.start_langsmith_run(
        name="AgentRouter",
        run_type="chain",
        inputs={"message": message, "intent": intent, "context": conversation_context},
        parent_run_id=root_run_id,
        tags=["router"],
    )
    try:
        plan_json = await acall_llm(
            system_prompt=PLANNER_PROMPT,
            user_prompt=f"{context_info}User message: {message}\nIntent: {intent}",
            temperature=0,
        )
        plan = json.loads(plan_json)["plan"]
    except Exception:
        # Fail safe: default to appropriate agent based on intent
        if intent == "ASK_CONCEPT":
            plan = ["EducatorAgent", "ComplianceAgent"]
        elif intent == "ASK_MARKET":
            plan = ["MarketAgent", "ComplianceAgent"]
        elif intent == "ASK_GOAL":
            plan = ["GoalPlanningAgent", "ComplianceAgent"]
        elif intent == "ASK_NEWS":
            plan = ["NewsSynthesizerAgent", "ComplianceAgent"]
        elif intent == "ASK_TAX":
            plan = ["TaxEducationAgent", "ComplianceAgent"]
        elif intent == "ASK_PORTFOLIO":
            plan = ["PortfolioCoachAgent", "ComplianceAgent"]
        elif intent == "ASK_RISK":
            plan = ["RiskProfilerAgent", "ComplianceAgent"]
        elif intent == "ASK_STRATEGY":
            plan = ["StrategyAgent", "ComplianceAgent"]
        else:
            plan = ["EducatorAgent", "ComplianceAgent"]
    finally:
        observability.end_langsmith_run(
            run_id=run_router_id,
            outputs={"plan": plan},
        )

    # 3. Fetch holdings once when portfolio-dependent agents are in the plan.
    holdings_dependent_steps = {"RiskProfilerAgent", "PortfolioCoachAgent", "StrategyAgent"}
    shared_holdings = None
    if any(step in holdings_dependent_steps for step in plan):
        try:
            portfolio_client = get_portfolio_client(user_id)
            portfolio_result = portfolio_client.get_holdings()
            shared_holdings = portfolio_result.get("holdings") or {}
        except Exception:
            shared_holdings = None

    # 4. Execute agents concurrently (ComplianceAgent is always run last, synchronously)
    # Each agent call runs in a thread pool via asyncio.to_thread so blocking LLM I/O
    # does not stall the event loop. Independent agents execute in parallel.
    async def _run_step(step: str) -> tuple[str, object]:
        """Run one agent step in a thread pool; return (context_key, result)."""
        run_step_id = observability.start_langsmith_run(
            name=step,
            run_type="chain",
            inputs={"message": message, "user_id": user_id},
            parent_run_id=root_run_id,
            tags=["agent", step],
        )
        try:
            if step == "EducatorAgent":
                result = await asyncio.to_thread(educator_run, message)
                return "educator", result
            elif step == "MarketAgent":
                result = await asyncio.to_thread(market_run, message)
                return "market", result
            elif step == "RiskProfilerAgent":
                result = await asyncio.to_thread(
                    risk_profiler_run,
                    message,
                    holdings_dict=shared_holdings,
                    user_id=user_id,
                )
                return "risk_analysis", result
            elif step == "GoalPlanningAgent":
                result = await asyncio.to_thread(goal_planning_run, message, user_id)
                return "goal_plan", result
            elif step == "NewsSynthesizerAgent":
                result = await asyncio.to_thread(news_synthesizer_run, message, user_id)
                return "news_summary", result
            elif step == "TaxEducationAgent":
                result = await asyncio.to_thread(tax_education_run, message, user_id)
                return "tax_education", result
            elif step == "PortfolioCoachAgent":
                result = await asyncio.to_thread(
                    portfolio_coach_run,
                    message,
                    holdings_dict=shared_holdings,
                    user_id=user_id,
                )
                return "portfolio_analysis", result
            elif step == "StrategyAgent":
                strategy_type = "balanced"
                m_lower = message.lower()
                if "dividend" in m_lower:
                    strategy_type = "dividend"
                elif "growth" in m_lower:
                    strategy_type = "growth"
                elif "value" in m_lower:
                    strategy_type = "value"
                result = await asyncio.to_thread(
                    strategy_run,
                    message,
                    shared_holdings,
                    strategy_type,
                    user_id,
                )
                return "strategy", result
            return step, None
        finally:
            observability.end_langsmith_run(
                run_id=run_step_id,
                outputs={"context_keys": [step]},
            )

    context = {}
    non_compliance_steps = [s for s in plan if s != "ComplianceAgent"]
    step_results = await asyncio.gather(
        *[_run_step(s) for s in non_compliance_steps],
        return_exceptions=True,
    )
    # Surface failures from parallel agent execution instead of dropping them silently.
    logger = logging.getLogger(__name__)
    for item in step_results:
        if isinstance(item, Exception):
            logger.exception("agent_step_failed", exc_info=item)
            context.setdefault("agent_errors", []).append(str(item))
            continue
        if isinstance(item, tuple):
            key, val = item
            if val is not None:
                context[key] = val

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

Goal planning:
{context.get("goal_plan") or "(Not requested)"}

News summary:
{context.get("news_summary") or "(Not requested)"}

Tax education:
{context.get("tax_education") or "(Not requested)"}

User question:
{message}

Provide a clear, beginner-friendly response synthesizing all available information.
"""

    # Try LLM synthesis; on failure produce a grounded fallback summary from agent outputs
    run_synth_id = observability.start_langsmith_run(
        name="FinalResponseComposer",
        run_type="chain",
        inputs={"message": message, "context_keys": list(context.keys())},
        parent_run_id=root_run_id,
        tags=["composer"],
    )
    try:
        draft_response = await acall_llm(
            system_prompt="You explain finance concepts clearly and safely using only provided information.",
            user_prompt=synthesis_prompt,
            temperature=0.3,
        )
    except Exception:
        parts = []
        if context.get("educator"):
            parts.append(f"Educator:\n{context['educator']}")
        if context.get("market"):
            parts.append(f"Market:\n{context['market']}")
        if context.get("portfolio_analysis"):
            parts.append(f"Portfolio Analysis:\n{context['portfolio_analysis']}")
        if context.get("risk_analysis"):
            parts.append(f"Risk Analysis:\n{context['risk_analysis']}")
        if context.get("strategy"):
            parts.append(f"Strategy:\n{context['strategy']}")

        if parts:
            draft_response = "\n\n".join(parts)
        else:
            draft_response = "I don't have enough information to synthesize an answer right now."
    finally:
        observability.end_langsmith_run(
            run_id=run_synth_id,
            outputs={"draft_length": len(draft_response) if isinstance(draft_response, str) else 0}
        )

    # 7. Compliance Agent (always last)
    final_response = compliance_run(draft_response, risk)

    return final_response, intent, risk

