from app.env import load_env_once

# Ensure .env is loaded before other imports need the keys
load_env_once()

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from app.guardrails import input_guardrails, output_guardrails
from app.agents.orchestrator import handle_message
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
    """Get user details"""
    user = db.query(User).filter(User.id == user_id).first()
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
    """Get user's complete portfolio"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    
    portfolio = {
        "user_id": user_id,
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
    """Add holding to portfolio"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found", "status": "error"}
    
    purchase_date = datetime.fromisoformat(holding.purchase_date) if holding.purchase_date else datetime.utcnow()
    
    new_holding = Holding(
        user_id=user_id,
        ticker=holding.ticker.upper(),
        quantity=holding.quantity,
        purchase_price=holding.purchase_price,
        current_price=holding.purchase_price,
        total_value=holding.quantity * holding.purchase_price,
        gain_loss=0.0,
        purchase_date=purchase_date
    )
    
    # Add transaction record
    txn = Transaction(
        user_id=user_id,
        ticker=holding.ticker.upper(),
        transaction_type="BUY",
        quantity=holding.quantity,
        price=holding.purchase_price,
        total_amount=holding.quantity * holding.purchase_price,
        transaction_date=purchase_date
    )
    
    db.add(new_holding)
    db.add(txn)
    
    # Update user portfolio value
    user.portfolio_value = sum(h.total_value for h in db.query(Holding).filter(Holding.user_id == user_id).all()) + (holding.quantity * holding.purchase_price)
    user.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(new_holding)
    
    return {
        "status": "success",
        "holding_id": new_holding.id,
        "message": f"Added {holding.quantity} shares of {holding.ticker}"
    }


@app.get("/users/{user_id}/holdings")
def list_holdings(user_id: str, ticker: Optional[str] = None, db: Session = Depends(get_db)):
    """List holdings"""
    query = db.query(Holding).filter(Holding.user_id == user_id)
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
    """Delete holding"""
    holding = db.query(Holding).filter(Holding.id == holding_id, Holding.user_id == user_id).first()
    if not holding:
        return {"error": "Holding not found", "status": "error"}
    
    db.delete(holding)
    db.commit()
    
    return {"status": "success", "message": f"Deleted {holding.ticker}"}


@app.get("/users/{user_id}/transactions")
def list_transactions(user_id: str, days: int = 90, db: Session = Depends(get_db)):
    """List transactions"""
    from datetime import timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    txns = db.query(Transaction).filter(
        Transaction.user_id == user_id,
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
    """Sync portfolio from external source"""
    user = db.query(User).filter(User.id == user_id).first()
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
    result = await SyncTaskRunner.sync_now(user_id, sync_req.provider, credentials)
    
    return result


@app.post("/users/{user_id}/snapshot")
def create_snapshot(user_id: str, db: Session = Depends(get_db)):
    """Create portfolio snapshot for analytics"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"error": "User not found", "status": "error"}
    
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
    total_value = sum(h.total_value for h in holdings)
    
    snapshot = PortfolioSnapshot(
        user_id=user_id,
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
    """Get asset allocation breakdown"""
    holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
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

    # Handle message with context
    reply, intent, risk = handle_message(msg, conversation_context=context)
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
