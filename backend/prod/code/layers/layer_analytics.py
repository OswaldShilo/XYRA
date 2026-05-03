"""
FLUX — Layer Analytics: 5 post-pipeline analytics functions.
Called on the cleaned DataFrame (pre-DSP) + pipeline outputs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict, List


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_risk(risk_str: str) -> str:
    """Strip emoji prefix from risk level strings."""
    return (
        risk_str.replace("🔴 ", "").replace("🟡 ", "").replace("🟢 ", "").upper().strip()
    )


def _safe_float(v: Any) -> float:
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return 0.0


# ── 1. Inventory Health ───────────────────────────────────────────────────────

def compute_inventory_health(
    df: pd.DataFrame,
    classifications: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Horizontal bar chart: top 15 SKUs sorted by days-to-stockout (ascending).
    Shape: [{ sku, category, days_to_stockout, risk_level, current_stock }]
    """
    rows: List[Dict[str, Any]] = []
    for c in classifications:
        d = c.get("days_to_stockout", 99.0)
        if d == float("inf") or d != d:  # inf or NaN
            d = 99.0
        rows.append(
            {
                "sku": c.get("product_id", "?"),
                "category": c.get("category", "general"),
                "days_to_stockout": round(float(d), 1),
                "risk_level": _clean_risk(c.get("risk_level", "SAFE")),
                "current_stock": int(c.get("current_stock", 0)),
            }
        )
    rows.sort(key=lambda x: x["days_to_stockout"])
    return rows[:15]


# ── 2. Demand Patterns ────────────────────────────────────────────────────────

def compute_demand_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Area chart: daily totals + day-of-week averages + category breakdown.
    Shape: { daily: [...], by_dow: [...], by_category: [...] }
    """
    if df.empty:
        return {"daily": [], "by_dow": [], "by_category": []}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Daily totals
    daily = (
        df.groupby("date")["units_sold"]
        .sum()
        .reset_index()
        .sort_values("date")
    )
    daily_list = [
        {"date": row["date"].strftime("%Y-%m-%d"), "units_sold": _safe_float(row["units_sold"])}
        for _, row in daily.iterrows()
    ]

    # Day-of-week averages
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df["dow"] = df["date"].dt.day_name()
    dow = df.groupby("dow")["units_sold"].mean().reset_index()
    dow["dow"] = pd.Categorical(dow["dow"], categories=dow_order, ordered=True)
    dow = dow.sort_values("dow")
    dow_list = [
        {"day": str(row["dow"]), "avg_units": _safe_float(row["units_sold"])}
        for _, row in dow.iterrows()
    ]

    # Category breakdown
    if "category" in df.columns:
        cat = (
            df.groupby("category")["units_sold"]
            .sum()
            .reset_index()
            .sort_values("units_sold", ascending=False)
        )
        total = float(cat["units_sold"].sum()) or 1.0
        cat_list = [
            {
                "category": str(row["category"]),
                "units_sold": _safe_float(row["units_sold"]),
                "pct": round(float(row["units_sold"]) / total * 100, 1),
            }
            for _, row in cat.iterrows()
        ]
    else:
        cat_list = []

    return {"daily": daily_list, "by_dow": dow_list, "by_category": cat_list}


# ── 3. Spike Detection ────────────────────────────────────────────────────────

def compute_spike_detection(
    df: pd.DataFrame,
    forecasts: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Top 5 products by spike_score: last-30-day actuals + 7-day forecast with
    confidence band.
    Shape: [{ product_id, spike_score, is_spike, history: [...], forecast: [...] }]
    """
    if df.empty or not forecasts:
        return []

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    ranked = sorted(
        forecasts.items(),
        key=lambda kv: kv[1].get("spike_score", 1.0),
        reverse=True,
    )[:5]

    result: List[Dict[str, Any]] = []
    for pid, fc in ranked:
        prod_df = (
            df[df["product_id"] == pid]
            .groupby("date")["units_sold"]
            .sum()
            .reset_index()
            .sort_values("date")
            .tail(30)
        )

        history = [
            {
                "date": row["date"].strftime("%Y-%m-%d"),
                "actual": _safe_float(row["units_sold"]),
            }
            for _, row in prod_df.iterrows()
        ]

        last_date_raw = fc.get("last_date")
        try:
            last_date = pd.to_datetime(last_date_raw)
        except Exception:
            last_date = pd.Timestamp.now()

        forecast_7d = fc.get("forecast_7d", [])[:7]
        lower = fc.get("confidence_lower", [])[:7]
        upper = fc.get("confidence_upper", [])[:7]

        forecast_pts = []
        for i, val in enumerate(forecast_7d):
            d = last_date + pd.Timedelta(days=i + 1)
            forecast_pts.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "forecast": _safe_float(val),
                    "lower": _safe_float(lower[i] if i < len(lower) else val * 0.8),
                    "upper": _safe_float(upper[i] if i < len(upper) else val * 1.2),
                }
            )

        result.append(
            {
                "product_id": pid,
                "spike_score": _safe_float(fc.get("spike_score", 1.0)),
                "is_spike": float(fc.get("spike_score", 1.0)) > 1.3,
                "method": fc.get("method", "unknown"),
                "history": history,
                "forecast": forecast_pts,
            }
        )

    return result


# ── 4. Historical Comparison ──────────────────────────────────────────────────

def compute_historical_comparison(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Monthly totals + MoM % growth + YoY per-category breakdown.
    Shape: { monthly: [...], mom: [...], yoy: [...] }
    """
    if df.empty:
        return {"monthly": [], "mom": [], "yoy": []}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["year_month"] = df["date"].dt.strftime("%Y-%m")

    # Monthly totals
    monthly = (
        df.groupby("year_month")["units_sold"]
        .sum()
        .reset_index()
        .sort_values("year_month")
    )
    monthly_list = [
        {"month": row["year_month"], "units_sold": _safe_float(row["units_sold"])}
        for _, row in monthly.iterrows()
    ]

    # MoM growth
    monthly["prev"] = monthly["units_sold"].shift(1)
    monthly["mom_pct"] = (
        (monthly["units_sold"] - monthly["prev"]) / monthly["prev"] * 100
    ).round(1)
    mom_list = [
        {
            "month": row["year_month"],
            "mom_pct": None if pd.isna(row["mom_pct"]) else float(row["mom_pct"]),
        }
        for _, row in monthly.iterrows()
    ]

    # YoY per category
    if "category" in df.columns:
        yoy_df = (
            df.groupby(["year", "category"])["units_sold"].sum().reset_index()
        )
        years = sorted(yoy_df["year"].unique())
        cats = yoy_df["category"].unique().tolist()
        yoy_list: List[Dict[str, Any]] = []
        for cat in cats:
            cat_data = yoy_df[yoy_df["category"] == cat]
            entry: Dict[str, Any] = {"category": str(cat)}
            for yr in years:
                row = cat_data[cat_data["year"] == yr]
                entry[str(int(yr))] = (
                    _safe_float(row["units_sold"].values[0]) if len(row) > 0 else 0.0
                )
            yoy_list.append(entry)
    else:
        yoy_agg = df.groupby("year")["units_sold"].sum().reset_index()
        yoy_list = [
            {"year": int(row["year"]), "units_sold": _safe_float(row["units_sold"])}
            for _, row in yoy_agg.iterrows()
        ]

    return {"monthly": monthly_list, "mom": mom_list, "yoy": yoy_list}


# ── 5. Forecast Accuracy ──────────────────────────────────────────────────────

def compute_forecast_accuracy(
    df: pd.DataFrame,
    forecasts: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    MAPE per product: compares last-7-day actuals vs forecast_7d values.
    Shape: [{ product_id, category, mape, accuracy_pct, method }]
    Sorted by accuracy ascending (worst first → easy to spot).
    """
    if df.empty or not forecasts:
        return []

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    results: List[Dict[str, Any]] = []
    for pid, fc in forecasts.items():
        prod_df = (
            df[df["product_id"] == pid]
            .groupby("date")["units_sold"]
            .sum()
            .reset_index()
            .sort_values("date")
        )

        if len(prod_df) < 7:
            continue

        actuals = prod_df["units_sold"].tail(7).values.astype(float)
        preds = np.array(fc.get("forecast_7d", [])[:7], dtype=float)

        if len(preds) < 7:
            continue

        preds = preds[: len(actuals)]
        mask = actuals > 0
        if mask.sum() == 0:
            continue

        mape = float(
            np.mean(np.abs((actuals[mask] - preds[mask]) / actuals[mask])) * 100
        )
        mape = round(mape, 1)
        accuracy = round(max(0.0, 100.0 - mape), 1)

        cat_col = df[df["product_id"] == pid]
        category = (
            str(cat_col["category"].mode().iloc[0])
            if "category" in df.columns and len(cat_col) > 0
            else "general"
        )

        results.append(
            {
                "product_id": pid,
                "category": category,
                "mape": mape,
                "accuracy_pct": accuracy,
                "method": fc.get("method", "unknown"),
            }
        )

    results.sort(key=lambda x: x["accuracy_pct"])
    return results[:20]


# ── Entry point ───────────────────────────────────────────────────────────────

def compute_all_analytics(
    df: pd.DataFrame,
    classifications: List[Dict[str, Any]],
    forecasts: Dict[str, Any],
) -> Dict[str, Any]:
    """Run all 5 analytics on the cleaned DataFrame. Call in _run_pipeline."""
    return {
        "inventory_health": compute_inventory_health(df, classifications),
        "demand_patterns": compute_demand_patterns(df),
        "spike_detection": compute_spike_detection(df, forecasts),
        "historical_comparison": compute_historical_comparison(df),
        "forecast_accuracy": compute_forecast_accuracy(df, forecasts),
    }
