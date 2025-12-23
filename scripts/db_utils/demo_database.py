"""
Quick demo of database integration
Shows complete workflow: create user -> sync from mock -> view portfolio
"""
import asyncio
from app.database import SessionLocal, User, init_db
from app.providers import sync_portfolio


async def demo():
    """Demonstrate complete workflow"""
    
    # Initialize database
    print("🗄️  Initializing database...")
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # 1. Create user
        print("\n👤 Creating user...")
        user = User(
            email="demo@example.com",
            username="demo_user",
            risk_tolerance="MEDIUM"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ User created: {user.username} ({user.email})")
        
        # 2. Sync from mock provider
        print("\n🔄 Syncing portfolio from mock provider...")
        result = await sync_portfolio(user.id, db, "mock", {})
        print(f"✅ Sync complete: {result['status']}")
        print(f"   - Synced items: {result['synced_items']}")
        print(f"   - Sync time: {result['sync_time_ms']}ms")
        
        # 3. View portfolio
        print("\n📊 Portfolio Summary:")
        from app.database import Holding
        holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
        
        total_value = sum(h.total_value for h in holdings)
        total_gain = sum(h.gain_loss for h in holdings)
        
        print(f"   Total Value: ${total_value:,.2f}")
        print(f"   Total Gain/Loss: ${total_gain:,.2f}")
        print(f"   Holdings: {len(holdings)}")
        
        print("\n📈 Holdings Detail:")
        for h in sorted(holdings, key=lambda x: x.total_value, reverse=True):
            pct_gain = (h.gain_loss / (h.purchase_price * h.quantity) * 100) if h.purchase_price > 0 else 0
            print(f"   {h.ticker:6s} | {h.quantity:5.0f} shares @ ${h.current_price:7.2f} | "
                  f"Value: ${h.total_value:9,.2f} | Gain: {pct_gain:+6.2f}%")
        
        # 4. View transactions
        print("\n💳 Recent Transactions:")
        from app.database import Transaction
        txns = db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).order_by(Transaction.transaction_date.desc()).limit(5).all()
        
        for t in txns:
            print(f"   {t.transaction_date.strftime('%Y-%m-%d')} | "
                  f"{t.transaction_type:8s} | {t.ticker:6s} | "
                  f"{t.quantity:5.0f} @ ${t.price:7.2f}")
        
        # 5. Create snapshot
        print("\n📸 Creating portfolio snapshot...")
        from app.database import PortfolioSnapshot
        snapshot = PortfolioSnapshot(
            user_id=user.id,
            total_value=total_value,
            daily_return=0.0
        )
        db.add(snapshot)
        db.commit()
        print(f"✅ Snapshot created (${total_value:,.2f})")
        
        print("\n🎉 Demo complete!")
        print(f"\n📝 Database file: finnie_chat.db")
        print(f"   You can inspect with: sqlite3 finnie_chat.db")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(demo())
