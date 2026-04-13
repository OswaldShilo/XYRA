"""
FLUX — Layer 2: Demand Forecasting (Prophet)
Generates 7-day and 30-day forecast per SKU with Indian holiday regressors
"""

import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, List
import warnings
warnings.filterwarnings("ignore")


INDIAN_HOLIDAYS = pd.DataFrame({
    "holiday": [
        "Pongal", "Pongal", "Republic_Day", "Republic_Day",
        "Holi", "Holi", "Independence_Day", "Independence_Day",
        "Diwali", "Diwali", "Dussehra", "Dussehra",
        "Christmas", "Christmas", "New_Year", "New_Year",
        "Eid", "Onam", "Navratri", "Ganesh_Chaturthi",
        "IPL_Start", "IPL_End",
    ],
    "ds": pd.to_datetime([
        "2024-01-14", "2025-01-14",
        "2024-01-26", "2025-01-26",
        "2024-03-25", "2025-03-14",
        "2024-08-15", "2025-08-15",
        "2024-11-01", "2025-10-20",
        "2024-10-12", "2025-10-02",
        "2024-12-25", "2025-12-25",
        "2024-01-01", "2025-01-01",
        "2024-04-10",
        "2024-09-15",
        "2024-10-03",
        "2024-09-07",
        "2024-03-22",
        "2024-05-26",
    ]),
    "lower_window": [
        -2, -2, -1, -1, -1, -1, -1, -1,
        -3, -3, -1, -1, -1, -1, -1, -1,
        -2, -3, -2, -2, 0, 0,
    ],
    "upper_window": [
        1, 1, 1, 1, 1, 1, 1, 1,
        2, 2, 1, 1, 1, 1, 1, 1,
        1, 2, 3, 2, 60, 0,
    ],
})


def forecast_product(
    product_df: pd.DataFrame,
    product_id: str,
    horizon_days: int = 30,
) -> Dict:
    """
    Runs Prophet on a single product's smoothed sales history.
    Returns forecast dict with 7-day and 30-day predictions.
    """
    # Prophet needs ds (date) and y (value)
    ts = product_df[["date", "smoothed_sales"]].rename(
        columns={"date": "ds", "smoothed_sales": "y"}
    ).copy()
    ts = ts.dropna(subset=["y"])

    if len(ts) < 10:
        return _insufficient_data_response(product_id)

    # Cap y at 0 (no negative sales)
    ts["y"] = ts["y"].clip(lower=0)

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        holidays=INDIAN_HOLIDAYS,
        interval_width=0.80,          # 80% confidence interval
        changepoint_prior_scale=0.05,  # conservative — prevents overfitting on short data
        seasonality_prior_scale=10,
    )

    model.fit(ts)

    future = model.make_future_dataframe(periods=horizon_days, freq="D")
    forecast = model.predict(future)

    # Extract future predictions only
    future_fc = forecast[forecast["ds"] > ts["ds"].max()].copy()
    future_fc["yhat"] = future_fc["yhat"].clip(lower=0).round(1)
    future_fc["yhat_lower"] = future_fc["yhat_lower"].clip(lower=0).round(1)
    future_fc["yhat_upper"] = future_fc["yhat_upper"].clip(lower=0).round(1)

    # Rolling baseline for spike detection
    historical_mean = ts["y"].rolling(28, min_periods=7).mean().iloc[-1]
    if historical_mean is None or historical_mean == 0:
        historical_mean = ts["y"].mean()

    # Spike score: ratio of forecasted mean vs historical mean
    next_7_mean = future_fc.head(7)["yhat"].mean()
    spike_score = round(next_7_mean / (historical_mean + 1e-9), 2)

    return {
        "product_id": product_id,
        "forecast_7d": _serialize_forecast(future_fc.head(7)),
        "forecast_30d": _serialize_forecast(future_fc),
        "total_demand_7d": round(float(future_fc.head(7)["yhat"].sum()), 1),
        "total_demand_30d": round(float(future_fc["yhat"].sum()), 1),
        "spike_score": spike_score,     # >1.2 = spike expected
        "historical_daily_avg": round(float(historical_mean), 2),
        "peak_day": str(future_fc.loc[future_fc["yhat"].idxmax(), "ds"].date()),
    }


def forecast_all(df: pd.DataFrame, horizon_days: int = 30) -> Dict[str, Dict]:
    """Run forecasting for all products in the DataFrame."""
    results = {}
    for pid in df["product_id"].unique():
        product_df = df[df["product_id"] == pid].copy()
        results[pid] = forecast_product(product_df, pid, horizon_days)
    return results


def _serialize_forecast(fc: pd.DataFrame) -> List[Dict]:
    return [
        {
            "date": str(row["ds"].date()),
            "predicted": row["yhat"],
            "lower": row["yhat_lower"],
            "upper": row["yhat_upper"],
        }
        for _, row in fc.iterrows()
    ]


def _insufficient_data_response(product_id: str) -> Dict:
    return {
        "product_id": product_id,
        "forecast_7d": [],
        "forecast_30d": [],
        "total_demand_7d": 0,
        "total_demand_30d": 0,
        "spike_score": 1.0,
        "historical_daily_avg": 0,
        "peak_day": None,
        "warning": "Insufficient data for forecasting (need 10+ data points)",
    }
