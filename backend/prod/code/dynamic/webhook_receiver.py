"""
XYRA — Webhook Receiver
Processes real-time sale events pushed by a POS system.
The actual FastAPI route lives in main.py; this module contains the pure logic.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from dynamic.digital_twin import SKUDigitalTwin, twin_registry


def process_sale_event(
    product_id: str,
    qty_sold: float,
    category: str = "general",
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle an incoming POS sale event.

    - Finds or auto-creates the digital twin for the product.
    - Subtracts qty_sold from current_stock.
    - Recalculates velocity, days_to_stockout, and risk_level.

    Returns the updated twin snapshot.
    """
    twin = twin_registry.get(product_id)
    if twin is None:
        twin = SKUDigitalTwin(
            product_id=product_id,
            category=category,
            current_stock=100.0,  # safe default for unknown products
        )
        twin_registry[product_id] = twin

    twin.update_sale(qty_sold)

    return {
        "received_at": timestamp or datetime.now().isoformat(),
        "twin": twin.snapshot(),
    }


def process_restock_event(
    product_id: str,
    qty_added: float,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Handle a stock replenishment event."""
    twin = twin_registry.get(product_id)
    if twin is None:
        raise KeyError(f"Product {product_id} not tracked. POST to /api/init-twins first.")

    twin.restock(qty_added)

    return {
        "received_at": timestamp or datetime.now().isoformat(),
        "twin": twin.snapshot(),
    }
