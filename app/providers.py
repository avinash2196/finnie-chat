"""
Provider pattern for portfolio data - supports mock and real external APIs
Allows switching between sources without code changes
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import json
import httpx
from app.database import Holding, Transaction, PortfolioSnapshot, SyncLog
from sqlalchemy.orm import Session
import uuid
import random
import asyncio


class PortfolioProvider(ABC):
    """Abstract base class for portfolio data providers"""
    
    @abstractmethod
    async def get_holdings(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch holdings from source"""
        pass
    
    @abstractmethod
    async def get_transactions(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch transactions from source"""
        pass
    
    @abstractmethod
    async def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current prices for list of tickers"""
        pass


class MockPortfolioProvider(PortfolioProvider):
    """Mock provider for development/testing"""
    
    SAMPLE_HOLDINGS = [
        {"ticker": "AAPL", "quantity": 10, "purchase_price": 150.0},
        {"ticker": "MSFT", "quantity": 5, "purchase_price": 350.0},
        {"ticker": "GOOGL", "quantity": 2, "purchase_price": 2800.0},
        {"ticker": "TSLA", "quantity": 3, "purchase_price": 900.0},
        {"ticker": "VOO", "quantity": 20, "purchase_price": 400.0},  # S&P 500 ETF
    ]
    
    SAMPLE_PRICES = {
        "AAPL": 192.5, "MSFT": 445.0, "GOOGL": 3150.0, 
        "TSLA": 920.0, "VOO": 475.0, "BRK.B": 410.0
    }
    
    async def get_holdings(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Return mock holdings"""
        # Simulate slight price variation
        holdings = []
        for h in self.SAMPLE_HOLDINGS:
            holdings.append({
                **h,
                "current_price": self.SAMPLE_PRICES[h["ticker"]] * (0.98 + random.random() * 0.04)
            })
        return holdings
    
    async def get_transactions(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Return mock transactions"""
        return [
            {
                "ticker": "AAPL",
                "type": "BUY",
                "quantity": 10,
                "price": 150.0,
                "date": "2024-01-15",
                "total": 1500.0
            },
            {
                "ticker": "MSFT",
                "type": "BUY",
                "quantity": 5,
                "price": 350.0,
                "date": "2024-02-20",
                "total": 1750.0
            },
            {
                "ticker": "AAPL",
                "type": "DIVIDEND",
                "quantity": 10,
                "price": 0.25,
                "date": "2024-03-15",
                "total": 2.5
            }
        ]
    
    async def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Return mock current prices"""
        return {
            ticker: self.SAMPLE_PRICES.get(ticker, 100.0)
            for ticker in tickers
        }


class RobinhoodPortfolioProvider(PortfolioProvider):
    """Robinhood API provider"""
    
    BASE_URL = "https://api.robinhood.com"
    
    async def get_holdings(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch holdings from Robinhood"""
        token = credentials.get("robinhood_token")
        if not token:
            raise ValueError("Robinhood token not provided")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.BASE_URL}/positions/",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Transform Robinhood format to standard format
                holdings = []
                for position in data.get("results", []):
                    holdings.append({
                        "ticker": position["instrument"].split("/")[-2],
                        "quantity": float(position["quantity"]),
                        "purchase_price": float(position["average_buy_price"]),
                        "current_price": float(position["last_trade_price"]),
                    })
                return holdings
            except httpx.RequestError as e:
                raise Exception(f"Robinhood API error: {str(e)}")
    
    async def get_transactions(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch transactions from Robinhood"""
        token = credentials.get("robinhood_token")
        if not token:
            raise ValueError("Robinhood token not provided")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.BASE_URL}/orders/",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                transactions = []
                for order in data.get("results", []):
                    transactions.append({
                        "ticker": order["instrument"].split("/")[-2],
                        "type": "BUY" if order["side"] == "buy" else "SELL",
                        "quantity": float(order["quantity"]),
                        "price": float(order["price"]),
                        "date": order["created_at"],
                        "total": float(order["quantity"]) * float(order["price"]),
                    })
                return transactions
            except httpx.RequestError as e:
                raise Exception(f"Robinhood API error: {str(e)}")
    
    async def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current prices from Robinhood quotes"""
        async with httpx.AsyncClient() as client:
            try:
                headers = {}
                ticker_params = ",".join(tickers)
                response = await client.get(
                    f"{self.BASE_URL}/quotes/",
                    params={"symbols": ticker_params},
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                prices = {}
                for quote in data.get("results", []):
                    prices[quote["symbol"]] = float(quote["last_trade_price"])
                return prices
            except httpx.RequestError as e:
                raise Exception(f"Robinhood API error: {str(e)}")


class FidelityPortfolioProvider(PortfolioProvider):
    """Fidelity API provider"""
    
    BASE_URL = "https://api.fidelity.com/api/v1"
    
    async def get_holdings(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch holdings from Fidelity"""
        token = credentials.get("fidelity_token")
        if not token:
            raise ValueError("Fidelity token not provided")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.BASE_URL}/accounts/holdings",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                holdings = []
                for holding in data.get("holdings", []):
                    holdings.append({
                        "ticker": holding["symbol"],
                        "quantity": float(holding["quantity"]),
                        "purchase_price": float(holding["cost_basis"]) / float(holding["quantity"]),
                        "current_price": float(holding["current_price"]),
                    })
                return holdings
            except httpx.RequestError as e:
                raise Exception(f"Fidelity API error: {str(e)}")
    
    async def get_transactions(self, user_id: str, credentials: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch transactions from Fidelity"""
        token = credentials.get("fidelity_token")
        if not token:
            raise ValueError("Fidelity token not provided")
        
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.BASE_URL}/accounts/transactions",
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                transactions = []
                for txn in data.get("transactions", []):
                    transactions.append({
                        "ticker": txn["symbol"],
                        "type": txn["type"].upper(),
                        "quantity": float(txn["quantity"]),
                        "price": float(txn["price"]),
                        "date": txn["date"],
                        "total": float(txn["total"]),
                    })
                return transactions
            except httpx.RequestError as e:
                raise Exception(f"Fidelity API error: {str(e)}")
    
    async def get_current_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get current prices from Fidelity"""
        async with httpx.AsyncClient() as client:
            try:
                headers = {}
                response = await client.get(
                    f"{self.BASE_URL}/quotes",
                    params={"symbols": ",".join(tickers)},
                    headers=headers,
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                prices = {}
                for quote in data.get("quotes", []):
                    prices[quote["symbol"]] = float(quote["price"])
                return prices
            except httpx.RequestError as e:
                raise Exception(f"Fidelity API error: {str(e)}")


class PortfolioProviderFactory:
    """Factory to select appropriate provider"""
    
    PROVIDERS = {
        "mock": MockPortfolioProvider,
        "robinhood": RobinhoodPortfolioProvider,
        "fidelity": FidelityPortfolioProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_type: str = "mock") -> PortfolioProvider:
        """Get provider instance"""
        provider_class = cls.PROVIDERS.get(provider_type.lower(), MockPortfolioProvider)
        return provider_class()
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register custom provider"""
        cls.PROVIDERS[name] = provider_class


# ==================== SYNC FUNCTIONS ====================

async def sync_portfolio(
    user_id: str,
    db: Session,
    provider_type: str = "mock",
    credentials: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Sync portfolio from external source
    Returns sync result with statistics
    """
    from app.database import User
    
    start_time = datetime.utcnow()
    sync_log = SyncLog(
        user_id=user_id,
        source=provider_type.upper(),
        status="PENDING",
        synced_items=0,
    )
    
    try:
        provider = PortfolioProviderFactory.get_provider(provider_type)
        
        # Fetch data
        holdings_data = await provider.get_holdings(user_id, credentials or {})
        transactions_data = await provider.get_transactions(user_id, credentials or {})
        
        # Get current prices
        tickers = [h["ticker"] for h in holdings_data]
        prices = await provider.get_current_prices(tickers)
        
        # Update or create holdings
        existing_holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
        existing_tickers = {h.ticker for h in existing_holdings}
        
        for holding_data in holdings_data:
            ticker = holding_data["ticker"]
            current_price = prices.get(ticker, holding_data.get("current_price", 0))
            
            # Find existing or create new
            holding = next((h for h in existing_holdings if h.ticker == ticker), None)
            if holding:
                # For mock provider, preserve manual quantities/prices; only refresh pricing
                if provider_type.lower() == "mock":
                    qty = holding.quantity
                    cost = holding.purchase_price
                else:
                    qty = holding_data["quantity"]
                    cost = holding_data["purchase_price"]

                holding.quantity = qty
                holding.purchase_price = cost
                holding.current_price = current_price
                holding.total_value = qty * current_price
                holding.gain_loss = (current_price - cost) * qty
                holding.updated_at = datetime.utcnow()
            else:
                holding = Holding(
                    user_id=user_id,
                    ticker=ticker,
                    quantity=holding_data["quantity"],
                    purchase_price=holding_data["purchase_price"],
                    current_price=current_price,
                    total_value=holding_data["quantity"] * current_price,
                    gain_loss=(current_price - holding_data["purchase_price"]) * holding_data["quantity"],
                    purchase_date=datetime.fromisoformat(holding_data.get("purchase_date", datetime.utcnow().isoformat()))
                )
                db.add(holding)
            
            sync_log.synced_items += 1
        
        # Update or create transactions
        existing_txns = db.query(Transaction).filter(Transaction.user_id == user_id).all()
        for txn_data in transactions_data:
            # Check if already exists
            exists = any(
                t.ticker == txn_data["ticker"] and
                t.transaction_date.date() == datetime.fromisoformat(txn_data["date"]).date()
                for t in existing_txns
            )
            
            if not exists:
                transaction = Transaction(
                    user_id=user_id,
                    ticker=txn_data["ticker"],
                    transaction_type=txn_data["type"],
                    quantity=txn_data["quantity"],
                    price=txn_data["price"],
                    total_amount=txn_data["total"],
                    transaction_date=datetime.fromisoformat(txn_data["date"]),
                )
                db.add(transaction)
        
        # Update user portfolio value
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Refresh holdings to get latest values
            all_holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
            total = sum(h.total_value for h in all_holdings)
            user.portfolio_value = total
            user.updated_at = datetime.utcnow()
            db.flush()  # Ensure update is flushed
        
        db.commit()
        
        # Log success
        sync_log.status = "SUCCESS"
        sync_log.message = f"Synced {sync_log.synced_items} holdings"
        sync_log.sync_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
    except Exception as e:
        db.rollback()
        sync_log.status = "FAILED"
        sync_log.message = str(e)
        sync_log.sync_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    finally:
        db.add(sync_log)
        db.commit()
    
    return {
        "status": sync_log.status,
        "source": sync_log.source,
        "synced_items": sync_log.synced_items,
        "message": sync_log.message,
        "sync_time_ms": sync_log.sync_time_ms,
    }
