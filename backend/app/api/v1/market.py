"""Market data endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from app.schemas.market import QuoteResponse, HistoricalDataRequest, HistoricalDataResponse, OHLCVResponse
from app.data_providers.registry import get_provider

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/ticker/{ticker}/quote", response_model=QuoteResponse)
async def get_quote(ticker: str):
    """Get latest quote for a ticker"""
    try:
        provider = get_provider()
        quote = await provider.get_latest_quote(ticker.upper())

        return QuoteResponse(
            ticker=quote.ticker,
            price=quote.price,
            volume=quote.volume,
            open=quote.open,
            high=quote.high,
            low=quote.low,
            close=quote.close,
            timestamp=quote.timestamp,
            source=quote.source
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to fetch quote: {str(e)}")


@router.get("/ticker/{ticker}/history", response_model=HistoricalDataResponse)
async def get_historical_data(
    ticker: str,
    start_date: datetime = None,
    end_date: datetime = None,
    interval: str = "1d"
):
    """Get historical data for a ticker"""
    try:
        # Default date range: last 30 days
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        provider = get_provider()
        data = await provider.get_historical(
            ticker.upper(),
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )

        return HistoricalDataResponse(
            ticker=ticker.upper(),
            interval=interval,
            data=[
                OHLCVResponse(
                    timestamp=ohlcv.timestamp,
                    open=ohlcv.open,
                    high=ohlcv.high,
                    low=ohlcv.low,
                    close=ohlcv.close,
                    volume=ohlcv.volume
                )
                for ohlcv in data
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Failed to fetch historical data: {str(e)}")
