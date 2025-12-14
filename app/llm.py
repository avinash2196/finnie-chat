"""
LLM client using AI Gateway for intelligent routing, caching, and failover.
"""

from app.gateway import get_gateway


def call_llm(system_prompt: str, user_prompt: str, temperature=0):
    """
    Call LLM through the gateway with intelligent failover and caching.
    
    Args:
        system_prompt: System prompt
        user_prompt: User prompt
        temperature: Sampling temperature (0=deterministic, 1=creative)
        
    Returns:
        LLM response string
    """
    gateway = get_gateway()
    return gateway.call_llm(system_prompt, user_prompt, temperature)


def get_gateway_metrics():
    """Get gateway performance metrics."""
    gateway = get_gateway()
    return gateway.get_metrics()
