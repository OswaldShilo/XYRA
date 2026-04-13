"""
FLUX — Layer 7: Continuous Learning
Feedback loop that records manager decisions and recalibrates spike multipliers
"""

import json
import os
from datetime import date, datetime
from typing import Dict, List, Optional
from collections import defaultdict


FEEDBACK_LOG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "feedback_log.json"
)
MULTIPLIER_CACHE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "learned_multipliers.json"
)


# ── Persistence helpers ────────────────────────────────────────────────────────

def _load_json(path: str, default) -> any:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def _save_json(path: str, data: any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Core feedback functions ────────────────────────────────────────────────────

def record_feedback(
    product_id: str,
    recommendation_id: str,
    accepted: bool,
    recommended_qty: int,
    actual_qty_ordered: Optional[int] = None,
    category: str = "general",
    manager_note: str = "",
) -> Dict:
    """
    Store one feedback entry. Called from POST /feedback endpoint.
    """
    log = _load_json(FEEDBACK_LOG_PATH, [])

    entry = {
        "id": f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{product_id}",
        "product_id": product_id,
        "recommendation_id": recommendation_id,
        "category": category,
        "accepted": accepted,
        "recommended_qty": recommended_qty,
        "actual_qty_ordered": actual_qty_ordered if actual_qty_ordered is not None else recommended_qty,
        "manager_note": manager_note,
        "timestamp": str(datetime.now()),
        "date": str(date.today()),
    }

    log.append(entry)
    _save_json(FEEDBACK_LOG_PATH, log)

    # Trigger recalibration after every 10 feedback entries
    if len(log) % 10 == 0:
        recalibrate_multipliers()

    return {"status": "recorded", "entry_id": entry["id"]}


def recalibrate_multipliers() -> Dict:
    """
    Analyzes feedback log and adjusts quantity multipliers per category.
    Logic: if we consistently under-order (actual > recommended), bump multiplier up.
           if we consistently over-order (actual < recommended), bring it down.
    """
    log = _load_json(FEEDBACK_LOG_PATH, [])
    if len(log) < 5:
        return {"status": "insufficient_data", "entries": len(log)}

    # Group by category
    category_data: Dict[str, List[float]] = defaultdict(list)

    for entry in log:
        if not entry.get("accepted", True):
            continue  # Rejected recommendations skew data — skip
        rec = entry.get("recommended_qty", 0)
        actual = entry.get("actual_qty_ordered", rec)
        if rec > 0:
            ratio = actual / rec  # >1 = we under-recommended; <1 = over-recommended
            category_data[entry.get("category", "general")].append(ratio)

    # Compute adjustment per category
    learned = _load_json(MULTIPLIER_CACHE_PATH, {})
    adjustments = {}

    for category, ratios in category_data.items():
        if len(ratios) < 3:
            continue
        avg_ratio = sum(ratios) / len(ratios)
        # Smooth adjustment: don't overcorrect — blend 30% new signal with 70% existing
        current = learned.get(category, 1.0)
        new_multiplier = round(current * 0.7 + avg_ratio * 0.3, 3)
        # Clamp to reasonable bounds
        new_multiplier = max(0.5, min(new_multiplier, 2.5))
        learned[category] = new_multiplier
        adjustments[category] = {
            "previous": current,
            "new": new_multiplier,
            "based_on": len(ratios),
        }

    _save_json(MULTIPLIER_CACHE_PATH, learned)
    return {"status": "recalibrated", "adjustments": adjustments}


def get_learned_multipliers() -> Dict[str, float]:
    """Returns current learned multipliers per category."""
    return _load_json(MULTIPLIER_CACHE_PATH, {})


def get_learning_stats() -> Dict:
    """Returns accuracy stats and feedback history summary."""
    log = _load_json(FEEDBACK_LOG_PATH, [])
    learned = _load_json(MULTIPLIER_CACHE_PATH, {})

    if not log:
        return {
            "total_feedback_entries": 0,
            "acceptance_rate": None,
            "learned_multipliers": learned,
            "status": "No feedback recorded yet",
        }

    total = len(log)
    accepted = sum(1 for e in log if e.get("accepted", False))
    acceptance_rate = round(accepted / total * 100, 1)

    # Accuracy per category
    category_accuracy = defaultdict(list)
    for entry in log:
        rec = entry.get("recommended_qty", 0)
        actual = entry.get("actual_qty_ordered", rec)
        if rec > 0:
            pct_error = abs(actual - rec) / rec * 100
            category_accuracy[entry.get("category", "general")].append(pct_error)

    accuracy_report = {
        cat: {"avg_error_pct": round(sum(errors)/len(errors), 1), "samples": len(errors)}
        for cat, errors in category_accuracy.items()
    }

    return {
        "total_feedback_entries": total,
        "acceptance_rate_pct": acceptance_rate,
        "learned_multipliers": learned,
        "category_accuracy": accuracy_report,
        "last_recalibration": log[-1].get("date") if log else None,
    }
