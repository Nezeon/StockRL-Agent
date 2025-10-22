"""Position model for current holdings"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class Position(Base):
    """Current holdings in a portfolio"""
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'ticker', name='uq_portfolio_ticker'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 4), nullable=False)  # Supports fractional shares
    avg_purchase_price = Column(Numeric(15, 4), nullable=False)  # Cost basis per share
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")

    def __repr__(self):
        return f"<Position(ticker={self.ticker}, qty={self.quantity}, avg_price={self.avg_purchase_price})>"
