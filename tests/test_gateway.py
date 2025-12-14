"""
Tests for AI Gateway with multi-provider support, caching, and resilience.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.gateway import (
    AIGateway, LLMConfig, ProviderType, RequestCache, CircuitBreaker, get_gateway
)


def test_request_cache_hit():
    """Test cache stores and retrieves responses."""
    cache = RequestCache(max_size=10)
    
    response = "Cached response"
    cache.set("system", "user", "gpt-4", response, ttl_seconds=60)
    
    cached = cache.get("system", "user", "gpt-4")
    assert cached == response


def test_request_cache_expiry():
    """Test cache entries expire after TTL."""
    import time
    cache = RequestCache(max_size=10)
    
    response = "Short TTL response"
    cache.set("system", "user", "gpt-4", response, ttl_seconds=0)
    
    time.sleep(0.1)
    cached = cache.get("system", "user", "gpt-4")
    assert cached is None


def test_request_cache_miss_different_prompts():
    """Test cache miss with different prompts."""
    cache = RequestCache(max_size=10)
    
    cache.set("sys1", "user1", "gpt-4", "response1", ttl_seconds=60)
    cached = cache.get("sys2", "user2", "gpt-4")
    assert cached is None


def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold."""
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout_seconds=60)
    
    assert not breaker.is_open()
    
    breaker.record_failure()
    breaker.record_failure()
    assert not breaker.is_open()  # Still below threshold
    
    breaker.record_failure()
    assert breaker.is_open()  # Now open


def test_circuit_breaker_resets_on_success():
    """Test circuit breaker resets on success."""
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout_seconds=60)
    
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open()
    
    breaker.record_success()
    assert not breaker.is_open()


def test_circuit_breaker_timeout_reset():
    """Test circuit breaker resets after timeout."""
    import time
    breaker = CircuitBreaker(failure_threshold=2, reset_timeout_seconds=1)
    
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open()
    
    # Not yet expired
    assert breaker.is_open()
    
    # Wait and check reset
    time.sleep(1.1)
    assert not breaker.is_open()  # Should reset after timeout


def test_gateway_add_provider():
    """Test gateway can add providers."""
    gateway = AIGateway()
    config = LLMConfig(
        provider=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4"
    )
    gateway.add_provider(config)
    
    assert len(gateway._providers) == 1
    assert gateway._providers[0].model == "gpt-4"


def test_gateway_provider_priority():
    """Test gateway sorts providers by priority."""
    gateway = AIGateway()
    
    gateway.add_provider(LLMConfig(
        provider=ProviderType.OPENAI,
        api_key="key1",
        model="gpt-4",
        priority=0
    ))
    gateway.add_provider(LLMConfig(
        provider=ProviderType.ANTHROPIC,
        api_key="key2",
        model="claude-3",
        priority=1
    ))
    
    # Higher priority should be first
    assert gateway._providers[0].model == "claude-3"
    assert gateway._providers[1].model == "gpt-4"


@patch('openai.OpenAI')
def test_gateway_openai_fallthrough(mock_openai_class):
    """Test gateway successfully calls OpenAI."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "OpenAI response"
    mock_client.chat.completions.create.return_value = mock_response
    
    gateway = AIGateway(cache_enabled=False)
    gateway.add_provider(LLMConfig(
        provider=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4"
    ))
    
    result = gateway.call_llm("system", "user", temperature=0)
    assert result == "OpenAI response"
    assert gateway._metrics["total_requests"] == 1


@patch('openai.OpenAI')
def test_gateway_retry_on_failure(mock_openai_class):
    """Test gateway retries on provider failure."""
    mock_openai_class.side_effect = Exception("API Error")
    
    gateway = AIGateway(cache_enabled=False)
    gateway.add_provider(LLMConfig(
        provider=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4"
    ))
    
    with pytest.raises(Exception, match="All LLM providers failed"):
        gateway.call_llm("system", "user")
    
    assert gateway._metrics["failures"] == 1


def test_gateway_metrics():
    """Test gateway metrics collection."""
    gateway = AIGateway()
    gateway.add_provider(LLMConfig(
        provider=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4"
    ))
    
    metrics = gateway.get_metrics()
    assert metrics["total_requests"] == 0
    assert metrics["cache_hits"] == 0
    assert metrics["cache_hit_rate_percent"] == 0


def test_get_gateway_singleton():
    """Test get_gateway returns singleton."""
    gateway1 = get_gateway()
    gateway2 = get_gateway()
    
    assert gateway1 is gateway2


def test_get_gateway_loads_openai_from_env(monkeypatch):
    """Test gateway loads OpenAI from environment."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    
    # Reset global gateway
    import app.gateway
    app.gateway._gateway = None
    
    gateway = get_gateway()
    assert len(gateway._providers) >= 1
    assert any(p.provider == ProviderType.OPENAI for p in gateway._providers)
