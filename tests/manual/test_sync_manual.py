"""
Manual sync test hitting the providers sync logic.
Skipped by default; enable with RUN_MANUAL_TESTS=1.
"""
import os
import uuid
import pytest
import asyncio

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_MANUAL_TESTS"),
    reason="Manual sync test requires RUN_MANUAL_TESTS=1 (writes to DB).",
)

from app.database import SessionLocal, User, Holding, Transaction, init_db
from app.providers import sync_portfolio


@pytest.mark.asyncio
async def test_sync_manual():
    init_db()
    db = SessionLocal()
    try:
        unique_suffix = uuid.uuid4().hex[:8]
        email = f"synctest_{unique_suffix}@example.com"
        username = f"sync_test_{unique_suffix}"

        # Clean any prior user with same generated username (belt-and-suspenders)
        db.query(User).filter(User.username == username).delete()

        user = User(email=email, username=username, risk_tolerance="MEDIUM")
        db.add(user)
        db.commit()
        db.refresh(user)

        before_holdings = db.query(Holding).filter(Holding.user_id == user.id).count()
        before_txns = db.query(Transaction).filter(Transaction.user_id == user.id).count()
        assert before_holdings == 0
        assert before_txns == 0

        result = await sync_portfolio(user.id, db, "mock", {})
        assert result["status"] == "SUCCESS"
    finally:
        db.close()
