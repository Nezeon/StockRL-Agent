"""Reward function for trading agent"""
from decimal import Decimal
import numpy as np
from typing import Optional, List


def calculate_reward(
    prev_nav: float,
    current_nav: float,
    trade_fees: float,
    risk_profile: str,
    returns_history: Optional[List[float]] = None,
    peak_nav: Optional[float] = None
) -> float:
    """
    Calculate reward for agent action

    Reward components:
    1. NAV change (primary signal)
    2. Transaction cost penalty (discourage overtrading)
    3. Risk-adjusted component (based on volatility)
    4. Drawdown penalty (encourage capital preservation)

    Args:
        prev_nav: Previous Net Asset Value
        current_nav: Current Net Asset Value
        trade_fees: Total transaction fees this step
        risk_profile: "conservative", "moderate", or "aggressive"
        returns_history: Recent returns for volatility calculation
        peak_nav: Peak NAV achieved so far (for drawdown)

    Returns:
        Reward value (positive for good actions, negative for bad)
    """
    # 1. Base reward from NAV change
    nav_change = (current_nav - prev_nav) / prev_nav if prev_nav > 0 else 0
    base_reward = nav_change * 100  # Scale to reasonable range

    # 2. Transaction cost penalty (discourage unnecessary trading)
    cost_penalty = -(trade_fees / current_nav) * 10 if current_nav > 0 else 0

    # 3. Risk-adjusted component (volatility penalty)
    volatility_penalty = 0.0
    if returns_history and len(returns_history) > 1:
        returns_std = np.std(returns_history)

        # Penalty strength based on risk profile
        if risk_profile == "conservative":
            volatility_penalty = -returns_std * 2.0  # Strong penalty
        elif risk_profile == "moderate":
            volatility_penalty = -returns_std * 1.0  # Medium penalty
        else:  # aggressive
            volatility_penalty = -returns_std * 0.5  # Weak penalty

    # 4. Drawdown penalty (encourage capital preservation)
    drawdown_penalty = 0.0
    if peak_nav and peak_nav > 0:
        if current_nav < peak_nav:
            drawdown = (peak_nav - current_nav) / peak_nav
            drawdown_penalty = -drawdown * 5.0
        # else: New peak, no penalty (actually positive signal)

    # Final reward
    reward = base_reward + cost_penalty + volatility_penalty + drawdown_penalty

    # Clip extreme values to prevent instability
    reward = np.clip(reward, -10.0, 10.0)

    return float(reward)


def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio from returns

    Args:
        returns: List of period returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Sharpe ratio (higher is better)
    """
    if not returns or len(returns) < 2:
        return 0.0

    returns_array = np.array(returns)
    mean_return = np.mean(returns_array)
    std_return = np.std(returns_array)

    if std_return == 0:
        return 0.0

    sharpe = (mean_return - risk_free_rate) / std_return

    return float(sharpe)


def calculate_max_drawdown(nav_history: List[float]) -> float:
    """
    Calculate maximum drawdown from NAV history

    Args:
        nav_history: List of NAV values

    Returns:
        Maximum drawdown as percentage (0 to 1)
    """
    if not nav_history or len(nav_history) < 2:
        return 0.0

    nav_array = np.array(nav_history)
    cumulative_max = np.maximum.accumulate(nav_array)

    drawdowns = (cumulative_max - nav_array) / cumulative_max
    max_drawdown = np.max(drawdowns)

    return float(max_drawdown)
