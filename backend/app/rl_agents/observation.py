"""Observation space builder for trading environment"""
import numpy as np
from typing import Dict, List
from decimal import Decimal
from app.data_providers.base import OHLCV


class ObservationBuilder:
    """Builds observation vectors from portfolio and market data"""

    def __init__(self, tickers: List[str], lookback_window: int = 30):
        """
        Initialize observation builder

        Args:
            tickers: List of tickers in portfolio
            lookback_window: Number of historical timesteps to include
        """
        self.tickers = tickers
        self.n_tickers = len(tickers)
        self.lookback_window = lookback_window

        # Running statistics for normalization
        self.price_mean = {ticker: 0.0 for ticker in tickers}
        self.price_std = {ticker: 1.0 for ticker in tickers}
        self.volume_mean = {ticker: 0.0 for ticker in tickers}
        self.volume_std = {ticker: 1.0 for ticker in tickers}

    def build(
        self,
        portfolio_state: Dict,
        market_data: Dict[str, List[OHLCV]],
        indicators: Dict[str, Dict[str, float]]
    ) -> np.ndarray:
        """
        Build observation vector from current state

        Observation components:
        1. Portfolio state (cash ratio + per-ticker position info)
        2. Market data (last N timesteps of normalized OHLCV)
        3. Technical indicators (SMA, RSI, MACD, Bollinger)

        Args:
            portfolio_state: Dict with 'cash', 'initial_budget', 'nav', 'positions'
            market_data: Dict mapping ticker to list of recent OHLCV data
            indicators: Dict mapping ticker to indicator values

        Returns:
            Flattened observation vector
        """
        observation_components = []

        # 1. Portfolio state
        portfolio_obs = self._build_portfolio_obs(portfolio_state)
        observation_components.append(portfolio_obs)

        # 2. Market data (price/volume history)
        for ticker in self.tickers:
            if ticker in market_data:
                market_obs = self._build_market_obs(ticker, market_data[ticker])
                observation_components.append(market_obs)
            else:
                # If no data, use zeros
                zeros = np.zeros(self.lookback_window * 3)
                observation_components.append(zeros)

        # 3. Technical indicators
        for ticker in self.tickers:
            if ticker in indicators:
                indicator_obs = self._build_indicator_obs(indicators[ticker])
                observation_components.append(indicator_obs)
            else:
                # If no indicators, use zeros
                zeros = np.zeros(5)
                observation_components.append(zeros)

        # Concatenate all components
        observation = np.concatenate(observation_components)

        return observation.astype(np.float32)

    def _build_portfolio_obs(self, portfolio_state: Dict) -> np.ndarray:
        """Build portfolio state observation"""
        obs = []

        # Cash ratio
        cash = float(portfolio_state.get('cash', 0))
        initial_budget = float(portfolio_state.get('initial_budget', 1))
        cash_ratio = cash / initial_budget if initial_budget > 0 else 0
        obs.append(cash_ratio)

        # Per-ticker position information
        positions = portfolio_state.get('positions', {})
        nav = float(portfolio_state.get('nav', 1))

        for ticker in self.tickers:
            if ticker in positions:
                pos = positions[ticker]
                # Position ratio (market value / NAV)
                market_value = float(pos.get('market_value', 0))
                position_ratio = market_value / nav if nav > 0 else 0
                obs.append(position_ratio)

                # Unrealized P&L ratio
                unrealized_pnl = float(pos.get('unrealized_pnl_percent', 0))
                obs.append(unrealized_pnl / 100.0)  # Normalize to [-1, 1] range
            else:
                obs.append(0.0)  # No position
                obs.append(0.0)  # No P&L

        return np.array(obs, dtype=np.float32)

    def _build_market_obs(self, ticker: str, data: List[OHLCV]) -> np.ndarray:
        """Build market data observation (normalized price/volume history)"""
        obs = []

        # Take last N timesteps
        recent_data = data[-self.lookback_window:]

        # Pad if not enough data
        if len(recent_data) < self.lookback_window:
            padding_needed = self.lookback_window - len(recent_data)
            # Use first available data point for padding
            if recent_data:
                padding = [recent_data[0]] * padding_needed
                recent_data = padding + recent_data
            else:
                # No data at all - return zeros
                return np.zeros(self.lookback_window * 3, dtype=np.float32)

        # Extract prices and volumes
        prices = np.array([d.close for d in recent_data])
        volumes = np.array([d.volume for d in recent_data])

        # Normalize prices (z-score)
        price_mean = np.mean(prices)
        price_std = np.std(prices) if np.std(prices) > 0 else 1.0
        normalized_prices = (prices - price_mean) / price_std

        # Normalize volumes
        volume_mean = np.mean(volumes)
        volume_std = np.std(volumes) if np.std(volumes) > 0 else 1.0
        normalized_volumes = (volumes - volume_mean) / volume_std

        # Calculate returns
        returns = np.zeros(len(prices))
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns[i] = np.log(prices[i] / prices[i-1])

        # Concatenate: [prices, volumes, returns]
        for i in range(self.lookback_window):
            obs.extend([
                normalized_prices[i],
                normalized_volumes[i],
                returns[i]
            ])

        return np.array(obs, dtype=np.float32)

    def _build_indicator_obs(self, indicators: Dict[str, float]) -> np.ndarray:
        """Build technical indicator observation"""
        obs = []

        # SMA(20) / current_price - 1
        sma_20_ratio = indicators.get('sma_20_ratio', 0.0)
        obs.append(sma_20_ratio)

        # SMA(50) / current_price - 1
        sma_50_ratio = indicators.get('sma_50_ratio', 0.0)
        obs.append(sma_50_ratio)

        # RSI (0-100, normalized to 0-1)
        rsi = indicators.get('rsi', 50.0)
        obs.append(rsi / 100.0)

        # MACD signal (-1 to 1)
        macd_signal = indicators.get('macd_signal', 0.0)
        obs.append(np.clip(macd_signal, -1.0, 1.0))

        # Bollinger band position (0-1)
        bb_position = indicators.get('bb_position', 0.5)
        obs.append(bb_position)

        return np.array(obs, dtype=np.float32)

    def get_observation_dim(self) -> int:
        """Calculate total observation dimension"""
        # Portfolio: 1 (cash) + n_tickers * 2 (position ratio + pnl)
        portfolio_dim = 1 + (self.n_tickers * 2)

        # Market data: n_tickers * lookback_window * 3 (price, volume, returns)
        market_dim = self.n_tickers * self.lookback_window * 3

        # Indicators: n_tickers * 5 (SMA20, SMA50, RSI, MACD, BB)
        indicator_dim = self.n_tickers * 5

        total_dim = portfolio_dim + market_dim + indicator_dim

        return total_dim


def build_observation(
    portfolio_state: Dict,
    market_data: Dict[str, List[OHLCV]],
    indicators: Dict[str, Dict[str, float]],
    tickers: List[str],
    lookback_window: int = 30
) -> np.ndarray:
    """
    Convenience function to build observation

    Args:
        portfolio_state: Portfolio state dict
        market_data: Market data dict
        indicators: Technical indicators dict
        tickers: List of tickers
        lookback_window: Historical window size

    Returns:
        Observation vector
    """
    builder = ObservationBuilder(tickers, lookback_window)
    return builder.build(portfolio_state, market_data, indicators)
