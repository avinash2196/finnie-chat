# External Portfolio API Specification

## Overview

This is an **OpenAPI 3.0 specification** (`external_portfolio_api.yaml`) that documents the contract for an external portfolio management service.

### What is this?

- **Blueprint**: A complete contract defining endpoints, request/response shapes, error codes, and authentication.
- **Communication**: Hand this to your portfolio provider (custodian, brokerage API, in-house backend, etc.) to implement.
- **Testing**: Use tools like Prism or Mockoon to mock this API locally during development.
- **Reference**: Agents and adapters in finnie-chat call this API to fetch real portfolio data.

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/users/{user_id}/holdings` | GET | Current positions (stocks, bonds, cash) |
| `/users/{user_id}/profile` | GET | User risk tolerance, goals, constraints |
| `/users/{user_id}/transactions` | GET | Transaction history (buy, sell, dividend, transfer) |
| `/users/{user_id}/performance` | GET | Performance metrics, price history, 52-week high/low |
| `/users/{user_id}/transactions/record` | POST | Record a new transaction |

### Authentication

**Bearer Token** (API key in `Authorization` header):
```
Authorization: Bearer sk_live_abc123xyz...
```

### Rate Limits

- **100 requests/minute** per API key
- Response headers include `X-RateLimit-Limit` and `X-RateLimit-Remaining`

### Error Handling

All errors follow a consistent structure:
```json
{
  "error": "invalid_request",
  "message": "Missing required field: ticker",
  "timestamp": "2025-12-20T12:34:56Z"
}
```

Common error codes:
- `unauthorized` (401) — invalid or missing API key
- `not_found` (404) — user does not exist
- `invalid_request` (400) — malformed request
- `rate_limit_exceeded` (429) — too many requests
- `server_error` (500) — upstream issue

---

## How to Use This

### Option 1: Mock Locally (Recommended for Dev)

Use **Prism** or **Mockoon** to spin up a mock server:

```bash
# Install Prism (once)
npm install -g @stoplight/prism-cli

# Run mock server on port 8001
prism mock external_portfolio_api.yaml --host 0.0.0.0 --port 8001
```

Then set env vars to point to your mock:
```bash
export PORTFOLIO_BACKEND=external
export EXTERNAL_PORTFOLIO_BASE_URL=http://localhost:8001/v1
export EXTERNAL_PORTFOLIO_API_KEY=mock-key-12345
```

And in the code, the `ExternalPortfolioClient` will call the mock server.

### Option 2: Hand to External Provider

Share this YAML file with your portfolio provider (brokerage, custodian, etc.) and ask them to implement it. They will:
1. Implement the endpoints with your real data.
2. Provide you with a `BASE_URL` and `API_KEY`.
3. You configure those as env vars and enable `PORTFOLIO_BACKEND=external`.

### Option 3: Implement Your Own Backend

If you own the portfolio data, you can build a small service that implements this spec and database queries. It becomes your source of truth.

---

## Integration with finnie-chat

The finnie-chat codebase uses this spec via:

1. **Factory Pattern** (`app/mcp/portfolio.py`):
   ```python
   def get_portfolio_client(user_id="user_123"):
       backend = os.getenv("PORTFOLIO_BACKEND", "mock")
       if backend == "external":
           return ExternalPortfolioClient(user_id)
       return PortfolioClient(user_id)  # default mock
   ```

2. **Adapter** (`app/mcp/adapters/external_portfolio.py`):
   - Skeleton client that **will** call HTTP endpoints once implemented
   - Currently a no-op to keep system operational

3. **Agents** call `get_portfolio_client(user_id)` and don't care about the backend:
   - `app/agents/risk_profiler.py`
   - `app/agents/portfolio_coach.py`
   - `app/agents/strategy.py`

So when you configure `PORTFOLIO_BACKEND=external`, the agents automatically use real data from the external service. No code changes needed.

---

## Next Steps

1. **Validate**: Review this spec with your portfolio provider or stakeholders.
2. **Adjust**: Modify fields, add/remove endpoints, or change response shapes as needed.
3. **Implement**: 
   - Option A: Wire up `ExternalPortfolioClient` to call this API (add `httpx`, retries, caching).
   - Option B: Provide spec to external provider and wait for their implementation.
   - Option C: Mock it locally with Prism and develop/test first.
4. **Test**: Add integration tests that hit the real or mock API.

---

## Example: Holdings Response

```json
{
  "user_id": "user_123",
  "holdings": {
    "AAPL": {
      "ticker": "AAPL",
      "quantity": 100,
      "purchase_price": 150.00,
      "current_price": 180.00,
      "purchase_date": "2024-01-15",
      "current_value": 18000.00,
      "gain_loss": 3000.00,
      "gain_loss_pct": 20.0
    },
    "MSFT": {
      "ticker": "MSFT",
      "quantity": 50,
      "purchase_price": 300.00,
      "current_price": 350.00,
      "purchase_date": "2024-02-15",
      "current_value": 17500.00,
      "gain_loss": 2500.00,
      "gain_loss_pct": 8.33
    }
  },
  "total_shares_value": 35500.00,
  "total_cash": 10000.00,
  "total_portfolio_value": 45500.00,
  "timestamp": "2025-12-20T12:34:56Z"
}
```

---

## Support

For questions or updates to this spec, contact `api-support@portfolio-provider.com`.
