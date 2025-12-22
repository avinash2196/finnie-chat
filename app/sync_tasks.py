"""
Background tasks for syncing portfolio with external services
Uses APScheduler for scheduled syncs
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database import SessionLocal, User, SyncLog
from app.providers import sync_portfolio, PortfolioProviderFactory
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioSyncScheduler:
    """Manages scheduled portfolio syncs"""
    
    def __init__(self):
        self.is_running = False
        self.sync_interval_minutes = 60  # Sync every hour
    
    async def start(self):
        """Start background sync scheduler"""
        self.is_running = True
        logger.info("🔄 Portfolio sync scheduler started")
        
        while self.is_running:
            try:
                await self.sync_all_users()
            except Exception as e:
                logger.error(f"❌ Sync error: {str(e)}")
            
            # Wait before next sync
            await asyncio.sleep(self.sync_interval_minutes * 60)
    
    async def stop(self):
        """Stop background sync scheduler"""
        self.is_running = False
        logger.info("🛑 Portfolio sync scheduler stopped")
    
    async def sync_all_users(self):
        """Sync all users' portfolios from their configured sources"""
        db = SessionLocal()
        try:
            users = db.query(User).filter(User.robinhood_token.isnot(None) | User.fidelity_token.isnot(None)).all()
            logger.info(f"Syncing {len(users)} users...")
            
            for user in users:
                await self.sync_user_portfolio(db, user)
            
        except Exception as e:
            logger.error(f"Error in sync_all_users: {str(e)}")
        finally:
            db.close()
    
    async def sync_user_portfolio(self, db, user: User):
        """Sync a specific user's portfolio"""
        try:
            provider_type = "mock"
            credentials = {}
            
            # Determine which provider to use
            if user.robinhood_token:
                provider_type = "robinhood"
                credentials["robinhood_token"] = user.robinhood_token
            elif user.fidelity_token:
                provider_type = "fidelity"
                credentials["fidelity_token"] = user.fidelity_token
            
            logger.info(f"Syncing {user.email} from {provider_type}...")
            
            result = await sync_portfolio(user.id, db, provider_type, credentials)
            
            if result["status"] == "SUCCESS":
                logger.info(f"✅ {user.email}: Synced {result['synced_items']} holdings")
            else:
                logger.warning(f"⚠️ {user.email}: {result['message']}")
        
        except Exception as e:
            logger.error(f"Error syncing {user.email}: {str(e)}")


class SyncTaskRunner:
    """One-off sync task runner (for API calls)"""
    
    @staticmethod
    async def sync_now(user_id: str, provider_type: str = "mock", credentials: dict = None) -> dict:
        """
        Trigger immediate sync for a user
        Returns sync result
        """
        db = SessionLocal()
        try:
            logger.info(f"Triggering manual sync for user {user_id} from {provider_type}")
            
            result = await sync_portfolio(user_id, db, provider_type, credentials or {})
            
            logger.info(f"Sync result: {result['status']}")
            return result
        
        finally:
            db.close()
    
    @staticmethod
    async def sync_price_update(user_id: str) -> dict:
        """Update current prices for user's holdings (lightweight sync)"""
        db = SessionLocal()
        try:
            from app.database import Holding
            from app.providers import PortfolioProviderFactory
            
            holdings = db.query(Holding).filter(Holding.user_id == user_id).all()
            if not holdings:
                return {"status": "SUCCESS", "updated_holdings": 0, "message": "No holdings to update"}
            
            tickers = [h.ticker for h in holdings]
            
            # Use mock provider to get prices (in production, could use yfinance or other source)
            provider = PortfolioProviderFactory.get_provider("mock")
            prices = await provider.get_current_prices(tickers)
            
            # Update prices
            for holding in holdings:
                if holding.ticker in prices:
                    new_price = prices[holding.ticker]
                    old_price = holding.current_price
                    
                    holding.current_price = new_price
                    holding.total_value = holding.quantity * new_price
                    holding.gain_loss = (new_price - holding.purchase_price) * holding.quantity
                    holding.updated_at = datetime.utcnow()
                    
                    logger.info(f"Updated {holding.ticker}: ${old_price} → ${new_price}")
            
            db.commit()
            
            return {
                "status": "SUCCESS",
                "updated_holdings": len(holdings),
                "message": f"Updated prices for {len(holdings)} holdings"
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating prices: {str(e)}")
            return {"status": "FAILED", "message": str(e)}
        
        finally:
            db.close()
    
    @staticmethod
    async def create_daily_snapshots() -> dict:
        """Create daily snapshots for all users (for analytics)"""
        db = SessionLocal()
        try:
            from app.database import Holding, PortfolioSnapshot, User
            
            users = db.query(User).all()
            created_count = 0
            
            for user in users:
                holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
                total_value = sum(h.total_value for h in holdings)
                
                if total_value > 0:
                    snapshot = PortfolioSnapshot(
                        user_id=user.id,
                        total_value=total_value,
                        snapshot_date=datetime.utcnow()
                    )
                    db.add(snapshot)
                    created_count += 1
            
            db.commit()
            logger.info(f"Created {created_count} daily snapshots")
            
            return {
                "status": "SUCCESS",
                "snapshots_created": created_count
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating snapshots: {str(e)}")
            return {"status": "FAILED", "message": str(e)}
        
        finally:
            db.close()


# Global scheduler instance
_scheduler: Optional[PortfolioSyncScheduler] = None


def get_scheduler() -> PortfolioSyncScheduler:
    """Get or create global scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = PortfolioSyncScheduler()
    return _scheduler


async def start_scheduler():
    """Start global scheduler"""
    scheduler = get_scheduler()
    if not scheduler.is_running:
        asyncio.create_task(scheduler.start())


async def stop_scheduler():
    """Stop global scheduler"""
    scheduler = get_scheduler()
    await scheduler.stop()
