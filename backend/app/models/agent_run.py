"""AgentRun model for tracking agent sessions"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class AgentAlgorithm(str, enum.Enum):
    """Agent algorithm enumeration"""
    PPO = "PPO"
    DQN = "DQN"
    A2C = "A2C"
    SB3_PPO = "SB3_PPO"
    SB3_A2C = "SB3_A2C"


class AgentMode(str, enum.Enum):
    """Agent mode enumeration"""
    TRAIN = "train"
    LIVE = "live"


class ActionSpaceType(str, enum.Enum):
    """Action space type enumeration"""
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"


class AgentStatus(str, enum.Enum):
    """Agent status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    COMPLETED = "completed"


class AgentRun(Base):
    """Track agent training/trading sessions"""
    __tablename__ = "agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id"), nullable=False, index=True)
    algorithm = Column(SQLEnum(AgentAlgorithm), nullable=False)
    mode = Column(SQLEnum(AgentMode), nullable=False)
    action_space_type = Column(SQLEnum(ActionSpaceType), nullable=False)
    hyperparameters = Column(JSON, nullable=True)
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.RUNNING, nullable=False)
    start_time = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    final_nav = Column(Numeric(15, 2), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="agent_runs")
    metrics = relationship("AgentMetric", back_populates="agent_run", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="agent_run")

    def __repr__(self):
        return f"<AgentRun(id={self.id}, algorithm={self.algorithm}, status={self.status})>"
