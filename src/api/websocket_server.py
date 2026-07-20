"""WebSocket server for real-time updates to Mission Control.

Bridges the internal EventBus to external WebSocket clients.
Decoupled from any specific backend provider.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.events import Event, EventBus

logger = logging.getLogger("websocket_server")


class WebSocketClient:
    """Represents a connected WebSocket client."""

    def __init__(self, websocket, client_id: str):
        self.ws = websocket
        self.client_id = client_id
        self.subscriptions: Set[str] = set()
        self.connected_at = datetime.now(timezone.utc)
        self._last_heartbeat: float = 0.0

    async def send_json(self, data: dict) -> bool:
        try:
            await self.ws.send_json(data)
            return True
        except Exception:
            return False

    async def send_event(self, event: Event) -> bool:
        payload = {
            "type": "event",
            "event_type": event.event_type.value,
            "source": event.source,
            "data": event.data,
            "mid": event.id,
            "timestamp": event.timestamp.isoformat(),
        }
        return await self.send_json(payload)

    async def heartbeat(self) -> bool:
        return await self.send_json({"type": "heartbeat", "timestamp": datetime.now(timezone.utc).isoformat()})


class WebSocketEventBridge:
    """Bridges EventBus events to WebSocket clients.

    Creates an internal EventBus listener and fans out events
    to all connected clients. Filterable by subscription patterns.
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus
        self._clients: Dict[str, WebSocketClient] = {}
        self._lock = asyncio.Lock()
        self._running = False
        self._bus_subscription_id: Optional[str] = None

    async def register_client(self, websocket, client_id: str) -> WebSocketClient:
        client = WebSocketClient(websocket, client_id)
        async with self._lock:
            self._clients[client_id] = client
        logger.info("WebSocket client connected: %s (%d total)", client_id, len(self._clients))
        return client

    async def unregister_client(self, client_id: str):
        async with self._lock:
            self._clients.pop(client_id, None)
        logger.info("WebSocket client disconnected: %s (%d remaining)", client_id, len(self._clients))

    def get_client_count(self) -> int:
        return len(self._clients)

    def get_client_ids(self) -> list:
        return list(self._clients.keys())

    async def broadcast_event(self, event: Event):
        """Fan out an event to all subscribed WebSocket clients."""
        if not self._clients:
            return
        disconnected = []
        async with self._lock:
            for cid, client in list(self._clients.items()):
                success = await client.send_event(event)
                if not success:
                    disconnected.append(cid)
            if disconnected:
                logger.warning("Removing %d stale WebSocket clients", len(disconnected))

    async def broadcast_raw(self, message: dict):
        if not self._clients:
            return
        disconnected = []
        async with self._lock:
            for cid, client in list(self._clients.items()):
                success = await client.send_json(message)
                if not success:
                    disconnected.append(cid)

    def start_bridge(self):
        """Start listening to the EventBus and forwarding to WebSocket."""
        if self._running:
            return
        self._running = True
        if self.event_bus and not self._bus_subscription_id:
            self._bus_subscription_id = self.event_bus.subscribe(
                event_type=None,  # all events
                source_pattern=None,
                callback=self._on_system_event,
                async_mode=True,
            )
            logger.info("WebSocket bridge subscribed to EventBus")

    def _on_system_event(self, event: Event):
        """Forward an EventBus event to all WebSocket clients."""
        if not self._running:
            return
        asyncio.create_task(self.broadcast_event(event))

    def stop_bridge(self):
        self._running = False
        if self.event_bus and self._bus_subscription_id:
            self.event_bus.unsubscribe(self._bus_subscription_id)
            self._bus_subscription_id = None


# Singleton for the running bridge
_bridge: Optional[WebSocketEventBridge] = None


def create_bridge(event_bus: EventBus) -> WebSocketEventBridge:
    global _bridge
    _bridge = WebSocketEventBridge(event_bus)
    return _bridge


def get_bridge() -> Optional[WebSocketEventBridge]:
    return _bridge
