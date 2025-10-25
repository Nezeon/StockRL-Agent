"""Portfolio service - business logic for portfolio operations"""
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade
from app.data_providers.base import BaseDataProvider
from app.data_providers.registry import get_provider


class PortfolioService:
    """Service for portfolio operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_provider: Optional[BaseDataProvider] = None

    async def _get_data_provider(self) -> BaseDataProvider:
        """Get data provider instance"""
        if self.data_provider is None:
            self.data_provider = get_provider()
        return self.data_provider

    async def get_portfolio_with_positions(self, portfolio_id: UUID, user_id: UUID) -> Optional[Portfolio]:
        """Get portfolio with positions, verifying ownership"""
        from sqlalchemy.orm import selectinload
        stmt = select(Portfolio).options(selectinload(Portfolio.positions)).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        )
        result = await self.db.execute(stmt)
        portfolio = result.scalar_one_or_none()

        return portfolio

    async def compute_portfolio_nav(self, portfolio: Portfolio) -> Decimal:
        """
        Compute Net Asset Value for a portfolio

        NAV = cash + sum(position_value for all positions)
        """
        nav = Decimal(portfolio.current_cash)

        # Get current prices for all positions
        provider = await self._get_data_provider()

        for position in portfolio.positions:
            try:
                quote = await provider.get_latest_quote(position.ticker)
                position_value = Decimal(str(quote.price)) * position.quantity
                nav += position_value
            except Exception:
                # If quote fails, use last known avg price
                position_value = position.avg_purchase_price * position.quantity
                nav += position_value

        return nav

    async def compute_portfolio_metrics(self, portfolio: Portfolio) -> Dict:
        """
        Compute comprehensive portfolio metrics

        Returns dict with:
        - nav: Current net asset value
        - pnl: Profit/loss in dollars
        - pnl_percent: Profit/loss as percentage
        - positions: List of position details with current prices
        """
        provider = await self._get_data_provider()

        # Calculate NAV and position details
        nav = Decimal(portfolio.current_cash)
        position_details = []

        for position in portfolio.positions:
            try:
                quote = await provider.get_latest_quote(position.ticker)
                current_price = Decimal(str(quote.price))
            except Exception:
                current_price = position.avg_purchase_price

            market_value = current_price * position.quantity
            unrealized_pnl = (current_price - position.avg_purchase_price) * position.quantity
            unrealized_pnl_percent = ((current_price - position.avg_purchase_price) / position.avg_purchase_price * 100) if position.avg_purchase_price > 0 else Decimal(0)

            position_details.append({
                "ticker": position.ticker,
                "quantity": position.quantity,
                "avg_purchase_price": position.avg_purchase_price,
                "current_price": float(current_price),
                "market_value": float(market_value),
                "unrealized_pnl": float(unrealized_pnl),
                "unrealized_pnl_percent": float(unrealized_pnl_percent)
            })

            nav += market_value

        # Calculate total P&L
        pnl = nav - portfolio.initial_budget
        pnl_percent = (pnl / portfolio.initial_budget * 100) if portfolio.initial_budget > 0 else Decimal(0)

        return {
            "nav": float(nav),
            "pnl": float(pnl),
            "pnl_percent": float(pnl_percent),
            "positions": position_details
        }

    async def get_portfolio_trades(
        self,
        portfolio_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Trade], int]:
        """
        Get trades for a portfolio with pagination

        Returns:
            (trades, total_count)
        """
        # Get trades
        stmt = select(Trade).where(
            Trade.portfolio_id == portfolio_id
        ).order_by(Trade.executed_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        trades = result.scalars().all()

        # Get total count
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(Trade).where(
            Trade.portfolio_id == portfolio_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        return list(trades), total

    async def validate_tickers(self, tickers: List[str]) -> Dict[str, bool]:
        """
        Validate if tickers are valid

        Returns:
            Dict mapping ticker to validity (True/False)
        """
        provider = await self._get_data_provider()
        results = {}

        for ticker in tickers:
            try:
                is_valid = await provider.validate_ticker(ticker)
                results[ticker] = is_valid
            except Exception:
                results[ticker] = False

        return results

    async def get_user_portfolios(self, user_id: UUID) -> List[Portfolio]:
        """Get all portfolios for a user"""
        from sqlalchemy.orm import selectinload
        stmt = select(Portfolio).options(selectinload(Portfolio.positions)).where(Portfolio.user_id == user_id).order_by(Portfolio.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_portfolio(self, user_id: UUID, portfolio_data: dict) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(
            user_id=user_id,
            name=portfolio_data["name"],
            initial_budget=portfolio_data["initial_budget"],
            current_cash=portfolio_data["initial_budget"],  # Start with full budget as cash
            tickers=portfolio_data["tickers"],
            allocation_strategy=portfolio_data.get("allocation_strategy"),
            risk_profile=portfolio_data["risk_profile"]
        )

        self.db.add(portfolio)
        await self.db.commit()
        await self.db.refresh(portfolio)

        return portfolio

    async def update_portfolio(self, portfolio: Portfolio, update_data: dict) -> Portfolio:
        """Update an existing portfolio"""
        for field, value in update_data.items():
            if value is not None and hasattr(portfolio, field):
                setattr(portfolio, field, value)

        await self.db.commit()
        await self.db.refresh(portfolio)

        return portfolio

    async def delete_portfolio(self, portfolio: Portfolio):
        """Delete a portfolio"""
        await self.db.delete(portfolio)
        await self.db.commit()
