"""
LLM client using AI Gateway for intelligent routing, caching, and failover.
"""

from app.gateway import get_gateway


def call_llm(system_prompt: str, user_prompt: str, temperature=0):
    """
    Call LLM through the gateway with intelligent failover and caching.
    Synchronous — use acall_llm() in async contexts to avoid blocking the event loop.
    """
    gateway = get_gateway()
    return gateway.call_llm(system_prompt, user_prompt, temperature)


async def acall_llm(system_prompt: str, user_prompt: str, temperature=0):
    """Async LLM call — runs in a thread pool so uvicorn's event loop is not blocked."""
    gateway = get_gateway()
    return await gateway.acall_llm(system_prompt, user_prompt, temperature)


def get_gateway_metrics():
    """Get gateway performance metrics."""
    gateway = get_gateway()
    return gateway.get_metrics()
