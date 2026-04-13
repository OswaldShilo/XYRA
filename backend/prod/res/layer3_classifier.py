"""
FLUX — Layer 3: Risk Classification
Classifies each SKU as Critical / Warning / Safe and calculates reorder quantity
"""

import pandas as pd
import math
from typing import Dict, List
from datetime import date, timedelta


RISK_CRITICAL = "CRITICAL"
RISK_WARNING  = "WARNING"
RISK_SAFE     = "SAFE"

DEFAULT_LEAD_TIME_DAYS = 2   # days from order to delivery


def classify_products(
    df: pd.DataFrame,
    forecasts: Dict,
    event_multipliers: Dict,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
) -> List[Dict]:
    """
    For each product, compute risk level and reorder recommendation.

    Args:
        df: cleaned + filtered DataFrame (latest stock per product)
        forecasts: output from layer2_forecaster.forecast_all()
        event_multipliers: output from layer4_events (category → multiplier)
        lead_time_days: supplier delivery time in days

    Returns:
        List of product risk cards sorted by urgency
    """
    results = []

    # Get latest stock snapshot per product
    latest = (
        df.sort_values("date")
        .groupby("product_id")
        .last()
        .reset_index()[["product_id", "product_name", "current_stock", "category"]]
    )

    for _, row in latest.iterrows():
        pid = row["product_id"]
        fc = forecasts.get(pid, {})

        avg_daily = fc.get("historical_daily_avg", 1)
        spike_score = fc.get("spike_score", 1.0)
        demand_7d = fc.get("total_demand_7d", avg_daily * 7)
        demand_30d = fc.get("total_demand_30d", avg_daily * 30)

        category = row.get("category", "general")
        event_multiplier = event_multipliers.get(category, 1.0)

        # Combine spike score with event multiplier (take the higher signal)
        effective_multiplier = max(spike_score, event_multiplier)

        current_stock = float(row["current_stock"])

        # Effective days of stock accounting for upcoming spikes
        if avg_daily > 0:
            days_of_stock = current_stock / (avg_daily * effective_multiplier)
        else:
            days_of_stock = 999

        # Risk classification
        if days_of_stock <= 3:
            risk = RISK_CRITICAL
            urgency = 1
        elif days_of_stock <= 7:
            risk = RISK_WARNING
            urgency = 2
        else:
            risk = RISK_SAFE
            urgency = 3

        # Reorder quantity: cover next 14 days demand + lead time buffer - current stock
        reorder_qty = math.ceil(
            (demand_7d * 2 * effective_multiplier) + (avg_daily * lead_time_days) - current_stock
        )
        reorder_qty = max(reorder_qty, 0)

        # Reorder-by date
        reorder_by = (
            date.today() + timedelta(days=max(0, int(days_of_stock) - lead_time_days))
            if days_of_stock < 30
            else None
        )

        results.append({
            "product_id": pid,
            "product_name": row["product_name"],
            "category": category,
            "current_stock": int(current_stock),
            "risk_level": risk,
            "risk_emoji": {"CRITICAL": "🔴", "WARNING": "🟡", "SAFE": "🟢"}[risk],
            "days_to_stockout": round(days_of_stock, 1),
            "effective_multiplier": round(effective_multiplier, 2),
            "demand_forecast_7d": round(demand_7d, 1),
            "demand_forecast_30d": round(demand_30d, 1),
            "reorder_qty": reorder_qty,
            "reorder_by_date": str(reorder_by) if reorder_by else None,
            "urgency_rank": urgency,
            "peak_demand_day": fc.get("peak_day"),
        })

    # Sort: Critical first, then Warning, then Safe; within group by days_to_stockout asc
    results.sort(key=lambda x: (x["urgency_rank"], x["days_to_stockout"]))

    return results
