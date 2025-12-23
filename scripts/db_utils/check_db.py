"""Quick database check script"""
from app.database import SessionLocal, User, Holding, Transaction, SyncLog, init_db

# Initialize database
init_db()
db = SessionLocal()

try:
    # Count records
    users = db.query(User).all()
    holdings = db.query(Holding).all()
    transactions = db.query(Transaction).all()
    sync_logs = db.query(SyncLog).order_by(SyncLog.synced_at.desc()).limit(5).all()
    
    print("=" * 60)
    print("DATABASE STATUS")
    print("=" * 60)
    print(f"\n📊 Record Counts:")
    print(f"   Users:        {len(users)}")
    print(f"   Holdings:     {len(holdings)}")
    print(f"   Transactions: {len(transactions)}")
    
    if users:
        print(f"\n👥 Users:")
        for u in users:
            print(f"   - {u.username} ({u.email}) [ID: {u.id}]")
            print(f"     Risk: {u.risk_tolerance}")
            user_holdings = [h for h in holdings if h.user_id == u.id]
            user_transactions = [t for t in transactions if t.user_id == u.id]
            print(f"     Holdings: {len(user_holdings)}, Transactions: {len(user_transactions)}")
    else:
        print("\n⚠️  No users in database!")
    
    if sync_logs:
        print(f"\n📝 Recent Sync Logs:")
        for log in sync_logs:
            status_icon = "✅" if log.status == "SUCCESS" else "❌"
            print(f"   {status_icon} {log.synced_at} - User {log.user_id} - {log.status}")
            print(f"      Source: {log.source}, Items: {log.synced_items}, Time: {log.sync_time_ms}ms")
            if log.message:
                print(f"      Message: {log.message}")
    else:
        print("\n⚠️  No sync logs found!")
    
    print("\n" + "=" * 60)
    
finally:
    db.close()
