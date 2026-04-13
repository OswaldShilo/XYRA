"""
FLUX — Layer 1.5: DSP Noise Filtering
Smooths time series, removes outliers, decomposes signal before forecasting
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL
from typing import Dict, Tuple


def filter_noise(df: pd.DataFrame, product_id: str = None) -> Tuple[pd.DataFrame, dict]:
    """
    Apply DSP filtering to the full cleaned DataFrame.
    Returns smoothed DataFrame + decomposition report per product.
    """
    report = {}
    filtered_frames = []

    products = df["product_id"].unique() if product_id is None else [product_id]

    for pid in products:
        product_df = df[df["product_id"] == pid].copy().sort_values("date")

        if len(product_df) < 14:
            # Not enough data — skip filtering, pass through as-is
            product_df["smoothed_sales"] = product_df["units_sold"]
            product_df["is_outlier"] = False
            product_df["trend"] = product_df["units_sold"]
            product_df["seasonal"] = 0.0
            product_df["residual"] = 0.0
            filtered_frames.append(product_df)
            report[pid] = {"status": "skipped — insufficient data", "outliers_removed": 0}
            continue

        series = product_df["units_sold"].values.astype(float)

        # --- Step 1: Z-score outlier detection ---
        mean, std = np.mean(series), np.std(series)
        z_scores = np.abs((series - mean) / (std + 1e-9))
        outlier_mask = z_scores > 3.0

        # Clip outliers to 3σ boundary instead of removing
        clipped = np.where(outlier_mask, mean + 3 * std * np.sign(series - mean), series)
        product_df["is_outlier"] = outlier_mask

        # --- Step 2: IQR clipping ---
        q1, q3 = np.percentile(clipped, 25), np.percentile(clipped, 75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        clipped = np.clip(clipped, lower, upper)

        # --- Step 3: Rolling average smoothing (7-day window) ---
        smoothed = (
            pd.Series(clipped)
            .rolling(window=7, min_periods=1, center=True)
            .mean()
            .values
        )
        product_df["smoothed_sales"] = np.round(smoothed, 2)

        # --- Step 4: STL Decomposition (if enough data) ---
        if len(product_df) >= 28:
            try:
                stl = STL(pd.Series(smoothed), period=7, robust=True)
                result = stl.fit()
                product_df["trend"] = np.round(result.trend, 2)
                product_df["seasonal"] = np.round(result.seasonal, 2)
                product_df["residual"] = np.round(result.resid, 2)
            except Exception:
                product_df["trend"] = smoothed
                product_df["seasonal"] = 0.0
                product_df["residual"] = 0.0
        else:
            product_df["trend"] = smoothed
            product_df["seasonal"] = 0.0
            product_df["residual"] = 0.0

        report[pid] = {
            "outliers_clipped": int(outlier_mask.sum()),
            "original_mean": round(float(mean), 2),
            "smoothed_mean": round(float(np.mean(smoothed)), 2),
            "noise_reduction_pct": round(
                100 * (1 - np.std(smoothed) / (np.std(series) + 1e-9)), 1
            ),
        }

        filtered_frames.append(product_df)

    result_df = pd.concat(filtered_frames, ignore_index=True)
    return result_df, report
