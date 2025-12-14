"""
AI Gateway for managing LLM requests with resilience, caching, and routing.
Supports multiple providers, fallbacks, and intelligent retry strategies.
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""
    provider: ProviderType
    api_key: str
    model: str
    base_url: Optional[str] = None
    max_retries: int = 3
    timeout_seconds: int = 30
    priority: int = 0  # Higher = tried first


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    response: str
    timestamp: float
    ttl_seconds: int

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl_seconds


class RequestCache:
    """Simple in-memory cache for LLM responses."""

    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size

    def _cache_key(self, system: str, user: str, model: str) -> str:
        return f"{model}:{hash(system + user)}"

    def get(self, system: str, user: str, model: str) -> Optional[str]:
        """Retrieve cached response if valid."""
        key = self._cache_key(system, user, model)
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            logger.info(f"Cache hit: {key}")
            return entry.response
        if entry:
            del self._cache[key]
        return None

    def set(self, system: str, user: str, model: str, response: str, ttl_seconds: int = 3600):
        """Cache response with TTL."""
        if len(self._cache) >= self._max_size:
            # Simple eviction: remove oldest
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]

        key = self._cache_key(system, user, model)
        self._cache[key] = CacheEntry(response, time.time(), ttl_seconds)


class CircuitBreaker:
    """Circuit breaker pattern for provider resilience."""

    def __init__(self, failure_threshold: int = 5, reset_timeout_seconds: int = 60):
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout_seconds
        self._last_failure_time = None
        self._is_open = False

    def record_success(self):
        """Reset breaker on success."""
        self._failure_count = 0
        self._is_open = False

    def record_failure(self):
        """Increment failure count."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self._failure_threshold:
            self._is_open = True
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")

    def is_open(self) -> bool:
        """Check if breaker is open (and potentially ready to close)."""
        if not self._is_open:
            return False
        
        # Check if reset timeout has elapsed
        if self._last_failure_time and time.time() - self._last_failure_time > self._reset_timeout:
            logger.info("Circuit breaker attempting reset")
            self._is_open = False
            self._failure_count = 0
            return False
        
        return True


class AIGateway:
    """
    Intelligent LLM gateway with multi-provider support, failover, caching, and resilience.
    """

    def __init__(self, cache_enabled: bool = True):
        self._providers: List[LLMConfig] = []
        self._cache = RequestCache() if cache_enabled else None
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._metrics = {"total_requests": 0, "cache_hits": 0, "failures": 0}

    def add_provider(self, config: LLMConfig):
        """Add a provider to the gateway."""
        self._providers.append(config)
        self._providers.sort(key=lambda p: -p.priority)  # Higher priority first
        self._breakers[config.provider.value] = CircuitBreaker()
        logger.info(f"Added provider: {config.provider.value} ({config.model})")

    def _get_openai_response(self, config: LLMConfig, system: str, user: str, temperature: float) -> str:
        """Call OpenAI API."""
        from openai import OpenAI

        client = OpenAI(api_key=config.api_key)
        response = client.chat.completions.create(
            model=config.model,
            temperature=temperature,
            timeout=config.timeout_seconds,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return response.choices[0].message.content

    def _get_azure_openai_response(self, config: LLMConfig, system: str, user: str, temperature: float) -> str:
        """Call Azure OpenAI API."""
        from openai import AzureOpenAI

        client = AzureOpenAI(
            api_key=config.api_key,
            api_version="2024-02-15-preview",
            azure_endpoint=config.base_url
        )
        response = client.chat.completions.create(
            model=config.model,
            temperature=temperature,
            timeout=config.timeout_seconds,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        return response.choices[0].message.content

    def _get_anthropic_response(self, config: LLMConfig, system: str, user: str, temperature: float) -> str:
        """Call Anthropic API."""
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)
        message = client.messages.create(
            model=config.model,
            max_tokens=2048,
            temperature=temperature,
            system=system,
            messages=[
                {"role": "user", "content": user}
            ]
        )
        return message.content[0].text

    def call_llm(self, system: str, user: str, temperature: float = 0) -> str:
        """
        Call LLM with intelligent failover, caching, and resilience.
        
        Args:
            system: System prompt
            user: User prompt
            temperature: Sampling temperature
            
        Returns:
            LLM response
            
        Raises:
            Exception: If all providers fail
        """
        self._metrics["total_requests"] += 1

        # Check cache first
        if self._cache:
            # Use first provider's model for cache key
            model = self._providers[0].model if self._providers else "unknown"
            cached = self._cache.get(system, user, model)
            if cached:
                self._metrics["cache_hits"] += 1
                return cached

        # Try each provider in priority order
        last_error = None
        for provider_config in self._providers:
            breaker = self._breakers[provider_config.provider.value]

            # Skip if circuit breaker is open
            if breaker.is_open():
                logger.warning(f"Skipping {provider_config.provider.value}: circuit breaker open")
                continue

            try:
                logger.info(f"Attempting {provider_config.provider.value}/{provider_config.model}")

                if provider_config.provider == ProviderType.OPENAI:
                    response = self._get_openai_response(provider_config, system, user, temperature)
                elif provider_config.provider == ProviderType.AZURE_OPENAI:
                    response = self._get_azure_openai_response(provider_config, system, user, temperature)
                elif provider_config.provider == ProviderType.ANTHROPIC:
                    response = self._get_anthropic_response(provider_config, system, user, temperature)
                else:
                    raise ValueError(f"Unknown provider: {provider_config.provider}")

                # Cache successful response
                if self._cache:
                    self._cache.set(system, user, provider_config.model, response)

                breaker.record_success()
                logger.info(f"Success with {provider_config.provider.value}")
                return response

            except Exception as e:
                last_error = e
                breaker.record_failure()
                logger.error(f"Failed with {provider_config.provider.value}: {e}")
                continue

        # All providers failed
        self._metrics["failures"] += 1
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics."""
        total = self._metrics["total_requests"]
        cache_hits = self._metrics["cache_hits"]
        hit_rate = (cache_hits / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "cache_hits": cache_hits,
            "cache_hit_rate_percent": round(hit_rate, 2),
            "failures": self._metrics["failures"],
            "providers_active": len([p for p in self._providers if not self._breakers[p.provider.value].is_open()])
        }


# Global gateway instance
_gateway: Optional[AIGateway] = None


def get_gateway() -> AIGateway:
    """Get or create the AI gateway."""
    global _gateway
    if _gateway is None:
        _gateway = AIGateway(cache_enabled=True)
        
        # Load providers from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            _gateway.add_provider(LLMConfig(
                provider=ProviderType.OPENAI,
                api_key=api_key,
                model="gpt-4o-mini",
                priority=1
            ))
        
        # Optional: Add Azure OpenAI as fallback
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            _gateway.add_provider(LLMConfig(
                provider=ProviderType.AZURE_OPENAI,
                api_key=azure_key,
                model="gpt-4",
                base_url=azure_endpoint,
                priority=0  # Lower priority (fallback)
            ))
        
        # Optional: Add Anthropic as additional fallback
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            _gateway.add_provider(LLMConfig(
                provider=ProviderType.ANTHROPIC,
                api_key=anthropic_key,
                model="claude-3-5-sonnet-20241022",
                priority=0
            ))
    
    return _gateway
