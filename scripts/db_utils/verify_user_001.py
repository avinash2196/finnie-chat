#!/usr/bin/env python
"""Verify user_001 data in database"""
from app.database import SessionLocal, User, Holding, Transaction

db = SessionLocal()

try:
    # Get user_001
    u = db.query(User).filter(User.username == 'user_001').first()
    if not u:
        print("❌ user_001 NOT FOUND")
        exit(1)
    
    print(f"✅ USER: {u.username} | UUID: {u.id}")
    
    # Get holdings
    holdings = db.query(Holding).filter(Holding.user_id == u.id).all()
    print(f"\n📊 HOLDINGS: {len(holdings)}")
    if holdings:
        for h in holdings:
            print(f"   {h.ticker}: qty={h.quantity}, purchase_price={h.purchase_price}, purchase_date={h.purchase_date}")
    
    # Get transactions
    transactions = db.query(Transaction).filter(Transaction.user_id == u.id).all()
    print(f"\n💳 TRANSACTIONS: {len(transactions)}")
    if transactions:
        for t in transactions:
            print(f"   {t.ticker} {t.transaction_type}: qty={t.quantity}, price={t.price}, date={t.transaction_date}")
    
    print(f"\n✅ Verification complete!")
    
finally:
    db.close()
