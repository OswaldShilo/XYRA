"""
FLUX — Utilities
Validators, helpers, and common functions
"""

import pandas as pd
from typing import Tuple, List, Dict, Any


def validate_csv_structure(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that CSV has minimum required columns.
    
    Returns: (is_valid, error_messages)
    """
    errors = []

    if df.empty:
        errors.append("CSV file is empty")
        return False, errors

    required_patterns = ['date', 'product', 'units', 'stock']
    cols_lower = {col.lower(): col for col in df.columns}

    # Check for at least some required columns
    found = sum(1 for pattern in required_patterns if any(pattern in col for col in cols_lower.keys()))

    if found < 2:
        errors.append(f"CSV must have at least date and product columns. Found columns: {list(df.columns)}")
        return False, errors

    return True, errors


def validate_feedback(payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate feedback payload structure."""
    errors = []

    required_fields = ['product_id', 'recommendation_id', 'accepted']
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    if not isinstance(payload.get('accepted'), bool):
        errors.append("'accepted' must be boolean")

    if 'actual_qty_ordered' in payload:
        if not isinstance(payload['actual_qty_ordered'], (int, float)):
            errors.append("'actual_qty_ordered' must be numeric")
        if payload['actual_qty_ordered'] < 0:
            errors.append("'actual_qty_ordered' cannot be negative")

    return len(errors) == 0, errors


def format_json_response(data: Any, status: str = "success") -> Dict[str, Any]:
    """Format standardized JSON response."""
    return {
        "status": status,
        "timestamp": pd.Timestamp.now().isoformat(),
        "data": data,
    }
