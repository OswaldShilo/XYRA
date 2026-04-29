"""
XYRA — Digital Twin
One SKUDigitalTwin object per product, held in memory.
Updates on every sale event; exposes a snapshot for the WebSocket broadcaster.
"""

from collections import deque
from datetime import datetime
from typing import Dict


class SKUDigitalTwin:
    """
    Live in-memory representation of a single SKU.

    Attributes
    ----------
    product_id   : str
    category     : str
    current_stock: float   — units on shelf
    velocity     : float   — rolling average units sold per event
    risk_level   : str     — CRITICAL | WARNING | SAFE
    days_to_stockout : float
    """

    MAXLEN = 30  # rolling window for velocity calculation

    def __init__(
        self,
        product_id: str,
        category: str = "general",
        current_stock: float = 0.0,
        velocity: float = 0.0,
    ):
        self.product_id = product_id
        self.category = category
        self.current_stock = max(0.0, float(current_stock))
        self._sales: deque = deque(maxlen=self.MAXLEN)
        self.velocity = float(velocity)
        self.risk_level = "SAFE"
        self.days_to_stockout: float = float("inf")
        self.total_units_sold: float = 0.0
        self.last_updated = datetime.now().isoformat()
        self._recalculate()

    # ── Public API ─────────────────────────────────────────────────────────────

    def update_sale(self, qty_sold: float) -> None:
        """Record a sale event and update all derived metrics."""
        qty_sold = max(0.0, float(qty_sold))
        self.current_stock = max(0.0, self.current_stock - qty_sold)
        self._sales.append(qty_sold)
        self.total_units_sold += qty_sold
        self._recalculate()
        self.last_updated = datetime.now().isoformat()

    def restock(self, qty_added: float) -> None:
        """Record a stock replenishment."""
        self.current_stock += max(0.0, float(qty_added))
        self._recalculate()
        self.last_updated = datetime.now().isoformat()

    def snapshot(self) -> dict:
        """Return a JSON-serialisable summary of the twin's current state."""
        return {
            "product_id": self.product_id,
            "category": self.category,
            "current_stock": round(self.current_stock, 2),
            "velocity": round(self.velocity, 3),
            "days_to_stockout": (
                round(self.days_to_stockout, 2)
                if self.days_to_stockout != float("inf")
                else 999
            ),
            "risk_level": self.risk_level,
            "total_units_sold": round(self.total_units_sold, 2),
            "last_updated": self.last_updated,
        }

    # ── Internals ──────────────────────────────────────────────────────────────

    def _recalculate(self) -> None:
        if self._sales:
            self.velocity = sum(self._sales) / len(self._sales)

        if self.velocity > 0:
            self.days_to_stockout = self.current_stock / self.velocity
        else:
            self.days_to_stockout = float("inf")

        if self.days_to_stockout <= 3:
            self.risk_level = "CRITICAL"
        elif self.days_to_stockout <= 7:
            self.risk_level = "WARNING"
        else:
            self.risk_level = "SAFE"


# Module-level registry — shared by webhook_receiver, poller, and ws_broadcaster
twin_registry: Dict[str, SKUDigitalTwin] = {}
