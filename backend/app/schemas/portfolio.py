"""Portfolio schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    name: str = Field(..., min_length=1, max_length=100)
    initial_budget: Decimal = Field(..., gt=0, description="Starting budget")
    tickers: List[str] = Field(..., min_items=1, description="List of ticker symbols")
    allocation_strategy: Optional[Dict[str, float]] = Field(None, description="Target allocations")
    risk_profile: str = Field("moderate", pattern="^(conservative|moderate|aggressive)$")


class PortfolioCreate(PortfolioBase):
    """Schema for creating a portfolio"""
    pass


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    tickers: Optional[List[str]] = Field(None, min_items=1)
    allocation_strategy: Optional[Dict[str, float]] = None
    risk_profile: Optional[str] = Field(None, pattern="^(conservative|moderate|aggressive)$")
    is_active: Optional[bool] = None


class PositionResponse(BaseModel):
    """Position schema for API responses"""
    ticker: str
    quantity: Decimal
    avg_purchase_price: Decimal
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

    class Config:
        from_attributes = True


class PortfolioResponse(PortfolioBase):
    """Portfolio schema for API responses"""
    id: UUID
    user_id: UUID
    current_cash: Decimal
    nav: float
    pnl: float
    pnl_percent: float
    is_active: bool
    positions: Optional[List[PositionResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """List of portfolios"""
    portfolios: List[PortfolioResponse]
