import asyncio
import sys
sys.path.insert(0, 'd:/Projects/StockRL-Agent/backend')

from app.db.session import AsyncSessionLocal
from app.services.portfolio_service import PortfolioService
from app.models.user import User
from sqlalchemy import select

async def test_create_portfolio():
    async with AsyncSessionLocal() as db:
        # Get Ayushmaan user
        stmt = select(User).where(User.username == "Ayushmaan")
        result = await db.execute(stmt)
        user = result.scalar_one()
        
        service = PortfolioService(db)
        
        # Validate NFLX ticker
        print("Validating NFLX ticker...")
        validation = await service.validate_tickers(["NFLX"])
        print(f"Validation result: {validation}")
        
        if validation.get("NFLX"):
            print("\n✓ NFLX is valid! Creating portfolio...")
            portfolio_data = {
                "name": "Test NFLX",
                "initial_budget": 10000,
                "tickers": ["NFLX"],
                "risk_profile": "moderate"
            }
            
            try:
                portfolio = await service.create_portfolio(user.id, portfolio_data)
                print(f"✓ Portfolio created: {portfolio.id}")
                print(f"  Name: {portfolio.name}")
                print(f"  Tickers: {portfolio.tickers}")
            except Exception as e:
                print(f"✗ Error creating portfolio: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("✗ NFLX is not valid!")

if __name__ == "__main__":
    asyncio.run(test_create_portfolio())
