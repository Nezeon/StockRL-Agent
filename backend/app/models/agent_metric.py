"""AgentMetric model for training metrics"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class AgentMetric(Base):
    """Time-series metrics for agent training monitoring"""
    __tablename__ = "agent_metrics"
    __table_args__ = (
        Index('ix_agent_metrics_run_timestamp', 'agent_run_id', 'timestamp'),
        Index('ix_agent_metrics_run_step', 'agent_run_id', 'step'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agent_run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    step = Column(Integer, nullable=False)
    episode_reward = Column(Numeric(15, 4), nullable=True)
    cumulative_reward = Column(Numeric(15, 4), nullable=False)
    loss = Column(Numeric(15, 6), nullable=True)
    portfolio_nav = Column(Numeric(15, 2), nullable=False)
    rolling_sharpe = Column(Numeric(10, 4), nullable=True)

    # Relationships
    agent_run = relationship("AgentRun", back_populates="metrics")

    def __repr__(self):
        return f"<AgentMetric(step={self.step}, reward={self.cumulative_reward}, nav={self.portfolio_nav})>"
