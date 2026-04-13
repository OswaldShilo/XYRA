"""
FLUX — Helper Functions
Common utilities for the pipeline
"""

from datetime import datetime, timedelta
import json


def get_pincode_or_default(stored_pincode: str = None) -> str:
    """Get pincode from env or stored value."""
    import os
    return stored_pincode or os.getenv("STORE_PINCODE", "600001")


def get_lead_time_or_default(stored_lead_time: int = None) -> int:
    """Get lead time from env or stored value."""
    import os
    return stored_lead_time or int(os.getenv("LEAD_TIME_DAYS", "2"))


def format_date(date_obj) -> str:
    """Format datetime to ISO string."""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.isoformat()


def days_until(target_date: str) -> int:
    """Calculate days until a date."""
    target = datetime.fromisoformat(target_date)
    today = datetime.now()
    return (target - today).days


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default."""
    if denominator == 0:
        return default
    return numerator / denominator
