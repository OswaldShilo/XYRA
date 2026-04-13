"""
FLUX — Layer 5: Weather Signals
Fetches 7-day weather forecast and returns demand adjustment multipliers
Uses OpenWeatherMap free tier (1000 calls/day)
"""

import os
import requests
from typing import Dict, Optional


OWM_BASE = "https://api.openweathermap.org/data/2.5"
API_KEY = os.getenv("OPENWEATHER_API_KEY", "")


# Demand multiplier rules based on weather conditions
WEATHER_RULES = {
    "rain_heavy": {   # rain > 10mm
        "all_categories": 0.80,         # footfall drops 20%
        "hot_beverages": 1.4,
        "umbrellas": 3.0,
    },
    "rain_light": {   # rain 2–10mm
        "all_categories": 0.90,
        "hot_beverages": 1.2,
    },
    "heatwave": {     # temp > 38°C
        "cold_drinks": 2.2,
        "ors": 1.9,
        "ice_cream": 1.8,
        "beverages": 1.6,
        "dairy": 0.9,           # milk spoils faster — less bulk buying
    },
    "hot": {          # temp 33–38°C
        "cold_drinks": 1.5,
        "beverages": 1.3,
        "ice_cream": 1.4,
    },
    "cold": {         # temp < 18°C
        "hot_beverages": 1.6,
        "soups": 1.4,
        "dairy": 1.2,
        "cold_drinks": 0.7,
    },
}

# OpenWeatherMap weather condition code → our internal label
def _classify_weather(temp_c: float, rain_mm: float, condition_id: int) -> str:
    if rain_mm > 10:
        return "rain_heavy"
    if rain_mm > 2:
        return "rain_light"
    if temp_c > 38:
        return "heatwave"
    if temp_c > 33:
        return "hot"
    if temp_c < 18:
        return "cold"
    return "normal"


def _get_lat_lon_from_pincode(pincode: str) -> Optional[Dict]:
    """Use OWM geocoding to convert pincode to lat/lon."""
    try:
        url = f"http://api.openweathermap.org/geo/1.0/zip?zip={pincode},IN&appid={API_KEY}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {"lat": data["lat"], "lon": data["lon"], "city": data.get("name", "")}
    except Exception:
        pass
    return None


def get_weather_multipliers(pincode: str) -> Dict:
    """
    Fetch 7-day weather forecast for pincode and return demand multipliers.
    Falls back to neutral multipliers if API is unavailable or key is missing.
    """
    if not API_KEY:
        return _neutral_response(pincode, reason="No API key configured")

    geo = _get_lat_lon_from_pincode(pincode)
    if not geo:
        return _neutral_response(pincode, reason="Could not geocode pincode")

    try:
        url = (
            f"{OWM_BASE}/forecast"
            f"?lat={geo['lat']}&lon={geo['lon']}"
            f"&appid={API_KEY}&units=metric&cnt=16"  # ~5 days, 3-hour intervals
        )
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return _neutral_response(pincode, reason=f"API error: {e}")

    # Aggregate weather signals across forecast window
    max_temp = -99
    total_rain = 0.0
    dominant_condition = "normal"

    for item in data.get("list", []):
        temp = item["main"]["temp"]
        rain = item.get("rain", {}).get("3h", 0)
        max_temp = max(max_temp, temp)
        total_rain += rain

    if max_temp == -99:
        return _neutral_response(pincode, reason="No forecast data returned")

    avg_rain_per_day = total_rain / max(len(data.get("list", [1])), 1) * 8  # convert 3h to daily
    dominant_condition = _classify_weather(max_temp, avg_rain_per_day, 0)

    multipliers = WEATHER_RULES.get(dominant_condition, {})

    return {
        "pincode": pincode,
        "city": geo.get("city", ""),
        "condition": dominant_condition,
        "max_temp_c": round(max_temp, 1),
        "expected_rain_mm_per_day": round(avg_rain_per_day, 1),
        "multipliers": multipliers,
        "source": "OpenWeatherMap",
    }


def _neutral_response(pincode: str, reason: str = "") -> Dict:
    return {
        "pincode": pincode,
        "condition": "normal",
        "max_temp_c": None,
        "expected_rain_mm_per_day": None,
        "multipliers": {},
        "source": "fallback",
        "note": reason,
    }
