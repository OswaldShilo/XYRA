"""
FLUX — Layer 2: Demand Forecasting (Prophet-based)
Per-SKU 7-day and 30-day forecast with confidence intervals
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

try:
    from prophet import Prophet
except ImportError:
    Prophet = None


def forecast_all(df: pd.DataFrame, forecast_days: int = 30) -> Dict[str, Dict[str, Any]]:
    """
    Forecast demand for all products using Prophet or fallback method.
    
    Returns: {
        product_id: {
            'forecast_7d': [list of forecasts],
            'forecast_30d': [list of forecasts],
            'confidence_lower': [...],
            'confidence_upper': [...],
            'last_date': datetime,
            'spike_score': float,
        }
    }
    """
    forecasts = {}

    if df.empty:
        return forecasts

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    for product_id in df['product_id'].unique():
        product_ts = df[df['product_id'] == product_id].groupby('date')['units_sold'].sum().reset_index()
        product_ts.columns = ['ds', 'y']
        product_ts = product_ts.sort_values('ds').reset_index(drop=True)

        if len(product_ts) < 14:  # Not enough data
            forecasts[product_id] = {
                'forecast_7d': [product_ts['y'].mean()] * 7,
                'forecast_30d': [product_ts['y'].mean()] * 30,
                'confidence_lower': [product_ts['y'].min()] * 30,
                'confidence_upper': [product_ts['y'].max()] * 30,
                'last_date': product_ts['ds'].max(),
                'spike_score': 1.0,
                'method': 'fallback_small_data',
            }
            continue

        try:
            if Prophet is None:
                # Fallback: simple moving average
                forecasts[product_id] = _forecast_fallback(product_ts)
            else:
                # Use Prophet
                forecasts[product_id] = _forecast_prophet(product_ts, forecast_days)
        except Exception as e:
            # Fallback on error
            forecasts[product_id] = _forecast_fallback(product_ts)

    return forecasts


def _forecast_prophet(product_ts: pd.DataFrame, forecast_days: int = 30) -> Dict[str, Any]:
    """Use Prophet for forecasting."""
    try:
        model = Prophet(
            yearly_seasonality=False,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.80,  # 80% confidence interval
            changepoint_prior_scale=0.05,
        )
        model.fit(product_ts)

        # Create future dataframe
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        # Filter to future only
        future_forecast = forecast[forecast['ds'] > product_ts['ds'].max()].reset_index(drop=True)

        last_actual = product_ts['y'].iloc[-7:].mean()  # 7-day avg
        future_avg = future_forecast['yhat'].mean()
        spike_score = future_avg / last_actual if last_actual > 0 else 1.0

        return {
            'forecast_7d': future_forecast['yhat'].head(7).tolist(),
            'forecast_30d': future_forecast['yhat'].head(30).tolist(),
            'confidence_lower': future_forecast['yhat_lower'].head(30).tolist(),
            'confidence_upper': future_forecast['yhat_upper'].head(30).tolist(),
            'last_date': product_ts['ds'].max(),
            'spike_score': spike_score,
            'method': 'prophet',
        }
    except Exception as e:
        return _forecast_fallback(product_ts)


def _forecast_fallback(product_ts: pd.DataFrame) -> Dict[str, Any]:
    """Fallback: exponential smoothing via simple MA."""
    ts_values = product_ts['y'].values

    # Simple exponential moving average
    alpha = 0.3
    ema = np.zeros(len(ts_values) + 30)
    ema[0] = ts_values[0]

    for i in range(1, len(ts_values)):
        ema[i] = alpha * ts_values[i] + (1 - alpha) * ema[i - 1]

    last_ema = ema[len(ts_values) - 1]

    # Forecast next 30 days (slowly converging to mean)
    forecast_values = []
    current_forecast = last_ema
    mean_val = ts_values.mean()

    for i in range(30):
        forecast_values.append(max(0, current_forecast))
        current_forecast = 0.7 * current_forecast + 0.3 * mean_val

    # Confidence intervals (rough estimate)
    std_dev = ts_values.std()
    lower_bound = [max(0, v - 1.28 * std_dev) for v in forecast_values]
    upper_bound = [v + 1.28 * std_dev for v in forecast_values]

    last_actual = ts_values[-7:].mean()
    spike_score = np.mean(forecast_values) / last_actual if last_actual > 0 else 1.0

    return {
        'forecast_7d': forecast_values[:7],
        'forecast_30d': forecast_values,
        'confidence_lower': lower_bound,
        'confidence_upper': upper_bound,
        'last_date': product_ts['ds'].max(),
        'spike_score': spike_score,
        'method': 'fallback_ema',
    }


def calculate_days_to_stockout(current_stock: float, daily_forecast: float) -> float:
    """Calculate days until stockout at current forecast rate."""
    if daily_forecast <= 0:
        return float('inf')
    return current_stock / daily_forecast
