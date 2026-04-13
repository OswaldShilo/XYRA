"""
FLUX — Layer 4: Event Signals
Detect upcoming Indian festivals and events, output demand multipliers by category
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any


# Hardcoded Indian festival calendar (simplified for MVP)
INDIAN_FESTIVALS = {
    "Pongal": {
        "months": [1],
        "days": [14, 15],
        "regions": ["South"],
        "multipliers": {
            "grains": 1.6,
            "sweets": 2.1,
            "oil": 1.4,
            "dairy": 1.2,
            "beverages": 1.3,
        }
    },
    "Holi": {
        "months": [3],
        "days": [25, 26],  # Approximate
        "regions": ["North", "East", "West"],
        "multipliers": {
            "sweets": 2.0,
            "snacks": 1.8,
            "colors": 2.5,
            "dairy": 1.3,
            "beverages": 1.4,
        }
    },
    "Diwali": {
        "months": [10, 11],
        "days": [1, 2, 3],  # Approximate
        "regions": ["North", "East", "West", "South"],
        "multipliers": {
            "sweets": 2.5,
            "snacks": 1.9,
            "oil": 1.7,
            "grains": 1.4,
            "dairy": 1.2,
            "decorations": 2.0,
        }
    },
    "Eid": {
        "months": [4, 5],  # Approximate
        "days": [10, 11],
        "regions": ["North", "East", "West"],
        "multipliers": {
            "meat": 2.0,
            "grains": 1.5,
            "sweets": 1.8,
            "dairy": 1.3,
            "beverages": 1.4,
        }
    },
    "IPL_Cricket": {
        "months": [3, 4, 5],
        "days": list(range(1, 31)),  # Entire month
        "regions": ["North", "South", "East", "West"],
        "multipliers": {
            "beverages": 1.8,
            "snacks": 1.9,
            "dairy": 1.1,
            "frozen_food": 1.5,
        }
    },
}

# Pincode to state/region mapping (simplified)
PINCODE_REGION_MAP = {
    "600": "South",  # Chennai
    "500": "South",  # Hyderabad
    "560": "South",  # Bangalore
    "411": "West",   # Pune
    "400": "West",   # Mumbai
    "380": "West",   # Ahmedabad
    "110": "North",  # Delhi
    "140": "North",  # Punjab
    "141": "North",  # Punjab
    "700": "East",   # Kolkata
}


def get_event_multipliers(pincode: str, lookahead_days: int = 14) -> Dict[str, Any]:
    """
    Get upcoming events and their demand multipliers for a store.
    
    Input: pincode (string)
    Output: {
        'events': [list of upcoming events],
        'multipliers': {category: multiplier},
    }
    """
    # Determine region from pincode
    region = "North"  # Default
    for prefix, detected_region in PINCODE_REGION_MAP.items():
        if pincode.startswith(prefix):
            region = detected_region
            break

    upcoming_events = []
    category_multipliers = {}

    today = datetime.now()
    end_date = today + timedelta(days=lookahead_days)

    # Check each festival
    for festival_name, festival_data in INDIAN_FESTIVALS.items():
        if region not in festival_data.get("regions", []):
            continue

        # Check if festival is within lookahead window (naive check)
        for month in festival_data.get("months", []):
            for day in festival_data.get("days", []):
                try:
                    # Construct date (use current year, or next if passed)
                    current_year = today.year
                    festival_date = datetime(current_year, month, day)
                    
                    if festival_date < today:
                        continue  # Already passed
                    
                    if festival_date <= end_date:
                        upcoming_events.append({
                            "name": festival_name,
                            "date": festival_date.isoformat(),
                            "days_until": (festival_date - today).days,
                        })

                        # Merge multipliers
                        for cat, mult in festival_data.get("multipliers", {}).items():
                            category_multipliers[cat] = max(category_multipliers.get(cat, 1.0), mult)
                        break
                except ValueError:
                    continue

    return {
        "region": region,
        "pincode": pincode,
        "events": upcoming_events,
        "multipliers": category_multipliers,
    }


def get_event_briefing(events: list) -> str:
    """Generate briefing text for upcoming events."""
    if not events:
        return "No significant events upcoming."

    event_text = ", ".join([e["name"] for e in events[:3]])
    days_until = min([e["days_until"] for e in events])
    
    return f"Upcoming: {event_text} (within {days_until} days) — expect demand spike."
