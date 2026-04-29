"""
XYRA — WebSocket Broadcaster
Manages live WebSocket connections and pushes dashboard snapshots every 5 seconds.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict

from fastapi import WebSocket


class ConnectionManager:
    """Manages the set of active WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """Send a message to all connected clients, dropping dead connections."""
        dead: List[WebSocket] = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Module-level singleton used by main.py
ws_manager = ConnectionManager()


async def broadcast_loop(manager: ConnectionManager, twin_registry: Dict) -> None:
    """
    Background task: every 5 seconds, snapshot all digital twins and broadcast
    to every connected WebSocket client.
    """
    while True:
        await asyncio.sleep(5)

        if not manager.active_connections:
            continue

        twins_snapshot = {pid: twin.snapshot() for pid, twin in twin_registry.items()}

        critical = sum(1 for t in twin_registry.values() if t.risk_level == "CRITICAL")
        warning = sum(1 for t in twin_registry.values() if t.risk_level == "WARNING")
        safe = sum(1 for t in twin_registry.values() if t.risk_level == "SAFE")

        payload = {
            "type": "dashboard_update",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "twins": twins_snapshot,
                "summary": {
                    "total": len(twin_registry),
                    "critical": critical,
                    "warning": warning,
                    "safe": safe,
                },
                "alerts": [
                    t for t in twins_snapshot.values()
                    if t["risk_level"] in ("CRITICAL", "WARNING")
                ],
            },
        }

        await manager.broadcast(json.dumps(payload))
