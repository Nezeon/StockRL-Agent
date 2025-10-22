"""Mock data provider for demo mode"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List
from app.data_providers.base import BaseDataProvider, Quote, OHLCV


class MockDataProvider(BaseDataProvider):
    """Mock data provider with realistic synthetic data"""

    def __init__(self):
        super().__init__(api_key=None)
        # Base prices for common tickers
        self.base_prices = {
            "AAPL": 175.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "TSLA": 250.0,
            "AMZN": 145.0,
            "META": 350.0,
            "NVDA": 480.0,
            "AMD": 120.0,
        }
        # Random walk state (for continuity between calls)
        self.current_prices = self.base_prices.copy()
        self.last_update = datetime.utcnow()

    async def get_latest_quote(self, ticker: str) -> Quote:
        """Get latest quote with realistic random walk"""
        # Update prices with random walk
        self._update_prices()

        if ticker not in self.current_prices:
            raise ValueError(f"Ticker {ticker} not supported in mock provider")

        price = self.current_prices[ticker]
        # Generate OHLC around current price
        high = price * (1 + random.uniform(0, 0.02))
        low = price * (1 - random.uniform(0, 0.02))
        open_price = random.uniform(low, high)
        volume = int(random.uniform(1_000_000, 10_000_000))

        return Quote(
            ticker=ticker,
            price=price,
            volume=volume,
            open=open_price,
            high=high,
            low=low,
            close=price,
            timestamp=datetime.utcnow(),
            source="mock"
        )

    async def get_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLCV]:
        """Generate historical data with realistic patterns"""
        if ticker not in self.base_prices:
            raise ValueError(f"Ticker {ticker} not supported in mock provider")

        # Generate dates based on interval
        dates = self._generate_dates(start_date, end_date, interval)
        base_price = self.base_prices[ticker]

        # Generate realistic price series using geometric Brownian motion
        data = []
        current_price = base_price

        for date in dates:
            # Random walk with drift
            drift = 0.0001  # Slight upward bias
            volatility = 0.02
            change = np.random.normal(drift, volatility)
            current_price = current_price * (1 + change)

            # Generate OHLC
            high = current_price * (1 + abs(np.random.normal(0, 0.015)))
            low = current_price * (1 - abs(np.random.normal(0, 0.015)))
            open_price = random.uniform(low * 1.005, high * 0.995)
            close = current_price
            volume = int(random.uniform(500_000, 15_000_000))

            data.append(OHLCV(
                timestamp=date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume
            ))

        return data

    async def validate_ticker(self, ticker: str) -> bool:
        """Check if ticker is in supported list"""
        return ticker in self.base_prices

    @property
    def name(self) -> str:
        return "mock"

    @property
    def supports_realtime(self) -> bool:
        return True

    def _update_prices(self):
        """Update current prices with random walk"""
        now = datetime.utcnow()
        # Update every few seconds to simulate market movement
        if (now - self.last_update).seconds < 2:
            return

        for ticker in self.current_prices:
            # Small random walk
            change = random.uniform(-0.005, 0.005)
            self.current_prices[ticker] *= (1 + change)
            # Keep prices reasonable (revert towards base)
            reversion = (self.base_prices[ticker] - self.current_prices[ticker]) * 0.01
            self.current_prices[ticker] += reversion

        self.last_update = now

    def _generate_dates(self, start: datetime, end: datetime, interval: str) -> List[datetime]:
        """Generate datetime range based on interval"""
        dates = []
        current = start

        if interval == "1d":
            delta = timedelta(days=1)
        elif interval == "1h":
            delta = timedelta(hours=1)
        elif interval == "5m":
            delta = timedelta(minutes=5)
        elif interval == "1m":
            delta = timedelta(minutes=1)
        else:
            delta = timedelta(days=1)

        while current <= end:
            dates.append(current)
            current += delta

        return dates
