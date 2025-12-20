# AI Gateway Setup & Configuration Guide

## Overview

The AI Gateway provides intelligent LLM request routing with multi-provider support, caching, resilience, and comprehensive metrics.

## Key Features

- **Multi-Provider Support**: OpenAI, Azure OpenAI, Anthropic
 - **Multi-Provider Support**: OpenAI, Gemini, Anthropic
- **Intelligent Failover**: Automatic fallback to secondary providers on failure
- **Circuit Breaker**: Prevents cascading failures by temporarily disabling failed providers
- **Request Caching**: TTL-based caching with configurable expiry (default 3600s)
- **Provider Priority**: Routes requests to higher-priority providers first
- **Metrics**: Track cache hit rate, failure count, and active providers

## Configuration

### Environment Variables

Set in `.env`:

```bash
# Primary provider (OpenAI)
OPENAI_API_KEY=sk-proj-...

# Optional: Gemini fallback (example)
GEMINI_API_KEY=your-gemini-key
GEMINI_ENDPOINT=https://your-gemini-endpoint.example.com

# Optional: Anthropic additional fallback
ANTHROPIC_API_KEY=sk-ant-...
```

### Programmatic Configuration

```python
from app.gateway import get_gateway, LLMConfig, ProviderType

gateway = get_gateway()

# Providers are auto-loaded from environment
# But you can add custom providers at runtime:

gateway.add_provider(LLMConfig(
    provider=ProviderType.OPENAI,
    api_key="your-key",
    model="gpt-4o-mini",
    priority=1  # Higher priority = tried first
))
```

## How the Gateway Works

### 1. Request Flow

```
User Request
    ↓
Cache Check → Cache Hit → Return cached response
    ↓ (miss)
Circuit Breaker Check
    ↓
Try Primary Provider (highest priority)
    ↓ (success) → Cache response → Return
    ↓ (failure) → Record failure
Try Secondary Provider
    ↓ (success) → Cache response → Return
    ↓ (failure) → Record failure
All providers failed → Raise exception
```

### 2. Circuit Breaker Behavior

- **Closed** (normal): Requests pass through
- **Open** (after 5 failures): Provider is skipped temporarily
- **Half-Open** (after timeout): Retries provider to see if recovered

Configuration:
```python
CircuitBreaker(
    failure_threshold=5,      # Opens after 5 consecutive failures
    reset_timeout_seconds=60   # Waits 60s before attempting recovery
)
```

### 3. Caching Strategy

- **Key**: Hash of (model, system_prompt, user_prompt)
- **TTL**: 3600 seconds by default
- **Size**: 1000 entries max (LRU eviction)
- **Use Cases**:
  - Repeated queries get instant responses
  - Reduced latency and API costs
  - Offline capability for cached requests

Disable caching:
```python
gateway = AIGateway(cache_enabled=False)
```

## Monitoring & Metrics

### View Gateway Metrics

```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "total_requests": 42,
  "cache_hits": 15,
  "cache_hit_rate_percent": 35.71,
  "failures": 2,
  "providers_active": 2
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok"
}
```

## Usage Examples

### Basic Usage (automatic via app)

```python
from app.llm import call_llm

response = call_llm(
    system_prompt="You are a helpful assistant.",
    user_prompt="What is 2+2?",
    temperature=0
)
print(response)
```

### Direct Gateway Access

```python
from app.gateway import get_gateway

gateway = get_gateway()
response = gateway.call_llm(
    system="You are a finance expert.",
    user="Explain bond pricing.",
    temperature=0.7
)
```

### Checking Metrics Programmatically

```python
from app.llm import get_gateway_metrics

metrics = get_gateway_metrics()
print(f"Cache hit rate: {metrics['cache_hit_rate_percent']}%")
print(f"Active providers: {metrics['providers_active']}")
```

## Best Practices

### 1. Provider Priority

Arrange providers by:
- **Reliability**: Most stable first
- **Cost**: Cheaper as fallback
- **Performance**: Faster models as primary

```python
# Recommended order
gateway.add_provider(LLMConfig(..., model="gpt-4o-mini", priority=2))   # Primary
gateway.add_provider(LLMConfig(..., model="gpt-4", priority=1))         # Fallback
gateway.add_provider(LLMConfig(..., model="claude-3", priority=0))      # Last resort
```

### 2. Caching Strategy

- **Enable** for repeated queries (chat, education agent)
- **Disable** for unique/sensitive queries
- **Set TTL** based on data freshness needs (market data: 60s, education: 3600s)

```python
# Short TTL for market data
cache.set(system, user, model, response, ttl_seconds=60)

# Longer TTL for educational content
cache.set(system, user, model, response, ttl_seconds=3600)
```

### 3. Error Handling

```python
try:
    response = call_llm(system, user)
except Exception as e:
    logger.error(f"All LLM providers failed: {e}")
    # Fallback to cached response or default message
    response = "I'm temporarily unavailable. Please try again."
```

### 4. Circuit Breaker Tuning

- **Adjust failure_threshold**: Higher = more tolerant, Lower = faster failover
- **Adjust reset_timeout**: Longer = safer, Shorter = faster recovery

```python
# Aggressive failover for reliable providers
CircuitBreaker(failure_threshold=3, reset_timeout_seconds=30)

# Tolerant for unreliable networks
CircuitBreaker(failure_threshold=10, reset_timeout_seconds=120)
```

## Troubleshooting

### Issue: "All LLM providers failed"

**Causes:**
1. Invalid API keys
2. All providers down
3. Circuit breakers all open

**Solution:**
```python
metrics = get_gateway_metrics()
print(f"Active providers: {metrics['providers_active']}")
print(f"Failures: {metrics['failures']}")
```

### Issue: Low cache hit rate

**Causes:**
1. Unique queries each time
2. Cache TTL too short
3. Cache disabled

**Solution:**
- Increase TTL for relevant prompts
- Reuse common system prompts
- Check cache is enabled

### Issue: Slow responses

**Causes:**
1. Primary provider slow/down
2. Circuit breaker delay
3. No cache hits

**Solution:**
- Add faster provider as primary
- Reduce failure_threshold for faster failover
- Ensure cache is enabled and hit rate is good

## Performance Optimization

### 1. Use async for multiple requests

```python
import asyncio

async def call_multiple():
    tasks = [
        asyncio.to_thread(call_llm, sys, usr)
        for sys, usr in prompts
    ]
    return await asyncio.gather(*tasks)
```

### 2. Batch similar queries for cache reuse

```python
# Bad: Each gets unique key
for query in unique_queries:
    call_llm("system", query)

# Good: Reuse system prompt
system = "You are a finance expert."
for query in related_queries:
    call_llm(system, query)  # More likely to hit cache
```

### 3. Monitor and adjust

```python
# Check metrics regularly
gateway = get_gateway()
metrics = gateway.get_metrics()

if metrics['cache_hit_rate_percent'] < 20:
    # Increase TTL or reuse prompts more
    pass

if metrics['failures'] > 5:
    # Add backup provider or check API keys
    pass
```

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│         FastAPI App (/chat)             │
└──────────────────┬──────────────────────┘
                   │ call_llm()
                   ↓
┌─────────────────────────────────────────┐
│      AI Gateway (app/gateway.py)        │
├─────────────────────────────────────────┤
│  ┌──────────────────────────────────┐  │
│  │    Request Cache (TTL-based)     │  │
│  │  Cache Hit → Return immediately  │  │
│  └──────────────────────────────────┘  │
│  ┌──────────────────────────────────┐  │
│  │  Circuit Breaker per Provider    │  │
│  │  Fail → Open → Try next provider │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ↙        ↓        ↘
   ┌─────────┐ ┌────────┐ ┌──────────┐
    │ OpenAI  │ │ Gemini │ │Anthropic │
    │(Priority│ │(Fallback)│ │(Fallback)│
    │  1)     │ │         │ │          │
   └─────────┘ └────────┘ └──────────┘
```

## Next Steps

1. **Monitor in production**: Track metrics endpoint
2. **Adjust providers**: Based on performance data
3. **Fine-tune caching**: Per-agent TTL strategies
4. **Cost tracking**: Add API cost logging to metrics
5. **Load testing**: Validate failover under load
