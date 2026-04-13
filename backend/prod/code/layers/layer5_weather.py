"""
FLUX — Layer 5: Weather Signals
Get weather data and output demand multipliers by category
"""

import os
from typing import Dict, Any
from datetime import datetime


def get_weather_multipliers(pincode: str) -> Dict[str, Any]:
    """
    Get 7-day weather forecast and output demand multipliers.
    
    For MVP: Return synthetic weather data (no API calls).
    In production: Integrate OpenWeatherMap API.
    
    Input: pincode
    Output: {
        'weather': [list of daily conditions],
        'multipliers': {category: multiplier},
    }
    """
    # For MVP, return deterministic weather based on pincode hash
    # In production, call OpenWeatherMap API
    
    api_key = os.getenv("OPENWEATHER_API_KEY", "demo")
    
    if api_key == "demo":
        # Synthetic weather data for demo
        weather_data = _get_synthetic_weather(pincode)
    else:
        # Would call actual API here
        weather_data = _get_synthetic_weather(pincode)

    # Calculate category multipliers based on weather
    category_multipliers = _calculate_weather_multipliers(weather_data)

    return {
        "pincode": pincode,
        "weather": weather_data,
        "multipliers": category_multipliers,
    }


def _get_synthetic_weather(pincode: str) -> list:
    """Generate synthetic weather for demo."""
    # Simple: based on pincode hash
    import hashlib
    hash_val = int(hashlib.md5(pincode.encode()).hexdigest(), 16)
    
    weather_conditions = ["Sunny", "Cloudy", "Rainy", "Hot", "Cool"]
    temps = [28, 32, 25, 38, 18]  # Celsius
    
    forecast = []
    for day in range(7):
        idx = (hash_val + day) % len(weather_conditions)
        forecast.append({
            "date": f"2026-04-{13+day}",
            "condition": weather_conditions[idx],
            "temp": temps[idx % len(temps)],
        })
    
    return forecast


def _calculate_weather_multipliers(weather_data: list) -> Dict[str, float]:
    """Convert weather data to demand multipliers."""
    multipliers = {}

    for day in weather_data:
        condition = day.get("condition", "")
        temp = day.get("temp", 28)

        # Rain reduces footfall
        if "rainy" in condition.lower():
            multipliers["general"] = multipliers.get("general", 1.0) * 0.85

        # Hot weather increases cold beverages
        if temp > 35:
            multipliers["beverages"] = multipliers.get("beverages", 1.0) * 1.6
            multipliers["cold_drinks"] = multipliers.get("cold_drinks", 1.0) * 2.0
            multipliers["ice_cream"] = multipliers.get("ice_cream", 1.0) * 1.8
            multipliers["dairy"] = multipliers.get("dairy", 1.0) * 0.9

        # Cold weather increases hot beverages
        if temp < 15:
            multipliers["beverages"] = multipliers.get("beverages", 1.0) * 1.3
            multipliers["hot_drinks"] = multipliers.get("hot_drinks", 1.0) * 1.6

    # Average multipliers across week
    for cat in multipliers:
        multipliers[cat] = multipliers[cat] ** (1/7)  # Geometric mean

    return multipliers


def get_weather_briefing(weather_data: list) -> str:
    """Generate briefing text for weather."""
    if not weather_data:
        return "Weather data unavailable."

    first = weather_data[0]
    condition = first.get("condition", "Unknown")
    temp = first.get("temp", "N/A")
    
    return f"Weather outlook: {condition}, ~{temp}°C — adjust cold/hot item demand accordingly."
