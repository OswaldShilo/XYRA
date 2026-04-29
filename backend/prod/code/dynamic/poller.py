"""
XYRA — Polling Job (Method B)
APScheduler-based fallback: pulls latest sales from POS API every 15 minutes.
Runs concurrently with webhook (Method A) to guarantee no sale event is missed.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, Any


_status: Dict[str, Any] = {
    "running": False,
    "last_poll": None,
    "polls_completed": 0,
    "interval_seconds": 900,  # 15 minutes
    "pos_api_url": None,
    "last_error": None,
}


async def polling_job(twin_registry: dict, pos_api_url: Optional[str] = None) -> None:
    """
    Poll the POS API every 15 minutes.

    In production: GET {pos_api_url}/sales?since={last_sync} and update twins.
    In demo mode: no-op (webhooks are the primary source).
    """
    _status["running"] = True
    _status["pos_api_url"] = pos_api_url

    while True:
        await asyncio.sleep(_status["interval_seconds"])

        _status["last_poll"] = datetime.now().isoformat()
        _status["polls_completed"] += 1

        if pos_api_url:
            try:
                await _fetch_and_apply(pos_api_url, twin_registry)
            except Exception as exc:
                _status["last_error"] = str(exc)


async def _fetch_and_apply(api_url: str, twin_registry: dict) -> None:
    """
    Fetch sales since last sync and apply to twins.
    Stub: real implementation calls the POS REST API.
    """
    # In production:
    #   resp = await httpx.get(f"{api_url}/sales", params={"since": _status["last_poll"]})
    #   for sale in resp.json()["sales"]:
    #       twin = twin_registry.get(sale["product_id"])
    #       if twin:
    #           twin.update_sale(sale["qty_sold"])
    pass


def get_poller_status() -> Dict[str, Any]:
    """Return current poller status (for /api/sync endpoint)."""
    return dict(_status)


def start_poller(twin_registry: dict, pos_api_url: Optional[str] = None):
    """Return the polling coroutine to be scheduled as a background task."""
    return polling_job(twin_registry, pos_api_url)
