# Database Integration Guide

## Overview

Finnie Chat includes a complete database layer with:
- **SQLite (dev) / PostgreSQL (prod)** — SQLAlchemy ORM with dual backend support
- **Agent-driven Portfolio Access** — Agents query database via Portfolio MCP Server
- **External API Integration** — Sync from Robinhood, Fidelity, or mock data
- **Provider Pattern** — Easily switch between data sources
- **Background Sync Tasks** — Automatic hourly portfolio updates
- **Comprehensive REST API** — Full CRUD operations for portfolios
- **Real User Context in Chat** — Portfolio agents see actual user holdings

## What's New (Dec 2025)

✅ **Portfolio MCP is Database-Backed** — No more mock data. The Portfolio MCP server now queries the real SQLite database for all user holdings, transactions, and profiles.

✅ **Chat Agents See Real Portfolios** — The `/chat` endpoint now passes user_id to the orchestrator, enabling agents to access actual user holdings.

✅ **UUID & Username Support** — All portfolio MCP functions support both lookup methods (by UUID or username).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Chat / REST API Requests                    │
├─────────────────────────────────────────────────────────────┤
│                   Orchestrator Layer                          │
│  (Routes to Portfolio Coach, Risk Profiler, Strategy, etc.)  │
├─────────────────────────────────────────────────────────────┤
│              Portfolio MCP Server (Database-Backed)           │
│  ├─ get_user_holdings(user_id)  ◄─ Query Holding table      │
│  ├─ get_user_profile(user_id)   ◄─ Query User table         │
│  ├─ get_transaction_history()   ◄─ Query Transaction table  │
│  └─ get_performance_metrics()   ◄─ Query PortfolioSnapshot  │
├─────────────────────────────────────────────────────────────┤
│                  SQLAlchemy ORM Layer                        │
├─────────────────────────────────────────────────────────────┤
│  User │ Holding │ Transaction │ Snapshot │ SyncLog          │
├─────────────────────────────────────────────────────────────┤
│                  SQLite / PostgreSQL                          │
└─────────────────────────────────────────────────────────────┘
```

## Database Models

### User
- `id`: UUID primary key
- `email`: Unique email address
- `username`: Unique username (also used for lookups in portfolio MCP)
- `risk_tolerance`: LOW, MEDIUM, HIGH
- `portfolio_value`: Cached total portfolio value
- `robinhood_token`, `fidelity_token`: External API credentials
- Relationships: holdings, transactions, snapshots

### Holding
- `id`: UUID primary key
- `user_id`: Foreign key to User (UUID)
- `ticker`: Stock symbol (AAPL, MSFT, etc.)
- `quantity`: Number of shares
- `purchase_price`: Original buy price
- `current_price`: Latest market price (synced from providers)
- `total_value`: quantity × current_price
- `gain_loss`: (current_price - purchase_price) × quantity


### Transaction
- `id`: UUID primary key
- `user_id`: Foreign key to User
- `ticker`: Stock symbol
- `transaction_type`: BUY, SELL, DIVIDEND
- `quantity`: Number of shares
- `price`: Price per share
- `total_amount`: quantity × price
- `transaction_date`: When transaction occurred

### PortfolioSnapshot
- `id`: UUID primary key
- `user_id`: Foreign key to User
- `total_value`: Portfolio value at snapshot time
- `daily_return`, `monthly_return`, `yearly_return`: Performance metrics
- `volatility`, `sharpe_ratio`: Risk metrics
- `snapshot_date`: When snapshot was created

### SyncLog
- `id`: UUID primary key
- `user_id`: Foreign key to User
- `source`: MOCK, ROBINHOOD, FIDELITY
- `status`: SUCCESS, FAILED, PENDING
- `synced_items`: Number of holdings synced
- `sync_time_ms`: How long sync took

## Quick Start

### 1. Initialize Database

```python
from app.database import init_db

# Creates all tables
init_db()
```

### 2. Create User

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myusername",
    "risk_tolerance": "MEDIUM"
  }'
```

### 3. Add Holdings Manually

```bash
curl -X POST http://localhost:8000/users/{user_id}/holdings \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "quantity": 10,
    "purchase_price": 150.0
  }'
```

### 4. Sync from External Provider

```bash
# Sync from mock data
curl -X POST http://localhost:8000/users/{user_id}/sync \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "mock"
  }'

# Sync from Robinhood (requires token)
curl -X POST http://localhost:8000/users/{user_id}/sync \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "robinhood",
    "api_token": "YOUR_ROBINHOOD_TOKEN"
  }'
```

### 5. View Portfolio

```bash
curl http://localhost:8000/users/{user_id}/portfolio
```

Response:
```json
{
  "user_id": "...",
  "total_value": 5000.0,
  "total_gain_loss": 250.0,
  "total_return_pct": 5.26,
  "holdings_count": 3,
  "holdings": [
    {
      "id": "...",
      "ticker": "AAPL",
      "quantity": 10,
      "purchase_price": 150.0,
      "current_price": 160.0,
      "total_value": 1600.0,
      "gain_loss": 100.0,
      "gain_loss_pct": 6.67
    }
  ]
}
```

## API Endpoints

### User Management
- `POST /users` - Create user
- `GET /users/{user_id}` - Get user details

### Portfolio Operations
- `GET /users/{user_id}/portfolio` - Get complete portfolio
- `GET /users/{user_id}/holdings` - List holdings
- `POST /users/{user_id}/holdings` - Add holding
- `DELETE /users/{user_id}/holdings/{holding_id}` - Delete holding
- `GET /users/{user_id}/allocation` - Get asset allocation breakdown

### Transactions
- `GET /users/{user_id}/transactions?days=90` - List transactions

### External Sync
- `POST /users/{user_id}/sync` - Sync from external provider

### Analytics
- `POST /users/{user_id}/snapshot` - Create portfolio snapshot
- `GET /users/{user_id}/snapshots?days=30` - Get historical snapshots

## Provider Pattern

### Using Mock Provider (Development)

```python
from app.providers import PortfolioProviderFactory, sync_portfolio

provider = PortfolioProviderFactory.get_provider("mock")
holdings = await provider.get_holdings(user_id, {})
```

### Using Robinhood Provider

```python
provider = PortfolioProviderFactory.get_provider("robinhood")
credentials = {"robinhood_token": "YOUR_TOKEN"}
holdings = await provider.get_holdings(user_id, credentials)
```

### Registering Custom Provider

```python
from app.providers import PortfolioProvider, PortfolioProviderFactory

class CustomProvider(PortfolioProvider):
    async def get_holdings(self, user_id, credentials):
        # Your implementation
        pass

PortfolioProviderFactory.register_provider("custom", CustomProvider)
```

## Background Sync

### Manual Sync

```python
from app.sync_tasks import SyncTaskRunner

# Immediate sync
result = await SyncTaskRunner.sync_now(user_id, "mock", {})

# Update prices only (lightweight)
result = await SyncTaskRunner.sync_price_update(user_id)

# Create daily snapshots
result = await SyncTaskRunner.create_daily_snapshots()
```

### Automatic Scheduled Sync

```python
from app.sync_tasks import start_scheduler, stop_scheduler

# Start background scheduler (syncs every hour)
await start_scheduler()

# Stop scheduler
await stop_scheduler()
```

## Database Configuration

### Development (SQLite)

```bash
# Uses local file
DATABASE_URL=sqlite:///./finnie_chat.db
```

### Production (PostgreSQL)

```bash
# Set in .env
DATABASE_URL=postgresql://user:password@localhost/finnie_chat
```

## Testing

### Run Database Tests

```bash
# All database tests
pytest tests/test_database.py -v

# Integration tests
pytest tests/test_integration_sync.py -v

# API endpoint tests
pytest tests/test_api_integration.py -v
```

### Test Coverage

- **Unit Tests**: 15 tests for database models
- **Integration Tests**: 25+ tests for provider sync
- **API Tests**: 30+ tests for REST endpoints
- **Total**: 70+ new tests added

## Migration from Mock MCP

The old `app/portfolio_mcp.py` returned static mock data. New system:

1. **Database persistence** - Holdings stored in SQLite/PostgreSQL
2. **External API support** - Sync from real brokers
3. **Transaction history** - Complete audit trail
4. **Analytics** - Historical snapshots and performance tracking

### Migration Steps

1. Keep using mock provider during development
2. Configure external API tokens when ready
3. Switch provider from "mock" to "robinhood" or "fidelity"
4. Data automatically syncs to database

## Examples

### Complete Workflow

```python
from app.database import SessionLocal, User
from app.providers import sync_portfolio

# 1. Create user
db = SessionLocal()
user = User(email="test@example.com", username="testuser")
db.add(user)
db.commit()

# 2. Sync from external source
result = await sync_portfolio(user.id, db, "mock", {})
print(f"Synced {result['synced_items']} holdings")

# 3. Query holdings
from app.database import Holding
holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
for h in holdings:
    print(f"{h.ticker}: {h.quantity} shares @ ${h.current_price}")

# 4. Create snapshot
from app.database import PortfolioSnapshot
snapshot = PortfolioSnapshot(
    user_id=user.id,
    total_value=sum(h.total_value for h in holdings)
)
db.add(snapshot)
db.commit()
```

### Frontend Integration

```javascript
// Fetch portfolio
const response = await fetch(`/users/${userId}/portfolio`);
const portfolio = await response.json();

console.log(`Total Value: $${portfolio.total_value}`);
console.log(`Holdings: ${portfolio.holdings_count}`);

portfolio.holdings.forEach(h => {
  console.log(`${h.ticker}: ${h.gain_loss_pct}% return`);
});

// Sync from Robinhood
await fetch(`/users/${userId}/sync`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    provider: 'robinhood',
    api_token: userToken
  })
});
```

## Performance

- **Sync time**: < 2 seconds for 10 holdings (mock)
- **Price update**: < 1 second for 20 holdings
- **Database queries**: Indexed on user_id, ticker, dates
- **Concurrent users**: Tested with 50+ simultaneous syncs

## Security

- **API tokens encrypted** in production (use environment variables)
- **No tokens in logs** - Redacted in sync logs
- **User isolation** - All queries filtered by user_id
- **Input validation** - Pydantic models validate all inputs

## Roadmap

- ✅ Database models and schema
- ✅ Mock provider for development
- ✅ External API adapters (Robinhood, Fidelity)
- ✅ Background sync tasks
- ✅ REST API endpoints
- ✅ Comprehensive tests (70+ tests)
- ⏳ Real-time price updates (WebSocket)
- ⏳ Portfolio analytics (Sharpe ratio, volatility)
- ⏳ Database migrations (Alembic)
- ⏳ Schwab/TD Ameritrade providers
- ⏳ Redis caching layer

## Troubleshooting

### Database not initialized
```bash
Error: no such table: users

Solution:
python -c "from app.database import init_db; init_db()"
```

### Sync fails with API error
```bash
Error: Robinhood API error: 401 Unauthorized

Solution:
- Check API token is valid
- Ensure token has proper scopes
- Use mock provider for testing
```

### Holdings not updating
```bash
Holdings show old prices

Solution:
# Trigger price update
curl -X POST /users/{user_id}/sync -d '{"provider":"mock"}'

# Or update prices only
await SyncTaskRunner.sync_price_update(user_id)
```

## Support

For issues or questions:
- Check test files for usage examples
- Review API endpoint tests for request/response formats
- See provider implementations in `app/providers.py`
