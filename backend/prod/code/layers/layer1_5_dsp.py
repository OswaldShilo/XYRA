"""
FLUX — Layer 1.5: DSP Noise Filtering & Decomposition
Rolling smoothing, IQR/z-score outlier removal, STL decomposition
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
from scipy import stats


def filter_noise(df: pd.DataFrame, window: int = 7, z_threshold: float = 3.0, iqr_multiplier: float = 1.5) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter noise from time series per product.
    
    Operations:
    - Rolling smoothing (7-day window)
    - IQR-based outlier detection and clipping
    - Z-score filtering
    - Basic trend extraction
    
    Returns: (filtered_df, dsp_report)
    """
    report = {
        "products_filtered": 0,
        "outliers_clipped": 0,
        "z_score_anomalies": 0,
        "smoothing_window": window,
    }

    if df.empty or 'units_sold' not in df.columns:
        return df, report

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    filtered_records = []

    # Per-product filtering
    for product_id in df['product_id'].unique():
        product_df = df[df['product_id'] == product_id].sort_values('date').reset_index(drop=True)
        
        if len(product_df) < 3:
            filtered_records.extend(product_df.to_dict('records'))
            continue

        report["products_filtered"] += 1

        # Extract time series
        ts = product_df['units_sold'].values.astype(float)

        # 1. Rolling average smoothing
        if len(ts) >= window:
            rolling_avg = pd.Series(ts).rolling(window=window, center=True, min_periods=1).mean().values
        else:
            rolling_avg = ts

        # 2. IQR-based outlier clipping
        Q1 = np.percentile(ts, 25)
        Q3 = np.percentile(ts, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - iqr_multiplier * IQR
        upper_bound = Q3 + iqr_multiplier * IQR

        ts_clipped = np.clip(ts, lower_bound, upper_bound)
        report["outliers_clipped"] += np.sum(ts != ts_clipped)

        # 3. Z-score filtering
        z_scores = np.abs(stats.zscore(ts_clipped, nan_policy='omit'))
        z_anomalies = z_scores > z_threshold
        report["z_score_anomalies"] += z_anomalies.sum()

        # Apply smoothing to anomalies
        ts_filtered = ts_clipped.copy()
        for i, is_anomaly in enumerate(z_anomalies):
            if is_anomaly and i > 0:
                ts_filtered[i] = rolling_avg[i]

        # Update dataframe
        product_df['units_sold'] = ts_filtered
        product_df['smoothed_sales'] = rolling_avg
        
        # Calculate residuals (noise component)
        product_df['residual'] = ts_filtered - rolling_avg

        filtered_records.extend(product_df.to_dict('records'))

    filtered_df = pd.DataFrame(filtered_records).sort_values('date').reset_index(drop=True)
    return filtered_df, report


def extract_trend(series: np.ndarray, window: int = 14) -> np.ndarray:
    """Extract trend from series using rolling average."""
    if len(series) < window:
        return series
    return pd.Series(series).rolling(window=window, center=True, min_periods=1).mean().values


def simple_decompose(df: pd.DataFrame) -> pd.DataFrame:
    """
    Simple STL-like decomposition: trend + seasonal
    For MVP, we'll use rolling average for trend and residual for seasonality
    """
    if df.empty or 'product_id' not in df.columns or 'units_sold' not in df.columns:
        return df
    
    df = df.copy()
    df['trend'] = 0.0
    df['seasonal'] = 0.0
    
    for product_id in df['product_id'].unique():
        product_mask = df['product_id'] == product_id
        product_data = df[product_mask]['units_sold'].values
        
        if len(product_data) >= 28:
            # Trend (28-day moving average)
            trend = extract_trend(product_data, window=28)
            df.loc[product_mask, 'trend'] = trend
            
            # Seasonal = actual - trend
            df.loc[product_mask, 'seasonal'] = product_data - trend
        else:
            df.loc[product_mask, 'trend'] = product_data
            df.loc[product_mask, 'seasonal'] = 0.0
    
    return df
