"""Trading simulator module"""
from app.simulator.executor import OrderExecutor, Order, OrderResult
from app.simulator.slippage import SlippageModel, calculate_slippage
from app.simulator.fees import FeeCalculator, calculate_fees
from app.simulator.broker_adapter import BrokerAdapter, PaperBrokerAdapter

__all__ = [
    "OrderExecutor",
    "Order",
    "OrderResult",
    "SlippageModel",
    "calculate_slippage",
    "FeeCalculator",
    "calculate_fees",
    "BrokerAdapter",
    "PaperBrokerAdapter",
]
