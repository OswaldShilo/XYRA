"""
FLUX — Layer 4: Event Signals
Maps store pincode → state → upcoming festivals → category spike multipliers
"""

import json
from datetime import date, timedelta
from typing import Dict, List


# Indian festival calendar with category multipliers
FESTIVAL_CALENDAR: List[Dict] = [
    {"name": "Pongal",             "date": "2026-01-14", "state": "TN",       "window": 4,
     "multipliers": {"grains": 1.6, "sweets": 2.1, "beverages": 1.3, "dairy": 1.4}},
    {"name": "Republic Day",       "date": "2026-01-26", "state": "ALL",      "window": 2,
     "multipliers": {"snacks": 1.3, "beverages": 1.2}},
    {"name": "Holi",               "date": "2026-03-22", "state": "NORTH",    "window": 3,
     "multipliers": {"sweets": 1.9, "beverages": 1.5, "dairy": 1.3, "colors": 3.0}},
    {"name": "Ugadi",              "date": "2026-03-19", "state": "AP,KA,TS", "window": 3,
     "multipliers": {"grains": 1.5, "sweets": 1.8, "fruits": 1.7}},
    {"name": "IPL Season",         "date": "2026-03-22", "state": "ALL",      "window": 60,
     "multipliers": {"beverages": 1.8, "snacks": 1.9, "dairy": 1.1}},
    {"name": "Ramzan / Eid",       "date": "2026-03-30", "state": "ALL",      "window": 5,
     "multipliers": {"sweets": 2.0, "grains": 1.5, "dairy": 1.4, "meat": 2.5}},
    {"name": "Tamil New Year",     "date": "2026-04-14", "state": "TN",       "window": 3,
     "multipliers": {"grains": 1.5, "sweets": 1.8, "fruits": 1.6}},
    {"name": "Independence Day",   "date": "2026-08-15", "state": "ALL",      "window": 2,
     "multipliers": {"snacks": 1.3, "beverages": 1.4}},
    {"name": "Onam",               "date": "2026-09-07", "state": "KL",       "window": 7,
     "multipliers": {"grains": 1.8, "sweets": 2.0, "fruits": 1.9, "vegetables": 1.6}},
    {"name": "Navratri",           "date": "2026-10-08", "state": "ALL",      "window": 9,
     "multipliers": {"sweets": 1.8, "dairy": 1.5, "fruits": 1.4}},
    {"name": "Dussehra",           "date": "2026-10-17", "state": "ALL",      "window": 3,
     "multipliers": {"sweets": 1.7, "snacks": 1.5}},
    {"name": "Diwali",             "date": "2026-11-08", "state": "ALL",      "window": 5,
     "multipliers": {"sweets": 2.5, "oil": 1.7, "snacks": 1.8, "beverages": 1.5, "dairy": 1.4}},
    {"name": "Christmas",          "date": "2026-12-25", "state": "ALL",      "window": 3,
     "multipliers": {"sweets": 1.7, "beverages": 1.5, "snacks": 1.4}},
    {"name": "New Year Eve",       "date": "2026-12-31", "state": "ALL",      "window": 2,
     "multipliers": {"beverages": 2.0, "snacks": 1.8}},
]

# Pincode prefix → state code
PINCODE_STATE_MAP = {
    "6": "TN",    # Tamil Nadu (600xxx, 620xxx, etc.)
    "5": "AP",    # Andhra/Telangana
    "56": "KA",   # Karnataka
    "68": "KL",   # Kerala
    "69": "KL",
    "1": "NORTH", # Delhi / UP / Haryana
    "2": "NORTH",
    "3": "NORTH", # Rajasthan
    "4": "WEST",  # Maharashtra / Gujarat
    "7": "EAST",  # West Bengal / Odisha
    "8": "EAST",
}


def get_state_from_pincode(pincode: str) -> str:
    pincode = str(pincode).strip()
    # Try 2-char prefix first, then 1-char
    two = PINCODE_STATE_MAP.get(pincode[:2])
    if two:
        return two
    one = PINCODE_STATE_MAP.get(pincode[:1])
    return one or "ALL"


def get_event_multipliers(
    pincode: str,
    lookahead_days: int = 14,
    today: date = None,
) -> Dict:
    """
    Returns category multipliers for events happening within lookahead_days.
    Multiple overlapping events are combined by taking the max per category.
    """
    today = today or date.today()
    state = get_state_from_pincode(pincode)
    window_end = today + timedelta(days=lookahead_days)

    combined_multipliers: Dict[str, float] = {}
    active_events: List[str] = []

    for event in FESTIVAL_CALENDAR:
        event_date = date.fromisoformat(event["date"])
        event_start = event_date - timedelta(days=2)
        event_end = event_date + timedelta(days=event.get("window", 2))

        # Check if event falls in our lookahead window
        if event_start > window_end or event_end < today:
            continue

        # Check if event is relevant to this store's state
        relevant_states = event["state"].split(",")
        if "ALL" not in relevant_states and state not in relevant_states:
            continue

        active_events.append(event["name"])

        for category, multiplier in event["multipliers"].items():
            combined_multipliers[category] = max(
                combined_multipliers.get(category, 1.0),
                multiplier,
            )

    return {
        "pincode": pincode,
        "state": state,
        "active_events": active_events,
        "multipliers": combined_multipliers,
        "lookahead_days": lookahead_days,
    }
