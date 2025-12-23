from app.database import SessionLocal, User, Holding, init_db

init_db()
db = SessionLocal()

user = db.query(User).filter(User.username == 'demo_user').first()
if user:
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    total_from_holdings = sum(h.total_value for h in holdings)
    
    print(f"User: {user.username}")
    print(f"User ID: {user.id}")
    print(f"Portfolio value in DB: ${user.portfolio_value:.2f}")
    print(f"Total from holdings: ${total_from_holdings:.2f}")
    print(f"Holdings count: {len(holdings)}")
else:
    print("User not found")

db.close()
