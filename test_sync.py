"""Test sync functionality"""
import asyncio
from app.database import SessionLocal, User, Holding, Transaction, init_db
from app.providers import sync_portfolio

async def test_sync():
    """Test syncing with mock provider"""
    
    # Initialize database
    print("🗄️  Initializing database...")
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create a test user
        print("\n👤 Creating test user...")
        test_user = User(
            email="synctest@example.com",
            username="sync_test",
            risk_tolerance="MEDIUM"
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ User created: {test_user.username} (ID: {test_user.id})")
        
        # Check holdings before sync
        before_holdings = db.query(Holding).filter(Holding.user_id == test_user.id).count()
        before_txns = db.query(Transaction).filter(Transaction.user_id == test_user.id).count()
        print(f"\n📊 Before sync: {before_holdings} holdings, {before_txns} transactions")
        
        # Perform sync
        print("\n🔄 Syncing with MOCK provider...")
        result = await sync_portfolio(test_user.id, db, "mock", {})
        
        print(f"\n✅ Sync result:")
        print(f"   Status: {result['status']}")
        print(f"   Source: {result['source']}")
        print(f"   Items synced: {result['synced_items']}")
        print(f"   Message: {result['message']}")
        print(f"   Time: {result['sync_time_ms']}ms")
        
        # Check holdings after sync
        after_holdings = db.query(Holding).filter(Holding.user_id == test_user.id).all()
        after_txns = db.query(Transaction).filter(Transaction.user_id == test_user.id).all()
        
        print(f"\n📊 After sync: {len(after_holdings)} holdings, {len(after_txns)} transactions")
        
        if after_holdings:
            print("\n📈 Holdings:")
            for h in after_holdings:
                print(f"   {h.ticker}: {h.quantity} shares @ ${h.current_price:.2f} (Total: ${h.total_value:.2f})")
        else:
            print("\n⚠️  No holdings found after sync!")
        
        if after_txns:
            print("\n📝 Transactions:")
            for t in after_txns:
                print(f"   {t.transaction_type} {t.quantity} {t.ticker} @ ${t.price:.2f}")
        
        # Refresh to get latest data after commit
        db.expire_all()
        test_user = db.query(User).filter(User.id == test_user.id).first()
        
        # Check user portfolio value
        print(f"\n💰 User portfolio value: ${test_user.portfolio_value:.2f}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_sync())
