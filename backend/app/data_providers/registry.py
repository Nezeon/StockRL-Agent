"""Data provider registry and factory"""
from typing import Dict, Type
from app.data_providers.base import BaseDataProvider
from app.data_providers.mock_provider import MockDataProvider
from app.data_providers.yahoo_finance import YahooFinanceProvider
from app.data_providers.alpha_vantage import AlphaVantageProvider
from app.data_providers.finnhub import FinnhubProvider
from app.config import settings


# Provider registry
_PROVIDERS: Dict[str, Type[BaseDataProvider]] = {
    "mock": MockDataProvider,
    "yahoo": YahooFinanceProvider,
    "alphavantage": AlphaVantageProvider,
    "finnhub": FinnhubProvider,
}


def register_provider(name: str, provider_class: Type[BaseDataProvider]):
    """Register a new data provider"""
    _PROVIDERS[name] = provider_class


def get_provider(provider_name: str | None = None) -> BaseDataProvider:
    """Get data provider instance based on configuration"""
    name = provider_name or settings.data_provider

    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(_PROVIDERS.keys())}")

    provider_class = _PROVIDERS[name]

    # Initialize provider with API key if needed
    if name == "mock" or name == "yahoo":
        return provider_class()
    elif name == "alphavantage":
        if not settings.alpha_vantage_key:
            raise ValueError("Alpha Vantage API key required (set ALPHA_VANTAGE_KEY)")
        return provider_class(api_key=settings.alpha_vantage_key)
    elif name == "finnhub":
        if not settings.finnhub_key:
            raise ValueError("Finnhub API key required (set FINNHUB_KEY)")
        return provider_class(api_key=settings.finnhub_key)
    else:
        return provider_class()
