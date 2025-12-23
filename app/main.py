from app.env import load_env_once

# Ensure .env is loaded before other imports need the keys
load_env_once()

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.guardrails import input_guardrails, output_guardrails
from app.agents.orchestrator import handle_message
from app.agents.market import get_market_data
from app.agents.strategy import run_dividend_screener, run_growth_screener, run_value_screener
from app.llm import get_gateway_metrics
from app.memory import get_memory
from app.rag.verification import query_rag_with_scores, categorize_answer_source, format_answer_with_sources
from app.database import get_db, User, Holding, Transaction, PortfolioSnapshot, init_db
from app.sync_tasks import SyncTaskRunner
import uuid
from datetime import datetime

# Initialize database
init_db()

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    conversation_id: str = None  # Optional; generates new if not provided
    user_id: str = "user_001"  # User ID for portfolio tracking
    verify_sources: bool = False  # Enable RAG verification in response


# ==================== PORTFOLIO DATABASE ENDPOINTS ====================

class UserCreate(BaseModel):
    email: str
    username: str
    risk_tolerance: str = "MEDIUM"


class HoldingCreate(BaseModel):
    ticker: str
    quantity: float
    purchase_price: float
    purchase_date: Optional[str] = None


class TransactionCreate(BaseModel):
    ticker: str
    transaction_type: str  # BUY, SELL, DIVIDEND
    quantity: float
    price: float
    transaction_date: Optional[str] = None


class SyncRequest(BaseModel):
    provider: str = "mock"  # mock, robinhood, fidelity
    api_token: Optional[str] = None


# Helper function to resolve user by ID or username
def get_user_by_id_or_username(user_id: str, db: Session) -> Optional[User]:
    """
    Resolve user by UUID or username for flexible API access.
    
    Allows frontend users to reference accounts using either:
    - UUID (e.g., "abc123-def-456...") - auto-generated on user creation
    - Username (e.g., "user_002") - user-friendly identifier
    
    This enables simpler frontend UX where users can type "user_002"
    instead of remembering complex UUIDs.
    """
    # Try UUID first (most common case for existing implementations)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user
    # Fallback to username lookup
    user = db.query(User).filter(User.username == user_id).first()
    return user


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user"""
    existing = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if existing:
        return {"error": "User already exists", "status": "error"}
    
    new_user = User(
        email=user.email,
        username=user.username,
        risk_tolerance=user.risk_tolerance
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "status": "success",
        "user_id": new_user.id,
        "email": new_user.email,
        "username": new_user.username
    }


@app.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user details (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "risk_tolerance": user.risk_tolerance,
        "portfolio_value": user.portfolio_value,
        "created_at": user.created_at.isoformat()
    }


@app.get("/users/{user_id}/portfolio")
def get_portfolio(user_id: str, db: Session = Depends(get_db)):
    """Get user's complete portfolio (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    
    portfolio = {
        "user_id": user.id,
        "total_value": sum(h.total_value for h in holdings),
        "total_gain_loss": sum(h.gain_loss for h in holdings),
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
                "gain_loss_pct": round((h.gain_loss / (h.purchase_price * h.quantity) * 100), 2) if h.purchase_price > 0 else 0
            }
            for h in holdings
        ]
    }
    
    if portfolio["total_value"] > 0:
        portfolio["total_return_pct"] = round((portfolio["total_gain_loss"] / (portfolio["total_value"] - portfolio["total_gain_loss"]) * 100), 2)
    
    return portfolio


@app.post("/users/{user_id}/holdings")
def add_holding(user_id: str, holding: HoldingCreate, db: Session = Depends(get_db)):
    """Add holding to portfolio (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    purchase_date = datetime.fromisoformat(holding.purchase_date) if holding.purchase_date else datetime.utcnow()
    ticker = holding.ticker.upper()

    # If holding exists, merge quantities using weighted average cost
    existing = db.query(Holding).filter(Holding.user_id == user.id, Holding.ticker == ticker).first()
    if existing:
        old_qty = existing.quantity
        new_qty = old_qty + holding.quantity
        # Weighted average purchase price
        existing.purchase_price = ((old_qty * existing.purchase_price) + (holding.quantity * holding.purchase_price)) / new_qty
        existing.quantity = new_qty
        existing.current_price = existing.current_price or holding.purchase_price
        existing.total_value = existing.quantity * existing.current_price
        existing.gain_loss = (existing.current_price - existing.purchase_price) * existing.quantity
        existing.updated_at = datetime.utcnow()
        holding_record = existing
    else:
        holding_record = Holding(
            user_id=user.id,
            ticker=ticker,
            quantity=holding.quantity,
            purchase_price=holding.purchase_price,
            current_price=holding.purchase_price,
            total_value=holding.quantity * holding.purchase_price,
            gain_loss=0.0,
            purchase_date=purchase_date
        )
        db.add(holding_record)
    
    # Add transaction record
    txn = Transaction(
        user_id=user.id,
        ticker=ticker,
        transaction_type="BUY",
        quantity=holding.quantity,
        price=holding.purchase_price,
        total_amount=holding.quantity * holding.purchase_price,
        transaction_date=purchase_date
    )
    db.add(txn)
    
    # Update user portfolio value
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    user.portfolio_value = sum(h.total_value for h in holdings)
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(holding_record)
    
    return {
        "status": "success",
        "holding_id": holding_record.id,
        "message": f"Added {holding.quantity} shares of {ticker} (total {holding_record.quantity})"
    }


@app.get("/users/{user_id}/holdings")
def list_holdings(user_id: str, ticker: Optional[str] = None, db: Session = Depends(get_db)):
    """List holdings (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    query = db.query(Holding).filter(Holding.user_id == user.id)
    if ticker:
        query = query.filter(Holding.ticker == ticker.upper())
    
    holdings = query.all()
    
    return {
        "holdings": [
            {
                "id": h.id,
                "ticker": h.ticker,
                "quantity": h.quantity,
                "purchase_price": h.purchase_price,
                "current_price": h.current_price,
                "total_value": h.total_value,
                "gain_loss": h.gain_loss,
                "purchase_date": h.purchase_date.isoformat()
            }
            for h in holdings
        ],
        "total_value": sum(h.total_value for h in holdings)
    }


@app.delete("/users/{user_id}/holdings/{holding_id}")
def delete_holding(user_id: str, holding_id: str, db: Session = Depends(get_db)):
    """Delete holding (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user.id).first()
    if not holding:
        return {"error": "Holding not found", "status": "error"}
    
    db.delete(holding)
    db.commit()
    
    return {"status": "success", "message": f"Deleted {holding.ticker}"}


@app.get("/users/{user_id}/transactions")
def list_transactions(user_id: str, days: int = 3650, db: Session = Depends(get_db)):
    """List transactions (supports UUID or username)"""
    from datetime import timedelta
    
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    txns = db.query(Transaction).filter(
        or_(Transaction.user_id == user.id, Transaction.user_id == user.username),
        Transaction.transaction_date >= cutoff
    ).order_by(Transaction.transaction_date.desc()).all()
    
    return {
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


@app.post("/users/{user_id}/sync")
async def sync_portfolio(user_id: str, sync_req: SyncRequest, db: Session = Depends(get_db)):
    """Sync portfolio from external source (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    credentials = {}
    if sync_req.api_token:
        if sync_req.provider == "robinhood":
            user.robinhood_token = sync_req.api_token
            credentials["robinhood_token"] = sync_req.api_token
        elif sync_req.provider == "fidelity":
            user.fidelity_token = sync_req.api_token
            credentials["fidelity_token"] = sync_req.api_token
        db.commit()
    
    # Trigger sync
    result = await SyncTaskRunner.sync_now(user.id, sync_req.provider, credentials)
    
    return result


@app.post("/users/{user_id}/snapshot")
def create_snapshot(user_id: str, db: Session = Depends(get_db)):
    """Create portfolio snapshot for analytics (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    total_value = sum(h.total_value for h in holdings)
    
    snapshot = PortfolioSnapshot(
        user_id=user.id,
        total_value=total_value
    )
    
    db.add(snapshot)
    db.commit()
    
    return {
        "status": "success",
        "snapshot_id": snapshot.id,
        "total_value": total_value,
        "date": snapshot.snapshot_date.isoformat()
    }


@app.get("/users/{user_id}/allocation")
def get_allocation(user_id: str, db: Session = Depends(get_db)):
    """Get asset allocation breakdown (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    total_value = sum(h.total_value for h in holdings)
    
    if total_value == 0:
        return {"allocation": [], "total_value": 0}
    
    return {
        "allocation": [
            {
                "ticker": h.ticker,
                "value": h.total_value,
                "percentage": round((h.total_value / total_value) * 100, 2),
                "quantity": h.quantity
            }
            for h in sorted(holdings, key=lambda x: x.total_value, reverse=True)
        ],
        "total_value": total_value,
        "holding_count": len(holdings)
    }


@app.post("/chat")
def chat(req: ChatRequest):
    # Use provided conversation_id or generate new one
    conversation_id = req.conversation_id or str(uuid.uuid4())
    
    ok, msg = input_guardrails(req.message)
    if not ok:
        return {
            "reply": msg,
            "conversation_id": conversation_id,
            "intent": None,
            "risk": None,
            "verification": None
        }

    # Get conversation context from memory
    memory = get_memory()
    context = memory.get_context(conversation_id, limit=10)

    # Handle message with context and user_id for portfolio access
    reply, intent, risk = handle_message(msg, conversation_context=context, user_id=req.user_id)
    reply = output_guardrails(reply, risk)

    # Store in conversation memory
    memory.add_message(conversation_id, role="user", content=req.message, intent=intent, risk=risk)
    memory.add_message(conversation_id, role="assistant", content=reply)

    # Verify answer source if requested
    verification = None
    if req.verify_sources:
        rag_results = query_rag_with_scores(msg)
        verification = categorize_answer_source(rag_results, reply)

    return {
        "reply": reply,
        "conversation_id": conversation_id,
        "intent": intent,
        "risk": risk,
        "verification": verification
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Get gateway metrics (cache hit rate, failures, etc.)."""
    return get_gateway_metrics()


@app.post("/users/{user_id}/sync/prices")
async def sync_prices(user_id: str, db: Session = Depends(get_db)):
    """Quick price update for existing holdings (supports UUID or username)"""
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    result = await SyncTaskRunner.sync_price_update(user.id)
    return result


@app.get("/users/{user_id}/analytics")
def get_portfolio_analytics(user_id: str, db: Session = Depends(get_db)):
    """Get portfolio analytics including Sharpe ratio, volatility, diversification (supports UUID or username)"""
    import numpy as np
    
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user.id
    ).order_by(PortfolioSnapshot.snapshot_date.desc()).limit(30).all()
    
    if not holdings:
        return {"error": "No holdings found"}
    
    # Calculate basic metrics
    total_value = sum(h.total_value for h in holdings)
    total_cost = sum(h.purchase_price * h.quantity for h in holdings)
    total_gain_loss = total_value - total_cost
    
    # Diversification (Herfindahl index)
    if total_value > 0:
        concentrations = [(h.total_value / total_value) ** 2 for h in holdings]
        herfindahl = sum(concentrations)
        diversification_score = (1 - herfindahl) * 100  # 0-100 scale
    else:
        diversification_score = 0
    
    # Volatility calculation from snapshots
    if len(snapshots) >= 2:
        returns = []
        for i in range(len(snapshots) - 1):
            if snapshots[i+1].total_value > 0:
                daily_return = (snapshots[i].total_value - snapshots[i+1].total_value) / snapshots[i+1].total_value
                returns.append(daily_return)
        
        if returns:
            volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
            avg_return = np.mean(returns) * 252 * 100  # Annualized
            sharpe = (avg_return - 2.0) / volatility if volatility > 0 else 0  # Assume 2% risk-free rate
        else:
            volatility = 0
            avg_return = 0
            sharpe = 0
    else:
        volatility = 0
        avg_return = 0
        sharpe = 0
    
    return {
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_return": round(total_gain_loss, 2),
        "return_pct": round((total_gain_loss / total_cost * 100) if total_cost > 0 else 0, 2),
        "diversification_score": round(diversification_score, 2),
        "volatility": round(volatility, 2),
        "sharpe_ratio": round(sharpe, 2),
        "holdings_count": len(holdings),
        "largest_position": max([h.total_value / total_value * 100 for h in holdings]) if total_value > 0 else 0
    }


@app.get("/users/{user_id}/performance")
def get_performance_history(user_id: str, days: int = 30, db: Session = Depends(get_db)):
    """Get portfolio performance history (supports UUID or username)"""
    from datetime import timedelta
    
    user = get_user_by_id_or_username(user_id, db)
    if not user:
        return {"error": "User not found", "status": "error"}
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    snapshots = db.query(PortfolioSnapshot).filter(
        PortfolioSnapshot.user_id == user.id,
        PortfolioSnapshot.snapshot_date >= cutoff
    ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()
    
    return {
        "snapshots": [
            {
                "date": s.snapshot_date.isoformat(),
                "value": s.total_value,
                "cash": s.cash_balance,
                "daily_return": s.daily_return,
                "monthly_return": s.monthly_return,
                "yearly_return": s.yearly_return
            }
            for s in snapshots
        ],
        "count": len(snapshots)
    }


@app.post("/verify-rag")
def verify_rag(query: str):
    """
    Verify if a question would get RAG-grounded answers
    Returns: RAG documents with similarity scores and verification analysis
    """
    rag_results = query_rag_with_scores(query)
    verification = categorize_answer_source(rag_results, "")
    
    return {
        "query": query,
        "rag_documents_found": len(rag_results),
        "documents": [
            {
                "text": r["document"][:200] + "..." if len(r["document"]) > 200 else r["document"],
                "similarity_score": r["similarity_score"],
                "full_text": r["document"]
            }
            for r in rag_results
        ],
        "category": verification["category"],
        "confidence": verification["confidence"],
        "warning": verification["warning"],
        "recommendation": verification["recommendation"]
    }


# ==================== MARKET & STRATEGY ENDPOINTS ====================

class MarketQuoteRequest(BaseModel):
    symbols: List[str]


class ScreenerRequest(BaseModel):
    screener_type: str
    params: Optional[dict] = {}


@app.post("/market/quote")
def get_market_quote(req: MarketQuoteRequest):
    """Get real-time quotes for multiple symbols"""
    try:
        quotes = {}
        for symbol in req.symbols:
            data = get_market_data(symbol)
            if data:
                quotes[symbol] = {
                    "price": data.get("price"),
                    "change": data.get("change"),
                    "change_pct": data.get("change_pct"),
                    "volume": data.get("volume"),
                    "market_cap": data.get("market_cap")
                }
        return {"quotes": quotes, "count": len(quotes)}
    except Exception as e:
        return {"error": str(e), "quotes": {}}


@app.post("/market/screen")
def run_screener(req: ScreenerRequest, db: Session = Depends(get_db)):
    """Run stock screener (supports UUID or username in params)"""
    try:
        # Get user's holdings for context
        user_id_param = req.params.get("user_id", "user_001")
        user = get_user_by_id_or_username(user_id_param, db)
        
        if user:
            holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
            holdings_dict = {h.ticker: {"quantity": h.quantity, "purchase_price": h.purchase_price} for h in holdings}
        else:
            holdings_dict = {}
        
        if req.screener_type.lower() == "dividend":
            results = run_dividend_screener(holdings_dict)
        elif req.screener_type.lower() == "growth":
            results = run_growth_screener(holdings_dict)
        elif req.screener_type.lower() == "value":
            results = run_value_screener(holdings_dict)
        else:
            results = {"error": "Unknown screener type"}
        
        return results
    except Exception as e:
        return {"error": str(e), "results": []}


@app.get("/strategy/ideas")
def get_strategy_ideas(risk_level: str = "MEDIUM"):
    """Get investment strategy ideas based on risk level"""
    strategies = {
        "LOW": [
            {
                "name": "Dividend Aristocrats",
                "description": "Companies with 25+ years of consecutive dividend increases",
                "tickers": ["JNJ", "PG", "KO", "MCD", "WMT"],
                "allocation": "30-40%",
                "risk": "LOW"
            },
            {
                "name": "Investment Grade Bonds",
                "description": "High-quality corporate and government bonds",
                "tickers": ["AGG", "BND", "VCIT"],
                "allocation": "40-50%",
                "risk": "LOW"
            }
        ],
        "MEDIUM": [
            {
                "name": "S&P 500 Index",
                "description": "Broad market exposure through index funds",
                "tickers": ["SPY", "VOO", "IVV"],
                "allocation": "40-50%",
                "risk": "MEDIUM"
            },
            {
                "name": "Balanced Growth",
                "description": "Mix of growth and value stocks",
                "tickers": ["VUG", "VTV", "SCHD"],
                "allocation": "30-40%",
                "risk": "MEDIUM"
            }
        ],
        "HIGH": [
            {
                "name": "AI & Technology",
                "description": "High-growth tech and AI companies",
                "tickers": ["NVDA", "MSFT", "GOOGL", "META"],
                "allocation": "30-40%",
                "risk": "HIGH"
            },
            {
                "name": "Emerging Markets",
                "description": "Growth opportunities in developing economies",
                "tickers": ["VWO", "IEMG", "EEM"],
                "allocation": "15-20%",
                "risk": "HIGH"
            }
        ]
    }
    
    return {
        "risk_level": risk_level,
        "strategies": strategies.get(risk_level, strategies["MEDIUM"])
    }

