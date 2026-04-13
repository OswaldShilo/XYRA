"""
FLUX — Layer 6: Output & Recommendations
Generate dashboard, briefing, and recommendation API responses
"""

import pandas as pd
import base64
from typing import Dict, List, Any
from datetime import datetime
import json


def generate_dashboard(classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate structured JSON dashboard with all product risk classifications.
    
    Returns: {
        'generated_at': timestamp,
        'total_products': int,
        'critical_count': int,
        'warning_count': int,
        'safe_count': int,
        'products': [classifications sorted by priority],
    }
    """
    if not classifications:
        return {
            'generated_at': datetime.now().isoformat(),
            'total_products': 0,
            'critical_count': 0,
            'warning_count': 0,
            'safe_count': 0,
            'products': [],
        }

    critical = [c for c in classifications if c['priority'] == 1]
    warning = [c for c in classifications if c['priority'] == 2]
    safe = [c for c in classifications if c['priority'] == 3]

    return {
        'generated_at': datetime.now().isoformat(),
        'total_products': len(classifications),
        'critical_count': len(critical),
        'warning_count': len(warning),
        'safe_count': len(safe),
        'products': classifications,
    }


def get_top_recommendations(classifications: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Extract top N reorder recommendations sorted by urgency.
    
    Returns: List of recommendation dicts with action items
    """
    recommendations = []

    for idx, classified in enumerate(classifications[:limit], 1):
        recommendation = {
            'rank': idx,
            'product_id': classified['product_id'],
            'category': classified['category'],
            'action': f"REORDER {classified['reorder_qty']} units by {classified['reorder_by_date']}",
            'urgency': classified['risk_level'],
            'current_stock': classified['current_stock'],
            'reorder_qty': classified['reorder_qty'],
            'reorder_by_date': classified['reorder_by_date'],
            'reason': classified['reason'],
            'forecast_7d_avg': classified['forecast_7d_avg'],
        }
        recommendations.append(recommendation)

    return recommendations


def generate_briefing(
    classifications: List[Dict[str, Any]],
    event_briefing: str = "",
    weather_briefing: str = "",
) -> str:
    """
    Generate plain-text weekly manager briefing.
    
    Example: "FLASK SUMMARY: 3 CRITICAL products need immediate reorder by Wed.
             Pongal spike expected — grains up 60%. Rain forecast reduces footfall.
             Top action: Reorder 200 units of Product X by 2026-04-16."
    """
    critical = [c for c in classifications if c['priority'] == 1]
    warning = [c for c in classifications if c['priority'] == 2]

    lines = []
    lines.append("=" * 70)
    lines.append("FLUX — Weekly Supply Chain Briefing")
    lines.append(f"Generated: {datetime.now().strftime('%A, %Y-%m-%d %H:%M')}")
    lines.append("=" * 70)
    lines.append("")

    # Summary
    lines.append(f"STATUS: {len(critical)} CRITICAL | {len(warning)} WARNING | {len([c for c in classifications if c['priority'] == 3])} SAFE")
    lines.append("")

    # Critical actions
    if critical:
        lines.append("🔴 IMMEDIATE ACTIONS (Critical):")
        for c in critical[:3]:
            lines.append(f"  • {c['product_id']}: Reorder {c['reorder_qty']} units by {c['reorder_by_date']}")
            lines.append(f"    Current stock: {c['current_stock']} units | Days to stockout: {c['days_to_stockout']}")
            lines.append(f"    Reason: {c['reason']}")
        lines.append("")

    # Event signals
    if event_briefing:
        lines.append("📅 EVENT SIGNALS:")
        lines.append(f"  {event_briefing}")
        lines.append("")

    # Weather signals
    if weather_briefing:
        lines.append("🌤️ WEATHER SIGNALS:")
        lines.append(f"  {weather_briefing}")
        lines.append("")

    # Warning items
    if warning:
        lines.append("🟡 WATCH LIST (Warning):")
        for w in warning[:5]:
            lines.append(f"  • {w['product_id']}: Monitor closely | Days to stockout: {w['days_to_stockout']}")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)


def generate_chart_png(classifications: List[Dict[str, Any]]) -> str:
    """
    Generate a risk heatmap as base64-encoded PNG.
    
    For MVP: Return placeholder. In production: Use matplotlib/plotly.
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # Simple bar chart: product_id vs days_to_stockout
        fig, ax = plt.subplots(figsize=(10, 6))

        products = [c['product_id'][:10] for c in classifications[:10]]
        days = [c['days_to_stockout'] for c in classifications[:10]]
        colors = ['red' if c['priority'] == 1 else 'orange' if c['priority'] == 2 else 'green' for c in classifications[:10]]

        ax.barh(products, days, color=colors, alpha=0.7)
        ax.axvline(x=3, color='red', linestyle='--', label='Critical (3 days)')
        ax.axvline(x=7, color='orange', linestyle='--', label='Warning (7 days)')
        ax.set_xlabel('Days to Stockout')
        ax.set_title('FLUX Risk Dashboard')
        ax.legend()

        # Convert to base64
        from io import BytesIO
        buffer = BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    except Exception as e:
        # Return placeholder on error
        return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNmMGYwZjAiLz48dGV4dCB4PSI1MCIgeT0iNTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkNoYXJ0PC90ZXh0Pjwvc3ZnPg=="
