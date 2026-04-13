"""
FLUX — Layer 6: Output & Recommendations
Generates final risk dashboard, top reorder actions, and plain-text briefing
"""

from typing import List, Dict
from datetime import date


def generate_dashboard(classified_products: List[Dict]) -> Dict:
    """
    Structures the full product risk dashboard response.
    """
    critical = [p for p in classified_products if p["risk_level"] == "CRITICAL"]
    warning  = [p for p in classified_products if p["risk_level"] == "WARNING"]
    safe     = [p for p in classified_products if p["risk_level"] == "SAFE"]

    return {
        "generated_at": str(date.today()),
        "summary": {
            "total_products": len(classified_products),
            "critical_count": len(critical),
            "warning_count": len(warning),
            "safe_count": len(safe),
            "action_required": len(critical) + len(warning),
        },
        "critical": critical,
        "warning": warning,
        "safe": safe,
    }


def get_top_recommendations(classified_products: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    Returns top N urgent reorder actions with plain-English reasons.
    """
    urgent = [p for p in classified_products if p["risk_level"] in ("CRITICAL", "WARNING")]
    top = urgent[:top_n]

    recommendations = []
    for p in top:
        reason = _build_reason(p)
        recommendations.append({
            "product_id": p["product_id"],
            "product_name": p["product_name"],
            "risk_emoji": p["risk_emoji"],
            "reorder_qty": p["reorder_qty"],
            "reorder_by_date": p["reorder_by_date"],
            "days_to_stockout": p["days_to_stockout"],
            "reason": reason,
            "action": f"Order {p['reorder_qty']} units of {p['product_name']} by {p['reorder_by_date']}",
        })

    return recommendations


def generate_briefing(
    classified_products: List[Dict],
    active_events: List[str],
    weather_condition: str,
    store_name: str = "your store",
) -> str:
    """
    Generates a plain-English weekly manager briefing paragraph.
    """
    critical = [p for p in classified_products if p["risk_level"] == "CRITICAL"]
    warning  = [p for p in classified_products if p["risk_level"] == "WARNING"]

    lines = []
    lines.append(f"📋 FLUX Weekly Briefing — {date.today().strftime('%d %B %Y')}")
    lines.append("")

    # Action summary
    if not critical and not warning:
        lines.append(f"✅ All products at {store_name} are well-stocked. No immediate reorders needed.")
    else:
        total_action = len(critical) + len(warning)
        lines.append(
            f"⚠️ {total_action} product(s) require attention at {store_name} this week."
        )

    # Critical products
    if critical:
        names = ", ".join(p["product_name"] for p in critical[:3])
        extra = f" and {len(critical)-3} more" if len(critical) > 3 else ""
        lines.append(
            f"🔴 URGENT: {names}{extra} will stock out within 3 days — reorder immediately."
        )

    # Warning products
    if warning:
        names = ", ".join(p["product_name"] for p in warning[:3])
        lines.append(
            f"🟡 WATCH: {names} need restocking within the week."
        )

    # Event context
    if active_events:
        events_str = ", ".join(active_events[:3])
        lines.append(
            f"📅 Upcoming events detected: {events_str}. "
            f"Expect higher-than-normal demand — reorder quantities have been adjusted upward."
        )

    # Weather context
    weather_messages = {
        "heatwave":   "🌡️ Heatwave forecast — boost cold drinks, ORS, and beverages stock.",
        "rain_heavy": "🌧️ Heavy rain expected — footfall may drop 20%. Avoid over-ordering perishables.",
        "rain_light": "🌦️ Light rain in the forecast — minor impact on footfall expected.",
        "cold":       "🧣 Cold weather ahead — stock up on hot beverages and soups.",
        "hot":        "☀️ Hot weather — cold drinks and beverages demand will be elevated.",
    }
    if weather_condition in weather_messages:
        lines.append(weather_messages[weather_condition])

    # Closing
    lines.append("")
    lines.append("— FLUX AI · Predict the rush. Never run out.")

    return "\n".join(lines)


def _build_reason(p: Dict) -> str:
    days = p["days_to_stockout"]
    mult = p["effective_multiplier"]
    spike_note = f" (demand spike of {round((mult-1)*100)}% detected)" if mult > 1.15 else ""
    peak = f" Peak demand expected on {p['peak_demand_day']}." if p.get("peak_demand_day") else ""

    if p["risk_level"] == "CRITICAL":
        return f"Only {days} days of stock remaining at current sales velocity.{spike_note}{peak} Immediate reorder required."
    else:
        return f"{days} days of stock remaining.{spike_note}{peak} Reorder this week to avoid stockout."
