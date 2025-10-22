"""Transaction fee calculation"""
from decimal import Decimal
from dataclasses import dataclass


@dataclass
class FeeCalculator:
    """Configuration for fee calculation"""
    # Fee tiers based on risk profile
    conservative_fee_pct: float = 0.001  # 0.1%
    moderate_fee_pct: float = 0.0005  # 0.05%
    aggressive_fee_pct: float = 0.0002  # 0.02%
    min_fee: float = 0.01  # Minimum $0.01 fee


def calculate_fees(
    price: Decimal,
    quantity: Decimal,
    risk_profile: str,
    calculator: FeeCalculator | None = None
) -> Decimal:
    """
    Calculate transaction fees for an order

    Fees vary based on risk profile:
    - Conservative: Higher fees (0.1%) - simulates full-service broker
    - Moderate: Medium fees (0.05%) - simulates standard broker
    - Aggressive: Lower fees (0.02%) - simulates discount broker

    Args:
        price: Execution price per share
        quantity: Number of shares
        risk_profile: "conservative", "moderate", or "aggressive"
        calculator: Fee calculator configuration

    Returns:
        Total fees for the transaction
    """
    if calculator is None:
        calculator = FeeCalculator()

    # Select fee percentage based on risk profile
    if risk_profile == "conservative":
        fee_pct = calculator.conservative_fee_pct
    elif risk_profile == "aggressive":
        fee_pct = calculator.aggressive_fee_pct
    else:  # moderate
        fee_pct = calculator.moderate_fee_pct

    # Calculate fee
    order_value = price * quantity
    fee = Decimal(str(fee_pct)) * order_value

    # Ensure minimum fee
    min_fee_decimal = Decimal(str(calculator.min_fee))
    fee = max(fee, min_fee_decimal)

    return fee
