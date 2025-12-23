#!/usr/bin/env python
"""Verify all users and their data"""
from app.database import SessionLocal, User, Holding, Transaction

db = SessionLocal()

try:
    # Get all users
    all_users = db.query(User).all()
    print(f"📋 TOTAL USERS: {len(all_users)}")
    
    for user in all_users:
        print(f"\n👤 {user.username} | UUID: {user.id}")
        
        # Holdings
        holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
        print(f"   📊 Holdings: {len(holdings)}")
        for h in holdings:
            print(f"      {h.ticker}: qty={h.quantity}, price=${h.purchase_price}")
        
        # Transactions
        transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
        print(f"   💳 Transactions: {len(transactions)}")
        for t in transactions:
            print(f"      {t.ticker} {t.transaction_type}: qty={t.quantity} @ ${t.price}")
    
finally:
    db.close()
