"""Portfolio model for user trading portfolios"""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class RiskProfile(str, enum.Enum):
    """Risk profile enumeration"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class Portfolio(Base):
    """User trading portfolio with configuration"""
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    initial_budget = Column(Numeric(15, 2), nullable=False)
    current_cash = Column(Numeric(15, 2), nullable=False)
    tickers = Column(JSON, nullable=False)  # List of ticker symbols
    allocation_strategy = Column(JSON, nullable=True)  # Optional target allocations
    risk_profile = Column(SQLEnum(RiskProfile), default=RiskProfile.MODERATE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, name={self.name}, user_id={self.user_id})>"

    def compute_nav(self, position_values: dict[str, Decimal]) -> Decimal:
        """Compute Net Asset Value (cash + total position values)"""
        total_position_value = sum(position_values.values())
        return Decimal(self.current_cash) + total_position_value
