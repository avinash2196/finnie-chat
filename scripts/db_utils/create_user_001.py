from app.database import SessionLocal, User, Holding, init_db

init_db()
db = SessionLocal()

# Check if user_001 exists
user = db.query(User).filter(User.id == 'user_001').first()

if user:
    print(f"✅ User exists: {user.username} ({user.email})")
    holdings = db.query(Holding).filter(Holding.user_id == 'user_001').all()
    print(f"   Holdings: {len(holdings)}")
    print(f"   Portfolio value: ${user.portfolio_value:.2f}")
else:
    print("❌ User 'user_001' does not exist in database")
    print("\nCreating user_001...")
    
    new_user = User(
        id="user_001",
        email="user_001@example.com",
        username="user_001",
        risk_tolerance="MEDIUM"
    )
    db.add(new_user)
    db.commit()
    print("✅ User 'user_001' created!")
    print("\nNow click 'Sync Now' in the Portfolio page to pull data.")

db.close()
