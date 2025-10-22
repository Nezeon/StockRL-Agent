"""Finnhub data provider"""
import aiohttp
from datetime import datetime
from typing import List
from app.data_providers.base import BaseDataProvider, Quote, OHLCV


class FinnhubProvider(BaseDataProvider):
    """Finnhub data provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        self.base_url = "https://finnhub.io/api/v1"

    async def get_latest_quote(self, ticker: str) -> Quote:
        """Get latest quote from Finnhub"""
        if not self.api_key:
            raise ValueError("Finnhub API key required")

        url = f"{self.base_url}/quote"
        params = {"symbol": ticker, "token": self.api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"API error: {response.status}")

                data = await response.json()

                if not data or data.get("c", 0) == 0:
                    raise ValueError(f"No data for ticker {ticker}")

                return Quote(
                    ticker=ticker,
                    price=float(data["c"]),  # current price
                    volume=0,  # Finnhub doesn't provide volume in quote
                    open=float(data["o"]),
                    high=float(data["h"]),
                    low=float(data["l"]),
                    close=float(data["c"]),
                    timestamp=datetime.utcnow(),
                    source="finnhub"
                )

    async def get_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLCV]:
        """Get historical candles from Finnhub"""
        if not self.api_key:
            raise ValueError("Finnhub API key required")

        # Map interval to Finnhub resolution
        resolution = self._map_resolution(interval)

        url = f"{self.base_url}/stock/candle"
        params = {
            "symbol": ticker,
            "resolution": resolution,
            "from": int(start_date.timestamp()),
            "to": int(end_date.timestamp()),
            "token": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"API error: {response.status}")

                data = await response.json()

                if data.get("s") != "ok" or not data.get("t"):
                    raise ValueError(f"No historical data for {ticker}")

                # Parse candles
                ohlcv_data = []
                for i in range(len(data["t"])):
                    ohlcv_data.append(OHLCV(
                        timestamp=datetime.fromtimestamp(data["t"][i]),
                        open=float(data["o"][i]),
                        high=float(data["h"][i]),
                        low=float(data["l"][i]),
                        close=float(data["c"][i]),
                        volume=int(data["v"][i])
                    ))

                return ohlcv_data

    async def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker by attempting to fetch quote"""
        try:
            await self.get_latest_quote(ticker)
            return True
        except:
            return False

    @property
    def name(self) -> str:
        return "finnhub"

    @property
    def supports_realtime(self) -> bool:
        return True

    def _map_resolution(self, interval: str) -> str:
        """Map interval to Finnhub resolution"""
        mapping = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "30m": "30",
            "1h": "60",
            "1d": "D",
            "1wk": "W",
            "1mo": "M"
        }
        return mapping.get(interval, "D")
