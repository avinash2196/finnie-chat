import asyncio
from app.database import SessionLocal, User, init_db
from app.providers import sync_portfolio

async def resync():
    init_db()
    db = SessionLocal()
    
    user = db.query(User).filter(User.username == 'demo_user').first()
    print(f"Before sync: Portfolio value = ${user.portfolio_value:.2f}")
    
    result = await sync_portfolio(user.id, db, "mock", {})
    print(f"\nSync result: {result['status']} - {result['message']}")
    
    # Refresh user
    db.expire_all()
    user = db.query(User).filter(User.id == user.id).first()
    print(f"After sync: Portfolio value = ${user.portfolio_value:.2f}")
    
    db.close()

asyncio.run(resync())
