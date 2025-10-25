"""Trading environment for RL agents"""
import numpy as np
from typing import Tuple, Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
from app.data_providers.base import BaseDataProvider, OHLCV
from app.rl_agents.observation import ObservationBuilder
from app.rl_agents.reward import calculate_reward
from app.simulator.executor import OrderExecutor, Order
from app.models.trade import TradeSide
import ta  # Technical analysis library


class TradingEnvironment:
    """
    Gym-like trading environment for RL agents

    Simulates trading a portfolio of stocks with:
    - Market data from data provider
    - Order execution with slippage and fees
    - Reward calculation based on NAV changes
    - Episode termination on bankruptcy or max steps
    """

    def __init__(
        self,
        portfolio_id: UUID,
        data_provider: BaseDataProvider,
        tickers: List[str],
        initial_cash: float,
        risk_profile: str = "moderate",
        action_space_type: str = "discrete",
        max_steps: int = 1000,
        lookback_window: int = 30
    ):
        """
        Initialize trading environment

        Args:
            portfolio_id: Portfolio UUID
            data_provider: Data provider instance
            tickers: List of tickers to trade
            initial_cash: Starting cash
            risk_profile: Risk profile for fees
            action_space_type: "discrete" or "continuous"
            max_steps: Maximum steps per episode
            lookback_window: Historical data window
        """
        self.portfolio_id = portfolio_id
        self.data_provider = data_provider
        self.tickers = tickers
        self.initial_cash = initial_cash
        self.risk_profile = risk_profile
        self.action_space_type = action_space_type
        self.max_steps = max_steps
        self.lookback_window = lookback_window

        # Environment state
        self.current_cash = initial_cash
        self.positions: Dict[str, Dict] = {}  # ticker -> {quantity, avg_price}
        self.current_step = 0
        self.done = False

        # Historical tracking
        self.nav_history = [initial_cash]
        self.returns_history = []
        self.peak_nav = initial_cash
        self.market_data_buffer: Dict[str, List[OHLCV]] = {t: [] for t in tickers}
        self.current_prices: Dict[str, float] = {}

        # Components
        self.obs_builder = ObservationBuilder(tickers, lookback_window)
        self.executor = OrderExecutor()

        # Action space
        if action_space_type == "discrete":
            # 3 actions per ticker: HOLD=0, BUY=1, SELL=2
            self.action_dim = 3 ** len(tickers)
        else:  # continuous
            # One value per ticker: [-1, 1] where negative=sell, positive=buy
            self.action_dim = len(tickers)

        self.obs_dim = self.obs_builder.get_observation_dim()

    async def reset(self) -> np.ndarray:
        """
        Reset environment to initial state

        Returns:
            Initial observation
        """
        self.current_cash = self.initial_cash
        self.positions = {}
        self.current_step = 0
        self.done = False
        self.nav_history = [self.initial_cash]
        self.returns_history = []
        self.peak_nav = self.initial_cash
        self.market_data_buffer = {t: [] for t in self.tickers}
        self.current_prices = {}

        # Fetch initial market data
        await self._fetch_market_data()

        # Get initial observation
        observation = self._get_observation()

        return observation

    async def step(self, action) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        Execute action and return next state

        Args:
            action: Agent's action (int for discrete, np.ndarray for continuous)

        Returns:
            (observation, reward, done, info)
        """
        # Store previous NAV
        prev_nav = self._compute_nav()

        # Execute action (place orders)
        trade_fees = await self._execute_action(action)

        # Update market data
        await self._fetch_market_data()

        # Calculate current NAV
        current_nav = self._compute_nav()

        # Calculate reward
        reward = calculate_reward(
            prev_nav=prev_nav,
            current_nav=current_nav,
            trade_fees=trade_fees,
            risk_profile=self.risk_profile,
            returns_history=self.returns_history[-20:] if len(self.returns_history) > 0 else None,
            peak_nav=self.peak_nav
        )

        # Update tracking
        self.nav_history.append(current_nav)
        if prev_nav > 0:
            period_return = (current_nav - prev_nav) / prev_nav
            self.returns_history.append(period_return)
        self.peak_nav = max(self.peak_nav, current_nav)

        # Check termination conditions
        self.current_step += 1
        bankruptcy_threshold = self.initial_cash * 0.1

        if current_nav < bankruptcy_threshold:
            self.done = True
            reward -= 10.0  # Large penalty for bankruptcy
        elif self.current_step >= self.max_steps:
            self.done = True

        # Get next observation
        observation = self._get_observation()

        # Info dict
        info = {
            "nav": current_nav,
            "cash": self.current_cash,
            "step": self.current_step,
            "positions": len(self.positions),
            "trade_fees": trade_fees
        }

        return observation, reward, self.done, info

    def _get_observation(self) -> np.ndarray:
        """Build observation from current state"""
        # Portfolio state
        portfolio_state = {
            "cash": self.current_cash,
            "initial_budget": self.initial_cash,
            "nav": self._compute_nav(),
            "positions": self._format_positions()
        }

        # Calculate technical indicators
        indicators = self._calculate_indicators()

        # Build observation
        observation = self.obs_builder.build(
            portfolio_state,
            self.market_data_buffer,
            indicators
        )

        return observation

    def _format_positions(self) -> Dict:
        """Format positions for observation builder"""
        formatted = {}
        for ticker, pos in self.positions.items():
            current_price = self.current_prices.get(ticker, pos["avg_price"])
            quantity = pos["quantity"]
            market_value = quantity * current_price
            unrealized_pnl = ((current_price - pos["avg_price"]) / pos["avg_price"]) * 100

            formatted[ticker] = {
                "quantity": quantity,
                "avg_price": pos["avg_price"],
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl_percent": unrealized_pnl
            }

        return formatted

    async def _fetch_market_data(self):
        """Fetch latest market data for all tickers"""
        for ticker in self.tickers:
            try:
                quote = await self.data_provider.get_latest_quote(ticker)

                # Convert quote to OHLCV
                ohlcv = OHLCV(
                    timestamp=quote.timestamp,
                    open=quote.open,
                    high=quote.high,
                    low=quote.low,
                    close=quote.close,
                    volume=quote.volume
                )

                # Add to buffer
                self.market_data_buffer[ticker].append(ohlcv)

                # Keep only recent data
                if len(self.market_data_buffer[ticker]) > self.lookback_window * 2:
                    self.market_data_buffer[ticker] = self.market_data_buffer[ticker][-self.lookback_window * 2:]

                # Update current price
                self.current_prices[ticker] = quote.price

            except Exception as e:
                # If data fetch fails, keep previous data
                pass

    def _calculate_indicators(self) -> Dict[str, Dict[str, float]]:
        """Calculate technical indicators for all tickers"""
        indicators = {}

        for ticker in self.tickers:
            data = self.market_data_buffer[ticker]

            if len(data) < 20:
                # Not enough data for indicators
                indicators[ticker] = {
                    "sma_20_ratio": 0.0,
                    "sma_50_ratio": 0.0,
                    "rsi": 50.0,
                    "macd_signal": 0.0,
                    "bb_position": 0.5
                }
                continue

            # Extract close prices
            closes = np.array([d.close for d in data])

            # SMA ratios
            if len(closes) >= 20:
                sma_20 = np.mean(closes[-20:])
                sma_20_ratio = (sma_20 / closes[-1]) - 1 if closes[-1] > 0 else 0
            else:
                sma_20_ratio = 0.0

            if len(closes) >= 50:
                sma_50 = np.mean(closes[-50:])
                sma_50_ratio = (sma_50 / closes[-1]) - 1 if closes[-1] > 0 else 0
            else:
                sma_50_ratio = 0.0

            # RSI (using ta library if available)
            try:
                import pandas as pd
                df = pd.DataFrame({"close": closes})
                rsi = ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]
                if np.isnan(rsi):
                    rsi = 50.0
            except:
                rsi = 50.0

            # MACD (simplified)
            macd_signal = 0.0  # TODO: Implement MACD

            # Bollinger bands position
            bb_position = 0.5  # TODO: Implement BB

            indicators[ticker] = {
                "sma_20_ratio": float(sma_20_ratio),
                "sma_50_ratio": float(sma_50_ratio),
                "rsi": float(rsi),
                "macd_signal": float(macd_signal),
                "bb_position": float(bb_position)
            }

        return indicators

    async def _execute_action(self, action) -> float:
        """
        Execute action and return total fees

        For discrete: Decode action and execute trades
        For continuous: Map action values to trade quantities

        Returns:
            Total fees from all trades
        """
        total_fees = 0.0

        if self.action_space_type == "discrete":
            # Coerce various action formats to a scalar index
            action_index = self._coerce_discrete_action(action)
            total_fees = await self._execute_discrete_action(action_index)
        else:
            total_fees = await self._execute_continuous_action(action)

        return total_fees

    def _coerce_discrete_action(self, action) -> int:
        """Convert an agent-produced action to a scalar discrete index safely.

        Accepts: int, numpy scalar, 1D numpy array, one-hot/probability vector.
        Fallback: argmax over vector-like inputs.
        """
        try:
            import numpy as np
            # Already an int
            if isinstance(action, (int,)):
                return int(action)
            # Numpy scalar
            if hasattr(action, "shape"):
                arr = np.asarray(action)
                if arr.ndim == 0:
                    return int(arr.item())
                # If single element array
                if arr.size == 1:
                    return int(arr.flatten()[0])
                # Otherwise, interpret as logits/probabilities/one-hot -> take argmax
                return int(np.argmax(arr))
            # Fallback to Python conversion
            return int(action)
        except Exception:
            # Safe fallback to HOLD
            return 0

    async def _execute_discrete_action(self, action_index: int) -> float:
        """Execute discrete action (HOLD=0, BUY=1, SELL=2 per ticker)"""
        total_fees = 0.0

        # Decode action (treat as base-3 number)
        actions = []
        temp = action_index
        for _ in range(len(self.tickers)):
            actions.append(temp % 3)
            temp //= 3

        # Execute per ticker
        for i, ticker in enumerate(self.tickers):
            action = actions[i]

            if action == 0:  # HOLD
                continue
            elif action == 1:  # BUY
                # Buy 10% of available cash worth of shares
                buy_amount = self.current_cash * 0.1
                current_price = self.current_prices.get(ticker, 100.0)
                if current_price > 0:
                    quantity = buy_amount / current_price
                    fees = await self._place_buy_order(ticker, quantity, current_price)
                    total_fees += fees
            elif action == 2:  # SELL
                # Sell 10% of position
                if ticker in self.positions:
                    quantity = self.positions[ticker]["quantity"] * 0.1
                    current_price = self.current_prices.get(ticker, self.positions[ticker]["avg_price"])
                    fees = await self._place_sell_order(ticker, quantity, current_price)
                    total_fees += fees

        return total_fees

    async def _execute_continuous_action(self, action: np.ndarray) -> float:
        """Execute continuous action (values in [-1, 1] per ticker)"""
        total_fees = 0.0

        for i, ticker in enumerate(self.tickers):
            action_value = action[i]

            # Threshold for HOLD
            if abs(action_value) < 0.1:
                continue

            current_price = self.current_prices.get(ticker, 100.0)

            if action_value > 0:  # BUY
                buy_amount = self.current_cash * abs(action_value) * 0.5  # Up to 50% of cash
                if current_price > 0:
                    quantity = buy_amount / current_price
                    fees = await self._place_buy_order(ticker, quantity, current_price)
                    total_fees += fees
            else:  # SELL
                if ticker in self.positions:
                    quantity = self.positions[ticker]["quantity"] * abs(action_value)
                    fees = await self._place_sell_order(ticker, quantity, current_price)
                    total_fees += fees

        return total_fees

    async def _place_buy_order(self, ticker: str, quantity: float, price: float) -> float:
        """Place buy order and update internal state"""
        if quantity <= 0 or price <= 0:
            return 0.0

        # Calculate total cost (simplified - no slippage model in env mode)
        fee_pct = 0.001 if self.risk_profile == "moderate" else 0.0005
        fees = quantity * price * fee_pct
        total_cost = (quantity * price) + fees

        # Check funds
        if total_cost > self.current_cash:
            return 0.0

        # Update cash
        self.current_cash -= total_cost

        # Update position
        if ticker in self.positions:
            old_qty = self.positions[ticker]["quantity"]
            old_avg = self.positions[ticker]["avg_price"]
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
            self.positions[ticker] = {"quantity": new_qty, "avg_price": new_avg}
        else:
            self.positions[ticker] = {"quantity": quantity, "avg_price": price}

        return fees

    async def _place_sell_order(self, ticker: str, quantity: float, price: float) -> float:
        """Place sell order and update internal state"""
        if quantity <= 0 or price <= 0:
            return 0.0

        if ticker not in self.positions:
            return 0.0

        # Cap quantity at available
        available = self.positions[ticker]["quantity"]
        quantity = min(quantity, available)

        # Calculate proceeds
        fee_pct = 0.001 if self.risk_profile == "moderate" else 0.0005
        fees = quantity * price * fee_pct
        proceeds = (quantity * price) - fees

        # Update cash
        self.current_cash += proceeds

        # Update position
        self.positions[ticker]["quantity"] -= quantity
        if self.positions[ticker]["quantity"] < 0.0001:
            del self.positions[ticker]

        return fees

    def _compute_nav(self) -> float:
        """Compute current Net Asset Value"""
        nav = self.current_cash

        for ticker, pos in self.positions.items():
            current_price = self.current_prices.get(ticker, pos["avg_price"])
            nav += pos["quantity"] * current_price

        return nav

    def render(self):
        """Optional: Render environment state (for debugging)"""
        nav = self._compute_nav()
        print(f"\n=== Step {self.current_step} ===")
        print(f"NAV: ${nav:.2f}")
        print(f"Cash: ${self.current_cash:.2f}")
        print(f"Positions: {len(self.positions)}")
        for ticker, pos in self.positions.items():
            print(f"  {ticker}: {pos['quantity']:.2f} @ ${pos['avg_price']:.2f}")
