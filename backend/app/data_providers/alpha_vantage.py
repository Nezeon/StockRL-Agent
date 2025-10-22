"""Alpha Vantage data provider"""
import aiohttp
from datetime import datetime, timedelta
from typing import List, Optional
from app.data_providers.base import BaseDataProvider, Quote, OHLCV


class AlphaVantageProvider(BaseDataProvider):
    """Alpha Vantage data provider"""

    def __init__(self, api_key: str):
        super().__init__(api_key=api_key)
        self.base_url = "https://www.alphavantage.co/query"

    async def get_latest_quote(self, ticker: str) -> Quote:
        """Get latest quote from Alpha Vantage"""
        if not self.api_key:
            raise ValueError("Alpha Vantage API key required")

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": ticker,
            "apikey": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"API error: {response.status}")

                data = await response.json()

                if "Global Quote" not in data or not data["Global Quote"]:
                    raise ValueError(f"No data for ticker {ticker}")

                quote_data = data["Global Quote"]

                return Quote(
                    ticker=ticker,
                    price=float(quote_data.get("05. price", 0)),
                    volume=int(quote_data.get("06. volume", 0)),
                    open=float(quote_data.get("02. open", 0)),
                    high=float(quote_data.get("03. high", 0)),
                    low=float(quote_data.get("04. low", 0)),
                    close=float(quote_data.get("05. price", 0)),
                    timestamp=datetime.utcnow(),
                    source="alpha_vantage"
                )

    async def get_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLCV]:
        """Get historical data from Alpha Vantage"""
        if not self.api_key:
            raise ValueError("Alpha Vantage API key required")

        # Determine function based on interval
        if interval in ["1m", "5m", "15m", "30m", "1h"]:
            function = "TIME_SERIES_INTRADAY"
            params = {
                "function": function,
                "symbol": ticker,
                "interval": interval,
                "outputsize": "full",
                "apikey": self.api_key
            }
        else:
            function = "TIME_SERIES_DAILY"
            params = {
                "function": function,
                "symbol": ticker,
                "outputsize": "full",
                "apikey": self.api_key
            }

        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"API error: {response.status}")

                data = await response.json()

                # Find time series key
                ts_key = None
                for key in data.keys():
                    if "Time Series" in key:
                        ts_key = key
                        break

                if not ts_key or ts_key not in data:
                    raise ValueError(f"No historical data for {ticker}")

                time_series = data[ts_key]

                # Parse data
                ohlcv_data = []
                for date_str, values in time_series.items():
                    timestamp = datetime.fromisoformat(date_str.replace(" ", "T"))

                    # Filter by date range
                    if start_date <= timestamp <= end_date:
                        ohlcv_data.append(OHLCV(
                            timestamp=timestamp,
                            open=float(values["1. open"]),
                            high=float(values["2. high"]),
                            low=float(values["3. low"]),
                            close=float(values["4. close"]),
                            volume=int(values["5. volume"])
                        ))

                # Sort by timestamp
                ohlcv_data.sort(key=lambda x: x.timestamp)

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
        return "alpha_vantage"

    @property
    def supports_realtime(self) -> bool:
        return True
