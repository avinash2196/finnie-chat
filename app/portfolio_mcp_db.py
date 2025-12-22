"""
MCP Server for Portfolio Management with database integration
Supports real Robinhood/Fidelity or mock data
"""
from mcp.server import Server, Request, CallToolRequest
from mcp.types import (
    Tool, TextContent, ToolResult, EmbeddedResource
)
from app.database import init_db, get_db, User, Holding, Transaction, PortfolioSnapshot, SessionLocal
from app.providers import PortfolioProviderFactory, sync_portfolio
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy.orm import Session

server = Server("portfolio-mcp")

# Initialize database
init_db()

# ==================== MCP TOOLS ====================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available portfolio tools"""
    return [
        Tool(
            name="get_portfolio",
            description="Get user's current portfolio with holdings and values",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User ID"},
                    "include_performance": {"type": "boolean", "description": "Include performance metrics"}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_holdings",
            description="Get list of holdings with current values",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "ticker_filter": {"type": "string", "description": "Filter by ticker (optional)"}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="add_holding",
            description="Add a new holding to portfolio",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "ticker": {"type": "string"},
                    "quantity": {"type": "number"},
                    "purchase_price": {"type": "number"},
                    "purchase_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["user_id", "ticker", "quantity", "purchase_price"]
            }
        ),
        Tool(
            name="sell_holding",
            description="Sell all or part of a holding",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "holding_id": {"type": "string"},
                    "quantity": {"type": "number"},
                    "sale_price": {"type": "number"}
                },
                "required": ["user_id", "holding_id", "quantity", "sale_price"]
            }
        ),
        Tool(
            name="get_transactions",
            description="Get transaction history",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "days": {"type": "integer", "description": "Last N days (optional)"},
                    "ticker_filter": {"type": "string"}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="sync_external",
            description="Sync portfolio from external service (Robinhood, Fidelity, or mock)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "provider": {"type": "string", "enum": ["mock", "robinhood", "fidelity"]},
                    "api_token": {"type": "string", "description": "API token for service (optional)"}
                },
                "required": ["user_id", "provider"]
            }
        ),
        Tool(
            name="get_portfolio_snapshot",
            description="Get historical portfolio snapshots for analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "days": {"type": "integer", "description": "Last N days of snapshots"}
                },
                "required": ["user_id", "days"]
            }
        ),
        Tool(
            name="create_snapshot",
            description="Create a portfolio snapshot (for analytics)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        ),
        Tool(
            name="get_allocation",
            description="Get portfolio asset allocation breakdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"}
                },
                "required": ["user_id"]
            }
        ),
    ]


@server.call_tool()
async def handle_tool_call(request: CallToolRequest) -> ToolResult:
    """Handle tool calls"""
    db = SessionLocal()
    try:
        tool_name = request.params["name"]
        args = request.params.get("arguments", {})
        
        if tool_name == "get_portfolio":
            return await _get_portfolio(db, args)
        elif tool_name == "get_holdings":
            return await _get_holdings(db, args)
        elif tool_name == "add_holding":
            return await _add_holding(db, args)
        elif tool_name == "sell_holding":
            return await _sell_holding(db, args)
        elif tool_name == "get_transactions":
            return await _get_transactions(db, args)
        elif tool_name == "sync_external":
            return await _sync_external(db, args)
        elif tool_name == "get_portfolio_snapshot":
            return await _get_snapshot(db, args)
        elif tool_name == "create_snapshot":
            return await _create_snapshot(db, args)
        elif tool_name == "get_allocation":
            return await _get_allocation(db, args)
        else:
            return ToolResult(content=[TextContent(type="text", text=f"Unknown tool: {tool_name}")], is_error=True)
            
    except Exception as e:
        return ToolResult(content=[TextContent(type="text", text=f"Error: {str(e)}")], is_error=True)
    finally:
        db.close()


# ==================== TOOL IMPLEMENTATIONS ====================

async def _get_portfolio(db: Session, args: dict) -> ToolResult:
    """Get complete portfolio snapshot"""
    user_id = args.get("user_id")
    include_perf = args.get("include_performance", True)
    
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    
    portfolio = {
        "total_value": sum(h.total_value for h in holdings),
        "total_gain_loss": sum(h.gain_loss for h in holdings),
        "total_return_pct": 0.0,
        "holdings_count": len(holdings),
        "holdings": [
            {
                "id": h.id,
                "ticker": h.ticker,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
                "current_price": h.current_price,
                "total_value": h.total_value,
                "gain_loss": h.gain_loss,
                "gain_loss_pct": (h.gain_loss / (h.purchase_price * h.quantity) * 100) if h.purchase_price > 0 else 0
            }
            for h in holdings
        ]
    }
    
    if portfolio["total_value"] > 0:
        portfolio["total_return_pct"] = (portfolio["total_gain_loss"] / (portfolio["total_value"] - portfolio["total_gain_loss"]) * 100)
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(portfolio, indent=2))],
        is_error=False
    )


async def _get_holdings(db: Session, args: dict) -> ToolResult:
    """Get holdings list"""
    user_id = args.get("user_id")
    ticker_filter = args.get("ticker_filter")
    
    query = db.query(Holding).filter(Holding.user_id == user_id)
    if ticker_filter:
        query = query.filter(Holding.ticker == ticker_filter.upper())
    
    holdings = query.all()
    
    result = {
        "holdings": [
            {
                "id": h.id,
                "ticker": h.ticker,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
                "current_price": h.current_price,
                "total_value": h.total_value,
                "gain_loss": h.gain_loss,
                "gain_loss_pct": (h.gain_loss / (h.purchase_price * h.quantity) * 100) if h.purchase_price > 0 else 0,
                "purchase_date": h.purchase_date.isoformat()
            }
            for h in holdings
        ],
        "total_value": sum(h.total_value for h in holdings)
    }
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        is_error=False
    )


async def _add_holding(db: Session, args: dict) -> ToolResult:
    """Add new holding"""
    user_id = args.get("user_id")
    ticker = args.get("ticker").upper()
    quantity = float(args.get("quantity"))
    purchase_price = float(args.get("purchase_price"))
    purchase_date_str = args.get("purchase_date", datetime.utcnow().isoformat())
    
    holding = Holding(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        ticker=ticker,
        quantity=quantity,
        purchase_price=purchase_price,
        purchase_date=datetime.fromisoformat(purchase_date_str),
        current_price=purchase_price,  # Will be updated by sync
        total_value=quantity * purchase_price,
        gain_loss=0.0
    )
    
    db.add(holding)
    
    # Add transaction record
    txn = Transaction(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        ticker=ticker,
        transaction_type="BUY",
        quantity=quantity,
        price=purchase_price,
        total_amount=quantity * purchase_price,
        transaction_date=datetime.fromisoformat(purchase_date_str)
    )
    db.add(txn)
    
    db.commit()
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "status": "success",
            "holding_id": holding.id,
            "message": f"Added {quantity} shares of {ticker} at ${purchase_price}"
        }, indent=2))],
        is_error=False
    )


async def _sell_holding(db: Session, args: dict) -> ToolResult:
    """Sell holding"""
    user_id = args.get("user_id")
    holding_id = args.get("holding_id")
    quantity = float(args.get("quantity"))
    sale_price = float(args.get("sale_price"))
    
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == user_id
    ).first()
    
    if not holding:
        return ToolResult(
            content=[TextContent(type="text", text="Holding not found")],
            is_error=True
        )
    
    if holding.quantity < quantity:
        return ToolResult(
            content=[TextContent(type="text", text=f"Not enough shares. Have {holding.quantity}, trying to sell {quantity}")],
            is_error=True
        )
    
    # Add transaction
    txn = Transaction(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        ticker=holding.ticker,
        transaction_type="SELL",
        quantity=quantity,
        price=sale_price,
        total_amount=quantity * sale_price,
        transaction_date=datetime.utcnow()
    )
    db.add(txn)
    
    # Update holding
    holding.quantity -= quantity
    if holding.quantity == 0:
        db.delete(holding)
    else:
        holding.total_value = holding.quantity * holding.current_price
        holding.updated_at = datetime.utcnow()
    
    db.commit()
    
    gain_loss = (sale_price - holding.purchase_price) * quantity
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "status": "success",
            "message": f"Sold {quantity} shares of {holding.ticker} at ${sale_price}",
            "gain_loss": gain_loss
        }, indent=2))],
        is_error=False
    )


async def _get_transactions(db: Session, args: dict) -> ToolResult:
    """Get transactions"""
    user_id = args.get("user_id")
    days = args.get("days", 90)
    ticker_filter = args.get("ticker_filter")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= cutoff_date
    )
    
    if ticker_filter:
        query = query.filter(Transaction.ticker == ticker_filter.upper())
    
    txns = query.order_by(Transaction.transaction_date.desc()).all()
    
    result = {
        "transactions": [
            {
                "id": t.id,
                "ticker": t.ticker,
                "type": t.transaction_type,
                "quantity": t.quantity,
                "price": t.price,
                "total": t.total_amount,
                "date": t.transaction_date.isoformat()
            }
            for t in txns
        ],
        "count": len(txns)
    }
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        is_error=False
    )


async def _sync_external(db: Session, args: dict) -> ToolResult:
    """Sync from external provider"""
    user_id = args.get("user_id")
    provider = args.get("provider", "mock")
    api_token = args.get("api_token")
    
    credentials = {}
    if api_token:
        if provider == "robinhood":
            credentials["robinhood_token"] = api_token
        elif provider == "fidelity":
            credentials["fidelity_token"] = api_token
    
    result = await sync_portfolio(user_id, db, provider, credentials)
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        is_error=result["status"] != "SUCCESS"
    )


async def _get_snapshot(db: Session, args: dict) -> ToolResult:
    """Get portfolio snapshots"""
    user_id = args.get("user_id")
    days = args.get("days", 30)
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id,
        PortfolioSnapshot.snapshot_date >= cutoff_date
    ).order_by(PortfolioSnapshot.snapshot_date.desc()).all()
    
    result = {
        "snapshots": [
            {
                "id": s.id,
                "date": s.snapshot_date.isoformat(),
                "total_value": s.total_value,
                "daily_return": s.daily_return,
                "volatility": s.volatility,
                "sharpe_ratio": s.sharpe_ratio
            }
            for s in snapshots
        ],
        "count": len(snapshots)
    }
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        is_error=False
    )


async def _create_snapshot(db: Session, args: dict) -> ToolResult:
    """Create portfolio snapshot"""
    user_id = args.get("user_id")
    
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    total_value = sum(h.total_value for h in holdings)
    
    # Calculate simple daily return (compare to most recent snapshot)
    last_snapshot = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user_id
    ).order_by(PortfolioSnapshot.snapshot_date.desc()).first()
    
    daily_return = 0.0
    if last_snapshot and last_snapshot.total_value > 0:
        daily_return = ((total_value - last_snapshot.total_value) / last_snapshot.total_value) * 100
    
    snapshot = PortfolioSnapshot(
        id=str(__import__("uuid").uuid4()),
        user_id=user_id,
        total_value=total_value,
        daily_return=daily_return,
        snapshot_date=datetime.utcnow()
    )
    
    db.add(snapshot)
    db.commit()
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps({
            "status": "success",
            "snapshot_id": snapshot.id,
            "total_value": total_value,
            "daily_return": daily_return
        }, indent=2))],
        is_error=False
    )


async def _get_allocation(db: Session, args: dict) -> ToolResult:
    """Get asset allocation"""
    user_id = args.get("user_id")
    
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    total_value = sum(h.total_value for h in holdings)
    
    if total_value == 0:
        return ToolResult(
            content=[TextContent(type="text", text=json.dumps({
                "allocation": [],
                "total_value": 0
            }, indent=2))],
            is_error=False
        )
    
    allocation = {
        "allocation": [
            {
                "ticker": h.ticker,
                "value": h.total_value,
                "percentage": (h.total_value / total_value) * 100,
                "quantity": h.quantity
            }
            for h in sorted(holdings, key=lambda x: x.total_value, reverse=True)
        ],
        "total_value": total_value,
        "holding_count": len(holdings)
    }
    
    return ToolResult(
        content=[TextContent(type="text", text=json.dumps(allocation, indent=2))],
        is_error=False
    )


# ==================== SERVER STARTUP ====================

if __name__ == "__main__":
    import asyncio
    asyncio.run(server.run(8765))
