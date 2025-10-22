"""Market data schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class QuoteResponse(BaseModel):
    """Quote schema"""
    ticker: str
    price: float
    volume: int
    open: float
    high: float
    low: float
    close: float
    timestamp: datetime
    source: str


class OHLCVResponse(BaseModel):
    """OHLCV candle schema"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoricalDataRequest(BaseModel):
    """Request for historical data"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: str = Field("1d", pattern="^(1m|5m|15m|1h|1d|1wk|1mo)$")


class HistoricalDataResponse(BaseModel):
    """Historical data response"""
    ticker: str
    interval: str
    data: List[OHLCVResponse]
