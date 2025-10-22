"""Agent schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class StartAgentRequest(BaseModel):
    """Request to start an agent"""
    portfolio_id: UUID
    algorithm: str = Field(..., pattern="^(PPO|DQN|A2C|SB3_PPO|SB3_A2C)$")
    mode: str = Field(..., pattern="^(train|live)$")
    action_space_type: str = Field("continuous", pattern="^(discrete|continuous)$")
    hyperparameters: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {
            "learning_rate": 0.0003,
            "batch_size": 64,
            "gamma": 0.99,
            "episodes": 100
        }
    )


class StopAgentRequest(BaseModel):
    """Request to stop an agent"""
    agent_run_id: UUID


class AgentStatusResponse(BaseModel):
    """Agent status response"""
    agent_run_id: Optional[UUID]
    status: str
    algorithm: Optional[str]
    mode: Optional[str]
    last_reward: Optional[float]
    current_nav: Optional[float]
    start_time: Optional[datetime]


class AgentRunResponse(BaseModel):
    """Agent run response"""
    id: UUID
    portfolio_id: UUID
    algorithm: str
    mode: str
    action_space_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    final_nav: Optional[Decimal]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class AgentMetricResponse(BaseModel):
    """Agent metric response"""
    timestamp: datetime
    step: int
    episode_reward: Optional[Decimal]
    cumulative_reward: Decimal
    loss: Optional[Decimal]
    portfolio_nav: Decimal
    rolling_sharpe: Optional[Decimal]

    class Config:
        from_attributes = True


class AgentStatsResponse(BaseModel):
    """Agent statistics response"""
    agent_run: AgentRunResponse
    metrics: List[AgentMetricResponse]
    total_metrics: int
