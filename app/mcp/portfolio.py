"""Portfolio MCP Server - Provides portfolio data to agents.

This server implements tools for:
- Getting user holdings
- Getting user profile (risk tolerance, goals)
- Recording transactions
- Getting performance history
- Getting dividend history

Uses hardcoded/mock data now; will connect to PostgreSQL database later.
"""

from typing import Optional, Dict, List
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


# ============================================================================
# HARDCODED DATA - Replace with database queries later
# ============================================================================

# Mock user profiles
MOCK_USER_PROFILES = {
    "user_123": {
        "user_id": "user_123",
        "name": "John Investor",
        "email": "john@example.com",
        "risk_tolerance": "moderate",  # conservative, moderate, aggressive
        "investment_horizon": "long_term",  # short_term, medium_term, long_term
        "annual_income": 120000,
        "investment_goals": ["wealth_building", "retirement"],
        "max_single_position": 40,  # percent
        "min_cash_reserve": 10,  # percent
        "preferred_sectors": ["technology", "healthcare", "finance"],
        "avoid_sectors": ["utilities"],
        "created_at": "2024-01-15",
        "last_updated": "2024-12-15"
    }
}

# Mock user holdings (current positions)
MOCK_HOLDINGS = {
    "user_123": {
        "AAPL": {"quantity": 100, "purchase_price": 150, "purchase_date": "2024-01-10"},
        "MSFT": {"quantity": 50, "purchase_price": 300, "purchase_date": "2024-02-15"},
        "GOOGL": {"quantity": 25, "purchase_price": 100, "purchase_date": "2024-03-20"},
        "JNJ": {"quantity": 40, "purchase_price": 150, "purchase_date": "2024-04-05"},
        "TSLA": {"quantity": 20, "purchase_price": 250, "purchase_date": "2024-05-12"},
        "CASH": {"quantity": 50000, "purchase_price": 1, "purchase_date": "2024-01-01"}
    }
}

# Mock transactions
MOCK_TRANSACTIONS = {
    "user_123": [
        {
            "id": "txn_001",
            "date": "2024-01-10",
            "type": "buy",
            "ticker": "AAPL",
            "quantity": 100,
            "price": 150,
            "amount": 15000,
            "notes": "Initial investment"
        },
        {
            "id": "txn_002",
            "date": "2024-02-15",
            "type": "buy",
            "ticker": "MSFT",
            "quantity": 50,
            "price": 300,
            "amount": 15000,
            "notes": "Tech diversification"
        },
        {
            "id": "txn_003",
            "date": "2024-03-20",
            "type": "buy",
            "ticker": "GOOGL",
            "quantity": 25,
            "price": 100,
            "amount": 2500,
            "notes": "Google position"
        },
        {
            "id": "txn_004",
            "date": "2024-04-05",
            "type": "buy",
            "ticker": "JNJ",
            "quantity": 40,
            "price": 150,
            "amount": 6000,
            "notes": "Healthcare dividend play"
        },
        {
            "id": "txn_005",
            "date": "2024-05-12",
            "type": "buy",
            "ticker": "TSLA",
            "quantity": 20,
            "price": 250,
            "amount": 5000,
            "notes": "Growth position"
        },
        {
            "id": "txn_006",
            "date": "2024-06-15",
            "type": "dividend",
            "ticker": "JNJ",
            "quantity": 40,
            "amount": 240,
            "notes": "Q2 dividend distribution"
        },
        {
            "id": "txn_007",
            "date": "2024-09-15",
            "type": "dividend",
            "ticker": "JNJ",
            "quantity": 40,
            "amount": 240,
            "notes": "Q3 dividend distribution"
        }
    ]
}

# Mock performance metrics (daily prices for last 30 days, simplified)
MOCK_PERFORMANCE = {
    "user_123": {
        "AAPL": {
            "current_price": 180,
            "prices_last_30_days": [150, 155, 160, 158, 162, 165, 168, 170, 172, 175, 
                                    178, 180, 179, 181, 180, 182, 184, 183, 185, 187,
                                    189, 188, 190, 192, 194, 195, 196, 197, 198, 180],
            "dividend_yield": 0.5,
            "52week_high": 199,
            "52week_low": 140
        },
        "MSFT": {
            "current_price": 350,
            "prices_last_30_days": [300, 305, 310, 315, 320, 325, 330, 335, 340, 345,
                                    350, 348, 352, 355, 358, 360, 362, 365, 367, 370,
                                    372, 375, 378, 380, 382, 385, 387, 390, 350, 350],
            "dividend_yield": 0.8,
            "52week_high": 400,
            "52week_low": 280
        },
        "GOOGL": {
            "current_price": 140,
            "prices_last_30_days": [100, 105, 110, 115, 120, 125, 130, 128, 135, 138,
                                    140, 142, 145, 143, 147, 150, 152, 155, 157, 160,
                                    162, 165, 168, 170, 172, 175, 177, 180, 140, 140],
            "dividend_yield": 0,
            "52week_high": 185,
            "52week_low": 95
        },
        "JNJ": {
            "current_price": 160,
            "prices_last_30_days": [150, 150, 151, 152, 151, 152, 153, 154, 155, 156,
                                    157, 158, 159, 160, 159, 160, 161, 162, 161, 162,
                                    163, 164, 163, 164, 165, 164, 165, 166, 160, 160],
            "dividend_yield": 2.5,
            "52week_high": 170,
            "52week_low": 145
        },
        "TSLA": {
            "current_price": 280,
            "prices_last_30_days": [250, 255, 260, 265, 270, 268, 275, 280, 278, 285,
                                    290, 288, 295, 300, 298, 305, 310, 308, 315, 320,
                                    325, 330, 335, 340, 345, 342, 348, 350, 280, 280],
            "dividend_yield": 0,
            "52week_high": 400,
            "52week_low": 200
        }
    }
}


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def get_user_holdings(user_id: str) -> Dict:
    """Get current holdings for a user.
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        dict with holdings data
    """
    try:
        if user_id not in MOCK_HOLDINGS:
            logger.warning(f"No holdings found for user {user_id}")
            return {
                "error": f"No holdings found for user {user_id}",
                "user_id": user_id,
                "holdings": {},
                "total_shares_value": 0,
                "total_cash": 0,
                "total_portfolio_value": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        holdings = MOCK_HOLDINGS[user_id]
        
        # Calculate totals
        total_shares_value = 0
        total_cash = 0
        performance = MOCK_PERFORMANCE.get(user_id, {})
        
        formatted_holdings = {}
        for ticker, holding in holdings.items():
            quantity = holding['quantity']
            purchase_price = holding['purchase_price']
            
            if ticker == "CASH":
                total_cash = quantity
            else:
                # Get current price from performance data
                current_price = performance.get(ticker, {}).get('current_price', purchase_price)
                current_value = quantity * current_price
                gain_loss = (current_price - purchase_price) * quantity
                gain_loss_pct = ((current_price - purchase_price) / purchase_price * 100) if purchase_price > 0 else 0
                
                total_shares_value += current_value
                
                formatted_holdings[ticker] = {
                    "quantity": quantity,
                    "purchase_price": round(purchase_price, 2),
                    "current_price": round(current_price, 2),
                    "current_value": round(current_value, 2),
                    "gain_loss": round(gain_loss, 2),
                    "gain_loss_pct": round(gain_loss_pct, 2),
                    "purchase_date": holding['purchase_date']
                }
        
        return {
            "error": None,
            "user_id": user_id,
            "holdings": formatted_holdings,
            "total_shares_value": round(total_shares_value, 2),
            "total_cash": round(total_cash, 2),
            "total_portfolio_value": round(total_shares_value + total_cash, 2),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting holdings for user {user_id}: {e}")
        return {
            "error": str(e),
            "holdings": {},
            "total_shares_value": 0,
            "total_cash": 0,
            "total_portfolio_value": 0
        }


def get_user_profile(user_id: str) -> Dict:
    """Get user profile including risk tolerance and investment goals.
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        dict with user profile data
    """
    try:
        if user_id not in MOCK_USER_PROFILES:
            logger.warning(f"No profile found for user {user_id}")
            return {
                "error": f"No profile found for user {user_id}",
                "profile": None
            }
        
        profile = MOCK_USER_PROFILES[user_id]
        
        return {
            "error": None,
            "user_id": user_id,
            "profile": profile,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting profile for user {user_id}: {e}")
        return {
            "error": str(e),
            "profile": None
        }


def record_transaction(user_id: str, ticker: str, transaction_type: str, 
                      quantity: int, price: float, notes: str = "") -> Dict:
    """Record a transaction (buy, sell, dividend, etc).
    
    Args:
        user_id: Unique user identifier
        ticker: Stock ticker symbol
        transaction_type: "buy", "sell", "dividend", "transfer"
        quantity: Number of shares or amount
        price: Price per share
        notes: Optional notes
    
    Returns:
        dict with transaction confirmation
    """
    try:
        # Validate input
        if transaction_type not in ["buy", "sell", "dividend", "transfer"]:
            return {
                "error": f"Invalid transaction type: {transaction_type}",
                "transaction": None
            }
        
        # Initialize user transactions if not exists
        if user_id not in MOCK_TRANSACTIONS:
            MOCK_TRANSACTIONS[user_id] = []
        
        # Create transaction
        txn_id = f"txn_{len(MOCK_TRANSACTIONS[user_id]) + 1:03d}"
        amount = quantity * price
        
        transaction = {
            "id": txn_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": transaction_type,
            "ticker": ticker,
            "quantity": quantity,
            "price": round(price, 2),
            "amount": round(amount, 2),
            "notes": notes
        }
        
        # Add to transactions
        MOCK_TRANSACTIONS[user_id].append(transaction)
        
        # Update holdings (simplified - in production, use database)
        if user_id not in MOCK_HOLDINGS:
            MOCK_HOLDINGS[user_id] = {}
        
        holdings = MOCK_HOLDINGS[user_id]
        
        if transaction_type == "buy":
            if ticker not in holdings:
                holdings[ticker] = {
                    "quantity": 0,
                    "purchase_price": price,
                    "purchase_date": datetime.now().strftime("%Y-%m-%d")
                }
            holdings[ticker]["quantity"] += quantity
        
        elif transaction_type == "sell":
            if ticker in holdings:
                holdings[ticker]["quantity"] -= quantity
                if holdings[ticker]["quantity"] <= 0:
                    del holdings[ticker]
        
        logger.info(f"Transaction recorded: {txn_id} for user {user_id}")
        
        return {
            "error": None,
            "transaction": transaction,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error recording transaction for user {user_id}: {e}")
        return {
            "error": str(e),
            "transaction": None
        }


def get_transaction_history(user_id: str, days: Optional[int] = None, 
                           transaction_type: Optional[str] = None) -> Dict:
    """Get transaction history for a user.
    
    Args:
        user_id: Unique user identifier
        days: Optional - filter to last N days (None = all)
        transaction_type: Optional - filter by type (buy, sell, dividend, etc)
    
    Returns:
        dict with transactions
    """
    try:
        if user_id not in MOCK_TRANSACTIONS:
            logger.warning(f"No transactions found for user {user_id}")
            return {
                "error": None,
                "user_id": user_id,
                "transactions": [],
                "total_transactions": 0
            }
        
        transactions = MOCK_TRANSACTIONS[user_id]
        
        # Filter by date if specified
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            transactions = [
                t for t in transactions
                if datetime.strptime(t['date'], "%Y-%m-%d") >= cutoff_date
            ]
        
        # Filter by type if specified
        if transaction_type:
            transactions = [
                t for t in transactions
                if t['type'] == transaction_type
            ]
        
        # Sort by date descending (newest first)
        transactions.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            "error": None,
            "user_id": user_id,
            "transactions": transactions,
            "total_transactions": len(transactions),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting transaction history for user {user_id}: {e}")
        return {
            "error": str(e),
            "transactions": [],
            "total_transactions": 0
        }


def get_dividend_history(user_id: str, days: Optional[int] = 365) -> Dict:
    """Get dividend history for a user.
    
    Args:
        user_id: Unique user identifier
        days: Optional - filter to last N days (default: 365 = 1 year)
    
    Returns:
        dict with dividend transactions
    """
    try:
        # Get transaction history filtered for dividends
        history = get_transaction_history(user_id, days=days, transaction_type="dividend")
        
        if history['error']:
            return history
        
        # Calculate dividend summary
        total_dividends = sum(t['amount'] for t in history['transactions'])
        dividends_by_ticker = {}
        
        for txn in history['transactions']:
            ticker = txn['ticker']
            if ticker not in dividends_by_ticker:
                dividends_by_ticker[ticker] = {
                    "total_amount": 0,
                    "transaction_count": 0,
                    "latest_date": None
                }
            dividends_by_ticker[ticker]["total_amount"] += txn['amount']
            dividends_by_ticker[ticker]["transaction_count"] += 1
            dividends_by_ticker[ticker]["latest_date"] = txn['date']
        
        return {
            "error": None,
            "user_id": user_id,
            "dividend_transactions": history['transactions'],
            "total_dividends_period": round(total_dividends, 2),
            "dividends_by_ticker": dividends_by_ticker,
            "period_days": days,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting dividend history for user {user_id}: {e}")
        return {
            "error": str(e),
            "dividend_transactions": [],
            "total_dividends_period": 0,
            "dividends_by_ticker": {}
        }


def get_performance_metrics(user_id: str, ticker: Optional[str] = None) -> Dict:
    """Get performance metrics for user's holdings.
    
    Args:
        user_id: Unique user identifier
        ticker: Optional - get metrics for specific ticker (None = all)
    
    Returns:
        dict with performance data
    """
    try:
        if user_id not in MOCK_PERFORMANCE:
            return {
                "error": f"No performance data for user {user_id}",
                "metrics": {}
            }
        
        performance_data = MOCK_PERFORMANCE[user_id]
        
        if ticker:
            if ticker not in performance_data:
                return {
                    "error": f"No performance data for ticker {ticker}",
                    "metrics": {}
                }
            
            metrics = performance_data[ticker]
            return {
                "error": None,
                "user_id": user_id,
                "ticker": ticker,
                "metrics": metrics,
                "timestamp": datetime.now().isoformat()
            }
        
        # Return all metrics
        return {
            "error": None,
            "user_id": user_id,
            "metrics": performance_data,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error getting performance metrics for user {user_id}: {e}")
        return {
            "error": str(e),
            "metrics": {}
        }


# ============================================================================
# PORTFOLIO CLIENT - Used by agents
# ============================================================================

class PortfolioClient:
    """Client for accessing portfolio data.
    
    Agents use this to fetch user data without direct database access.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def get_holdings(self) -> Dict:
        """Get user's current holdings."""
        return get_user_holdings(self.user_id)
    
    def get_profile(self) -> Dict:
        """Get user's profile."""
        return get_user_profile(self.user_id)
    
    def get_transactions(self, days: Optional[int] = None) -> Dict:
        """Get user's transaction history."""
        return get_transaction_history(self.user_id, days=days)
    
    def get_dividends(self, days: Optional[int] = 365) -> Dict:
        """Get user's dividend history."""
        return get_dividend_history(self.user_id, days=days)
    
    def get_performance(self, ticker: Optional[str] = None) -> Dict:
        """Get user's performance metrics."""
        return get_performance_metrics(self.user_id, ticker=ticker)
    
    def record_buy(self, ticker: str, quantity: int, price: float, notes: str = "") -> Dict:
        """Record a buy transaction."""
        return record_transaction(self.user_id, ticker, "buy", quantity, price, notes)
    
    def record_sell(self, ticker: str, quantity: int, price: float, notes: str = "") -> Dict:
        """Record a sell transaction."""
        return record_transaction(self.user_id, ticker, "sell", quantity, price, notes)
    
    def record_dividend(self, ticker: str, amount: float, notes: str = "") -> Dict:
        """Record a dividend distribution."""
        return record_transaction(self.user_id, ticker, "dividend", 1, amount, notes)


import os


def get_portfolio_client(user_id: str = "user_123") -> PortfolioClient:
    """Factory function to get a portfolio client for a user.

    This factory supports multiple backends via the `PORTFOLIO_BACKEND` env var:
      - `mock` (default): returns the internal `PortfolioClient` backed by mock data
      - `external`: returns an `ExternalPortfolioClient` (skeleton adapter)

    The external adapter lives in `app.mcp.adapters.external_portfolio` and is
    intentionally a lightweight skeleton until an external service is configured.
    """
    backend = os.getenv("PORTFOLIO_BACKEND", "mock").lower()

    if backend == "external":
        try:
            from app.mcp.adapters.external_portfolio import ExternalPortfolioClient
            return ExternalPortfolioClient(user_id)
        except Exception as e:
            logger.error(f"Failed to load ExternalPortfolioClient: {e}")
            # Fall back to mock client to keep system operational
            return PortfolioClient(user_id)

    # Default: mock/internal client
    return PortfolioClient(user_id)
