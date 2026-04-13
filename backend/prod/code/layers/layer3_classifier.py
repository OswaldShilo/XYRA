"""
FLUX — Layer 3: Risk Classification
Classify products as CRITICAL / WARNING / SAFE based on stock-to-forecast ratio
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta


def classify_products(
    df: pd.DataFrame,
    forecasts: Dict[str, Dict[str, Any]],
    external_multipliers: Dict[str, float] = None,
    lead_time: int = 2,
) -> List[Dict[str, Any]]:
    """
    Classify products based on stock levels vs forecasts.
    
    External multipliers (events, weather, learned) adjust forecast spike.
    Lead time is procurement lead time in days.
    
    Returns: List of classification dicts with reorder recommendations
    """
    if external_multipliers is None:
        external_multipliers = {}

    if df.empty or not forecasts:
        return []

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Get latest data per product
    latest_data = df.sort_values('date').groupby('product_id').tail(1)

    classifications = []

    for _, row in latest_data.iterrows():
        product_id = row['product_id']
        current_stock = max(0, row['current_stock'])
        category = row.get('category', 'general')

        if product_id not in forecasts:
            continue

        forecast_data = forecasts[product_id]
        forecast_30d = forecast_data['forecast_30d']
        spike_score = forecast_data['spike_score']

        # Get category multiplier (event + weather)
        cat_multiplier = external_multipliers.get(category, 1.0)

        # Adjusted forecast with external signals
        forecast_30d_adjusted = [f * cat_multiplier for f in forecast_30d]
        avg_daily_forecast = np.mean(forecast_30d_adjusted[:7]) if forecast_30d_adjusted else 1.0

        # Calculate days to stockout
        days_to_stockout = current_stock / avg_daily_forecast if avg_daily_forecast > 0 else float('inf')

        # Effective days accounting for lead time and spike
        effective_days = days_to_stockout / (spike_score * cat_multiplier) if spike_score > 0 else days_to_stockout

        # Classification logic
        if effective_days <= 3:
            risk_level = "🔴 CRITICAL"
            priority = 1
        elif effective_days <= 7:
            risk_level = "🟡 WARNING"
            priority = 2
        else:
            risk_level = "🟢 SAFE"
            priority = 3

        # Calculate reorder quantity
        # Reorder enough for: forecast_14d * lead_time + 7 days buffer - current_stock
        forecast_14d = np.sum(forecast_30d_adjusted[:14])
        buffer_days_forecast = np.mean(forecast_30d_adjusted[:7]) * 7
        reorder_qty = max(0, int(np.ceil(forecast_14d + buffer_days_forecast - current_stock)))

        # Reorder by date
        reorder_by_date = (datetime.now() + timedelta(days=days_to_stockout - lead_time)).date().isoformat()

        classifications.append({
            'product_id': product_id,
            'category': category,
            'current_stock': current_stock,
            'risk_level': risk_level,
            'priority': priority,
            'days_to_stockout': round(days_to_stockout, 2),
            'effective_days': round(effective_days, 2),
            'forecast_7d_avg': round(np.mean(forecast_30d_adjusted[:7]), 2),
            'forecast_14d_total': round(forecast_14d, 2),
            'reorder_qty': reorder_qty,
            'reorder_by_date': reorder_by_date,
            'spike_score': round(spike_score, 2),
            'external_multiplier': round(cat_multiplier, 2),
            'reason': _generate_reason(risk_level, days_to_stockout, spike_score, cat_multiplier),
        })

    # Sort by priority
    classifications.sort(key=lambda x: x['priority'])
    return classifications


def _generate_reason(risk_level: str, days_to_stockout: float, spike_score: float, multiplier: float) -> str:
    """Generate human-readable reason for classification."""
    parts = []

    if days_to_stockout < float('inf'):
        parts.append(f"Stock covers ~{days_to_stockout:.1f} days")

    if spike_score > 1.3:
        parts.append(f"Demand spike expected ({spike_score:.1f}x baseline)")

    if multiplier > 1.3:
        parts.append(f"Events/weather increase demand ({multiplier:.1f}x)")

    if not parts:
        parts.append("Normal stock levels")

    return " | ".join(parts)
