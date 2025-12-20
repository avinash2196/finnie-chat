import json
from app.llm import call_llm
from app.intent import classify_intent
from app.agents.educator import run as educator_run
from app.agents.market import run as market_run
from app.agents.compliance import run as compliance_run


# LLM PLANNER PROMPT
# -------------------------
PLANNER_PROMPT = """
You are an AI orchestrator for a financial education assistant.

Your job:
- Decide which agents must be called to answer the user question safely.
- Consider conversation history for context.

Available agents:
- EducatorAgent  explains financial concepts using trusted knowledge (RAG)
- MarketAgent  fetches live market data (MCP tools)
- ComplianceAgent  final safety and disclaimer check (must always be last)

Rules:
- For ASK_CONCEPT  EducatorAgent is REQUIRED.
- For ASK_MARKET  MarketAgent is REQUIRED, EducatorAgent is OPTIONAL.
- Do NOT use EducatorAgent if the user is asking only for current price or daily movement.
- ComplianceAgent must always be last.
- Use conversation history to provide context-aware responses.

Respond ONLY in valid JSON:
{
  "plan": ["EducatorAgent", "MarketAgent", "ComplianceAgent"]
}
"""


# MAIN ORCHESTRATION FUNCTION
# --------------------------------
def handle_message(message: str, conversation_context: str = ""):
    """
    Full agentic orchestration for Chat Tab with conversation memory support.
    
    Args:
        message: Current user message
        conversation_context: Recent conversation history for context-aware responses
    """

    # 1 Intent + Risk classification (LLM-based)
    intent, risk = classify_intent(message)

    # 2 Ask LLM to plan which agents to use (with context)
    context_info = f"Conversation history:\n{conversation_context}\n\n" if conversation_context else ""
    plan_json = call_llm(
        system_prompt=PLANNER_PROMPT,
        user_prompt=f"{context_info}User message: {message}\nIntent: {intent}",
        temperature=0
    )

    try:
        plan = json.loads(plan_json)["plan"]
    except Exception:
        # Fail safe: default to Educator + Compliance
        plan = ["EducatorAgent", "ComplianceAgent"]

    # 3 Execute agents
    context = {}

    for step in plan:
        if step == "EducatorAgent":
            context["educator"] = educator_run(message)

        elif step == "MarketAgent":
            context["market"] = market_run(message)

    # 4️⃣ HARD GUARD: For ASK_CONCEPT, RAG MUST exist
    if intent == "ASK_CONCEPT":
        if not context.get("educator"):
            return (
                "I don't have enough trusted information to answer that right now.",
                intent,
                risk
            )

    # 5️⃣ LLM SYNTHESIS (STRICTLY GROUNDED)
    synthesis_prompt = f"""
You are a financial education assistant.

You MUST follow these rules:
- Use ONLY the information provided below.
- Do NOT add new concepts.
- Do NOT generalize.
- Do NOT use outside knowledge.
- If information is missing, say: "I don't have enough information."
- Consider conversation history to provide coherent, context-aware responses.

Conversation history:
{conversation_context or "(No prior conversation)"}

Trusted educator information:
{context.get("educator") or "(No educator context)"}

Market data:
{context.get("market") or "(No market data)"}

User question:
{message}

Provide a clear, beginner-friendly explanation.
"""

    draft_response = call_llm(
        system_prompt="You explain finance concepts clearly and safely.",
        user_prompt=synthesis_prompt,
        temperature=0.3
    )

    # 6 Compliance Agent (always last)
    final_response = compliance_run(draft_response, risk)

    return final_response, intent, risk
