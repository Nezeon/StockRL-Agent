"""Base data provider interface"""
from abc import ABC, abstractmethod
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Quote:
    """Real-time quote data"""
    ticker: str
    price: float
    volume: int
    open: float
    high: float
    low: float
    close: float
    timestamp: datetime
    source: str


@dataclass
class OHLCV:
    """OHLCV candlestick data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class BaseDataProvider(ABC):
    """Abstract base class for data providers"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def get_latest_quote(self, ticker: str) -> Quote:
        """Get latest quote for a ticker"""
        pass

    @abstractmethod
    async def get_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLCV]:
        """Get historical OHLCV data"""
        pass

    @abstractmethod
    async def validate_ticker(self, ticker: str) -> bool:
        """Validate if ticker exists"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass

    @property
    @abstractmethod
    def supports_realtime(self) -> bool:
        """Whether provider supports real-time data"""
        pass
