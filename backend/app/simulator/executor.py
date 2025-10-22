"""Order execution engine for simulated trading"""
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.portfolio import Portfolio
from app.models.position import Position
from app.models.trade import Trade, TradeSide
from app.simulator.slippage import calculate_slippage, SlippageModel
from app.simulator.fees import calculate_fees, FeeCalculator


class InsufficientFundsError(Exception):
    """Raised when portfolio has insufficient cash for buy order"""
    pass


class InsufficientQuantityError(Exception):
    """Raised when portfolio has insufficient shares for sell order"""
    pass


@dataclass
class Order:
    """Order to be executed"""
    portfolio_id: UUID
    ticker: str
    side: TradeSide
    quantity: Decimal
    price: Decimal  # Market price (not execution price)
    agent_run_id: Optional[UUID] = None


@dataclass
class OrderResult:
    """Result of order execution"""
    trade: Trade
    updated_cash: Decimal
    updated_position: Optional[Position]


class OrderExecutor:
    """Executes orders and updates portfolio state"""

    def __init__(
        self,
        slippage_model: SlippageModel | None = None,
        fee_calculator: FeeCalculator | None = None
    ):
        self.slippage_model = slippage_model or SlippageModel()
        self.fee_calculator = fee_calculator or FeeCalculator()

    async def execute_order(
        self,
        order: Order,
        db: AsyncSession
    ) -> OrderResult:
        """
        Execute an order and update database

        Process:
        1. Validate order (sufficient funds/shares)
        2. Calculate execution price (with slippage)
        3. Calculate fees
        4. Update portfolio cash
        5. Update or create position
        6. Create trade record

        Args:
            order: Order to execute
            db: Database session

        Returns:
            OrderResult with trade and updated positions

        Raises:
            InsufficientFundsError: Not enough cash for buy
            InsufficientQuantityError: Not enough shares for sell
        """
        # Load portfolio
        portfolio = await db.get(Portfolio, order.portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {order.portfolio_id} not found")

        # Calculate slippage
        slippage = calculate_slippage(
            order.price,
            order.quantity,
            order.side.value,
            self.slippage_model
        )

        # Execution price includes slippage
        execution_price = order.price + slippage

        # Calculate fees
        fees = calculate_fees(
            execution_price,
            order.quantity,
            portfolio.risk_profile.value,
            self.fee_calculator
        )

        # Execute based on side
        if order.side == TradeSide.BUY:
            result = await self._execute_buy(
                order, portfolio, execution_price, slippage, fees, db
            )
        else:  # SELL
            result = await self._execute_sell(
                order, portfolio, execution_price, slippage, fees, db
            )

        await db.commit()
        return result

    async def _execute_buy(
        self,
        order: Order,
        portfolio: Portfolio,
        execution_price: Decimal,
        slippage: Decimal,
        fees: Decimal,
        db: AsyncSession
    ) -> OrderResult:
        """Execute buy order"""
        # Calculate total cost
        total_cost = (execution_price * order.quantity) + fees

        # Check sufficient funds
        if portfolio.current_cash < total_cost:
            raise InsufficientFundsError(
                f"Insufficient funds: need ${total_cost}, have ${portfolio.current_cash}"
            )

        # Update cash
        portfolio.current_cash -= total_cost

        # Find or create position
        from sqlalchemy import select
        stmt = select(Position).where(
            Position.portfolio_id == order.portfolio_id,
            Position.ticker == order.ticker
        )
        result = await db.execute(stmt)
        position = result.scalar_one_or_none()

        if position:
            # Update existing position with weighted average price
            total_quantity = position.quantity + order.quantity
            weighted_price = (
                (position.avg_purchase_price * position.quantity) +
                (execution_price * order.quantity)
            ) / total_quantity
            position.quantity = total_quantity
            position.avg_purchase_price = weighted_price
        else:
            # Create new position
            position = Position(
                portfolio_id=order.portfolio_id,
                ticker=order.ticker,
                quantity=order.quantity,
                avg_purchase_price=execution_price
            )
            db.add(position)

        # Create trade record
        trade = Trade(
            portfolio_id=order.portfolio_id,
            ticker=order.ticker,
            side=TradeSide.BUY,
            quantity=order.quantity,
            price=execution_price,
            slippage=slippage,
            fees=fees,
            simulated=True,
            agent_run_id=order.agent_run_id
        )
        db.add(trade)

        return OrderResult(
            trade=trade,
            updated_cash=portfolio.current_cash,
            updated_position=position
        )

    async def _execute_sell(
        self,
        order: Order,
        portfolio: Portfolio,
        execution_price: Decimal,
        slippage: Decimal,
        fees: Decimal,
        db: AsyncSession
    ) -> OrderResult:
        """Execute sell order"""
        # Find position
        from sqlalchemy import select
        stmt = select(Position).where(
            Position.portfolio_id == order.portfolio_id,
            Position.ticker == order.ticker
        )
        result = await db.execute(stmt)
        position = result.scalar_one_or_none()

        if not position or position.quantity < order.quantity:
            available = position.quantity if position else Decimal(0)
            raise InsufficientQuantityError(
                f"Insufficient shares: need {order.quantity}, have {available}"
            )

        # Calculate proceeds (subtract fees)
        proceeds = (execution_price * order.quantity) - fees

        # Update cash
        portfolio.current_cash += proceeds

        # Update position
        position.quantity -= order.quantity

        # Delete position if quantity reaches zero
        if position.quantity == 0:
            await db.delete(position)
            position = None

        # Create trade record
        trade = Trade(
            portfolio_id=order.portfolio_id,
            ticker=order.ticker,
            side=TradeSide.SELL,
            quantity=order.quantity,
            price=execution_price,
            slippage=abs(slippage),  # Make positive for sell
            fees=fees,
            simulated=True,
            agent_run_id=order.agent_run_id
        )
        db.add(trade)

        return OrderResult(
            trade=trade,
            updated_cash=portfolio.current_cash,
            updated_position=position
        )
