"""Broker adapter interface for future real broker integration"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal


class BrokerAdapter(ABC):
    """
    Abstract interface for broker integration

    WARNING: This interface is for FUTURE broker integration.
    Current implementation uses paper trading only (simulated=True).

    Before enabling real broker integration:
    1. Implement proper authentication and API key management
    2. Add rate limiting and circuit breakers
    3. Implement order validation and risk checks
    4. Add audit logging for all real trades
    5. Require explicit user confirmation for live trading
    6. Test extensively in broker sandbox environment
    7. Implement position reconciliation
    8. Add real-time balance checks

    DO NOT connect to live broker without explicit configuration.
    """

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        order_type: str = "market",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Place an order with the broker"""
        pass

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass

    @abstractmethod
    async def get_positions(self) -> Dict[str, Any]:
        """Get current positions"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass


class PaperBrokerAdapter(BrokerAdapter):
    """
    Paper trading broker adapter (mock implementation)

    This is a placeholder that returns mock data.
    All orders are marked as simulated=True.
    No actual broker API calls are made.
    """

    async def place_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
        order_type: str = "market",
        price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Simulate order placement"""
        return {
            "order_id": "PAPER_ORDER_123",
            "symbol": symbol,
            "quantity": float(quantity),
            "side": side,
            "status": "filled",
            "simulated": True,
            "message": "Paper trade - no real broker connection"
        }

    async def get_account_info(self) -> Dict[str, Any]:
        """Return mock account info"""
        return {
            "account_id": "PAPER_ACCOUNT",
            "cash": 100000.0,
            "buying_power": 100000.0,
            "simulated": True
        }

    async def get_positions(self) -> Dict[str, Any]:
        """Return empty positions"""
        return {
            "positions": [],
            "simulated": True
        }

    async def cancel_order(self, order_id: str) -> bool:
        """Simulate order cancellation"""
        return True
