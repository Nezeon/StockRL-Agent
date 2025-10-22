"""Slippage model for realistic trade execution"""
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class SlippageModel:
    """Configuration for slippage calculation"""
    base_slippage: float = 0.0001  # 0.01% base slippage
    size_impact: float = 0.00001  # Additional slippage per $1000 order size
    max_slippage: float = 0.01  # Maximum 1% slippage


def calculate_slippage(
    price: Decimal,
    quantity: Decimal,
    side: str,
    model: SlippageModel | None = None
) -> Decimal:
    """
    Calculate slippage for an order

    Slippage is the difference between expected and actual execution price.
    Larger orders experience more slippage due to market impact.

    Args:
        price: Expected execution price per share
        quantity: Number of shares
        side: "BUY" or "SELL"
        model: Slippage model configuration

    Returns:
        Slippage amount (positive for worse execution, negative for better)
    """
    if model is None:
        model = SlippageModel()

    # Calculate order value
    order_value = float(price * quantity)

    # Base slippage
    slippage_pct = model.base_slippage

    # Add size impact (more slippage for larger orders)
    size_component = (order_value / 1000.0) * model.size_impact
    slippage_pct += size_component

    # Cap at maximum
    slippage_pct = min(slippage_pct, model.max_slippage)

    # Direction: BUY pays more, SELL receives less
    direction = 1 if side == "BUY" else -1

    slippage = Decimal(str(slippage_pct)) * price * direction

    return slippage
