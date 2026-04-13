"""
FLUX — Layer 7: Continuous Learning
Store feedback, calculate accuracy, and adjust multipliers
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict


FEEDBACK_LOG_PATH = "data/feedback_log.json"
LEARNED_MULTIPLIERS_PATH = "data/learned_multipliers.json"


def record_feedback(feedback_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record manager feedback on a recommendation.
    
    Payload: {
        'product_id': str,
        'recommendation_id': str,
        'accepted': bool,
        'actual_qty_ordered': int,
        'category': str,
        'manager_note': str,
    }
    
    Returns: {
        'status': 'recorded',
        'feedback_id': str,
        'message': str,
    }
    """
    # Load existing feedback
    feedback_log = _load_feedback_log()

    # Create feedback record
    feedback_id = f"FB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    feedback_record = {
        'feedback_id': feedback_id,
        'timestamp': datetime.now().isoformat(),
        **feedback_payload,
    }

    feedback_log.append(feedback_record)

    # Save
    _save_feedback_log(feedback_log)

    # Recalculate and update multipliers
    _recalculate_multipliers(feedback_log)

    return {
        'status': 'recorded',
        'feedback_id': feedback_id,
        'message': 'Feedback recorded successfully. Multipliers updated.',
    }


def get_learning_stats() -> Dict[str, Any]:
    """
    Get learning statistics: accuracy, feedback count, category performance.
    
    Returns: {
        'total_feedback': int,
        'acceptance_rate': float,
        'accuracy_by_category': {...},
        'learned_multipliers': {...},
    }
    """
    feedback_log = _load_feedback_log()

    if not feedback_log:
        return {
            'total_feedback': 0,
            'acceptance_rate': 0.0,
            'accuracy_by_category': {},
            'learned_multipliers': get_learned_multipliers(),
        }

    # Calculate acceptance rate
    accepted = sum(1 for fb in feedback_log if fb.get('accepted', False))
    acceptance_rate = accepted / len(feedback_log) if feedback_log else 0.0

    # Calculate accuracy by category
    accuracy_by_category = _calculate_category_accuracy(feedback_log)

    return {
        'total_feedback': len(feedback_log),
        'acceptance_rate': round(acceptance_rate, 3),
        'accuracy_by_category': accuracy_by_category,
        'learned_multipliers': get_learned_multipliers(),
        'last_update': datetime.now().isoformat(),
    }


def get_learned_multipliers() -> Dict[str, float]:
    """Load learned multipliers from file."""
    if not os.path.exists(LEARNED_MULTIPLIERS_PATH):
        return {}

    try:
        with open(LEARNED_MULTIPLIERS_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}


def _load_feedback_log() -> List[Dict[str, Any]]:
    """Load feedback log from file."""
    os.makedirs(os.path.dirname(FEEDBACK_LOG_PATH), exist_ok=True)

    if not os.path.exists(FEEDBACK_LOG_PATH):
        return []

    try:
        with open(FEEDBACK_LOG_PATH, 'r') as f:
            return json.load(f)
    except:
        return []


def _save_feedback_log(feedback_log: List[Dict[str, Any]]):
    """Save feedback log to file."""
    os.makedirs(os.path.dirname(FEEDBACK_LOG_PATH), exist_ok=True)

    with open(FEEDBACK_LOG_PATH, 'w') as f:
        json.dump(feedback_log, f, indent=2)


def _calculate_category_accuracy(feedback_log: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Calculate accuracy metrics per category."""
    by_category = defaultdict(lambda: {'accepted': 0, 'total': 0})

    for fb in feedback_log:
        category = fb.get('category', 'general')
        by_category[category]['total'] += 1
        if fb.get('accepted'):
            by_category[category]['accepted'] += 1

    result = {}
    for cat, stats in by_category.items():
        rate = stats['accepted'] / stats['total'] if stats['total'] > 0 else 0
        result[cat] = {
            'acceptance_rate': round(rate, 3),
            'total_recommendations': stats['total'],
            'accepted': stats['accepted'],
        }

    return result


def _recalculate_multipliers(feedback_log: List[Dict[str, Any]]):
    """
    Recalculate category multipliers based on feedback.
    
    Simple logic: If acceptance rate is high, slightly increase multiplier.
    If low, adjust downward.
    """
    accuracy = _calculate_category_accuracy(feedback_log)
    learned = get_learned_multipliers()

    for category, stats in accuracy.items():
        if stats['total_recommendations'] < 5:
            continue  # Not enough data

        current_mult = learned.get(category, 1.0)
        acceptance = stats['acceptance_rate']

        # Adjust multiplier based on acceptance
        if acceptance > 0.8:
            # Manager accepted more than 80% → our forecast is typically undershooting → increase slightly
            new_mult = current_mult * 1.05
        elif acceptance < 0.5:
            # Manager accepted less than 50% → forecast overshooting → decrease
            new_mult = current_mult * 0.95
        else:
            new_mult = current_mult

        learned[category] = round(new_mult, 3)

    # Save learned multipliers
    os.makedirs(os.path.dirname(LEARNED_MULTIPLIERS_PATH), exist_ok=True)
    with open(LEARNED_MULTIPLIERS_PATH, 'w') as f:
        json.dump(learned, f, indent=2)
