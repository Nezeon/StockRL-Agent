"""Trade schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class TradeResponse(BaseModel):
    """Trade schema for API responses"""
    id: UUID
    ticker: str
    side: str  # "BUY" or "SELL"
    quantity: Decimal
    price: Decimal
    total_value: float
    slippage: Decimal
    fees: Decimal
    executed_at: datetime
    simulated: bool
    agent_run_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class TradeListResponse(BaseModel):
    """List of trades"""
    trades: List[TradeResponse]
    total: int
    page: int
    page_size: int


class SimulateTradeRequest(BaseModel):
    """Request to simulate a trade"""
    ticker: str = Field(..., min_length=1, max_length=10)
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, description="Execution price (if not provided, uses current market price)")
