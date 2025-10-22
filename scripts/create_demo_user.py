#!/usr/bin/env python3
"""Create demo user and portfolio for testing"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.user import User
from app.models.portfolio import Portfolio, RiskProfile
from app.dependencies import hash_password
from app.db.session import Base


async def create_demo_data():
    """Create demo user and portfolio"""
    print("Creating demo data...")

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if demo user exists
        from sqlalchemy import select
        stmt = select(User).where(User.username == "demo")
        result = await session.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("Demo user already exists!")
            user = existing_user
        else:
            # Create demo user
            user = User(
                username="demo",
                email="demo@stockrl.com",
                hashed_password=hash_password("demo123"),
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✓ Created demo user (username: demo, password: demo123)")

        # Check if demo portfolio exists
        stmt = select(Portfolio).where(
            Portfolio.user_id == user.id,
            Portfolio.name == "Demo Portfolio"
        )
        result = await session.execute(stmt)
        existing_portfolio = result.scalar_one_or_none()

        if existing_portfolio:
            print("Demo portfolio already exists!")
        else:
            # Create demo portfolio
            portfolio = Portfolio(
                user_id=user.id,
                name="Demo Portfolio",
                initial_budget=Decimal("10000.00"),
                current_cash=Decimal("10000.00"),
                tickers=["AAPL", "GOOGL", "MSFT", "TSLA"],
                allocation_strategy={
                    "AAPL": 0.25,
                    "GOOGL": 0.25,
                    "MSFT": 0.25,
                    "TSLA": 0.25
                },
                risk_profile=RiskProfile.MODERATE,
                is_active=True
            )
            session.add(portfolio)
            await session.commit()
            await session.refresh(portfolio)
            print(f"✓ Created demo portfolio (ID: {portfolio.id})")
            print(f"  - Budget: $10,000")
            print(f"  - Tickers: AAPL, GOOGL, MSFT, TSLA")
            print(f"  - Risk Profile: Moderate")

    await engine.dispose()

    print("\n✅ Demo setup complete!")
    print("\nLogin credentials:")
    print("  Username: demo")
    print("  Password: demo123")
    print("\nYou can now start the backend server:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(create_demo_data())
