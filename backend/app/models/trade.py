"""Trade model for historical trades"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class TradeSide(str, enum.Enum):
    """Trade side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class Trade(Base):
    """Historical record of executed trades"""
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    side = Column(SQLEnum(TradeSide), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)
    price = Column(Numeric(15, 4), nullable=False)  # Execution price per share
    slippage = Column(Numeric(10, 4), default=0, nullable=False)
    fees = Column(Numeric(10, 2), default=0, nullable=False)
    simulated = Column(Boolean, default=True, nullable=False)  # Paper trading flag
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="trades")
    agent_run = relationship("AgentRun", back_populates="trades")

    def __repr__(self):
        return f"<Trade(ticker={self.ticker}, side={self.side}, qty={self.quantity}, price={self.price})>"

    @property
    def total_value(self) -> float:
        """Calculate total cost/proceeds of trade"""
        return float(self.quantity * self.price)
