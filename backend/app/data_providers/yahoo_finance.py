"""Yahoo Finance data provider"""
import yfinance as yf
from datetime import datetime
from typing import List, Optional
from app.data_providers.base import BaseDataProvider, Quote, OHLCV


class YahooFinanceProvider(BaseDataProvider):
    """Yahoo Finance data provider using yfinance library"""

    def __init__(self):
        super().__init__(api_key=None)  # Yahoo Finance doesn't require API key

    async def get_latest_quote(self, ticker: str) -> Quote:
        """Get latest quote from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1d", interval="1m")

            if hist.empty:
                raise ValueError(f"No data available for ticker {ticker}")

            latest = hist.iloc[-1]

            return Quote(
                ticker=ticker,
                price=float(latest['Close']),
                volume=int(latest['Volume']),
                open=float(latest['Open']),
                high=float(latest['High']),
                low=float(latest['Low']),
                close=float(latest['Close']),
                timestamp=datetime.utcnow(),
                source="yahoo_finance"
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch quote for {ticker}: {str(e)}")

    async def get_historical(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d"
    ) -> List[OHLCV]:
        """Get historical data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)

            # Map interval format
            yf_interval = self._map_interval(interval)

            # Fetch historical data
            hist = stock.history(
                start=start_date,
                end=end_date,
                interval=yf_interval
            )

            if hist.empty:
                raise ValueError(f"No historical data for {ticker}")

            # Convert to OHLCV list
            data = []
            for index, row in hist.iterrows():
                data.append(OHLCV(
                    timestamp=index.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                ))

            return data
        except Exception as e:
            raise ValueError(f"Failed to fetch historical data for {ticker}: {str(e)}")

    async def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker by attempting to fetch info"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False

    @property
    def name(self) -> str:
        return "yahoo_finance"

    @property
    def supports_realtime(self) -> bool:
        return True  # Yahoo provides recent data (15-20 min delay)

    def _map_interval(self, interval: str) -> str:
        """Map interval format to yfinance format"""
        mapping = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "1h": "1h",
            "1d": "1d",
            "1wk": "1wk",
            "1mo": "1mo"
        }
        return mapping.get(interval, "1d")
