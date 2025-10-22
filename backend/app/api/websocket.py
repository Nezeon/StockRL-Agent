"""WebSocket endpoint for real-time updates"""
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from typing import Dict, Set
import json
import asyncio
from uuid import UUID

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        # Map of channel to set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str):
        """Accept and register a new connection"""
        await websocket.accept()
        async with self.lock:
            if channel not in self.active_connections:
                self.active_connections[channel] = set()
            self.active_connections[channel].add(websocket)

    async def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a connection"""
        async with self.lock:
            if channel in self.active_connections:
                self.active_connections[channel].discard(websocket)
                if not self.active_connections[channel]:
                    del self.active_connections[channel]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific websocket"""
        try:
            await websocket.send_json(message)
        except:
            pass

    async def broadcast(self, channel: str, message: dict):
        """Broadcast message to all connections in a channel"""
        async with self.lock:
            if channel in self.active_connections:
                disconnected = set()
                for connection in self.active_connections[channel]:
                    try:
                        await connection.send_json(message)
                    except:
                        disconnected.add(connection)

                # Clean up disconnected clients
                for connection in disconnected:
                    self.active_connections[channel].discard(connection)


# Global manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, channel: str = Query(...)):
    """
    WebSocket endpoint for real-time updates

    Channels:
    - portfolio_updates:{portfolio_id} - Portfolio NAV and position updates
    - agent_stats:{agent_run_id} - Agent training metrics
    - trade_executed:{portfolio_id} - Trade execution notifications
    - market_data:{ticker} - Market data updates
    """
    await manager.connect(websocket, channel)
    try:
        while True:
            # Keep connection alive and handle messages
            data = await websocket.receive_text()

            # Parse message
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)
                elif msg_type == "subscribe":
                    new_channel = message.get("channel")
                    if new_channel:
                        await manager.connect(websocket, new_channel)
                        await manager.send_personal_message(
                            {"type": "subscribed", "channel": new_channel},
                            websocket
                        )
                elif msg_type == "unsubscribe":
                    old_channel = message.get("channel")
                    if old_channel:
                        await manager.disconnect(websocket, old_channel)
                        await manager.send_personal_message(
                            {"type": "unsubscribed", "channel": old_channel},
                            websocket
                        )

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket, channel)


async def broadcast_portfolio_update(portfolio_id: UUID, data: dict):
    """Broadcast portfolio update to subscribers"""
    channel = f"portfolio_updates:{portfolio_id}"
    message = {
        "type": "portfolio_update",
        "portfolio_id": str(portfolio_id),
        "data": data
    }
    await manager.broadcast(channel, message)


async def broadcast_agent_metric(agent_run_id: UUID, metric: dict):
    """Broadcast agent metric to subscribers"""
    channel = f"agent_stats:{agent_run_id}"
    message = {
        "type": "agent_metric",
        "agent_run_id": str(agent_run_id),
        "metric": metric
    }
    await manager.broadcast(channel, message)


async def broadcast_trade_executed(portfolio_id: UUID, trade: dict):
    """Broadcast trade execution to subscribers"""
    channel = f"trade_executed:{portfolio_id}"
    message = {
        "type": "trade_executed",
        "portfolio_id": str(portfolio_id),
        "trade": trade
    }
    await manager.broadcast(channel, message)
