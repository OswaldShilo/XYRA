"""
FLUX — Quick Validation Test
Tests all layers with sample CSV data without heavy dependencies
"""

import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from io import BytesIO

print("=" * 70)
print("FLUX — Pipeline Validation Test")
print("=" * 70)


# Test Layer 1: Data Cleaning
print("\n[Layer 1] Testing Data Cleaning...")
try:
    from layers.layer1_cleaner import clean_csv
    
    # Read sample CSV
    sample_csv = pd.read_csv('data/retail_store_inventory.csv')
    print(f"✓ Sample CSV loaded: {len(sample_csv)} rows, {len(sample_csv.columns)} columns")
    print(f"  Columns: {list(sample_csv.columns)}")
    
    # Convert to bytes and clean
    csv_bytes = sample_csv.to_csv(index=False).encode('utf-8')
    cleaned_df, report = clean_csv(csv_bytes)
    
    print(f"✓ Cleaning successful:")
    print(f"  - Original rows: {report['original_rows']}")
    print(f"  - Final rows: {report['final_rows']}")
    print(f"  - Duplicates removed: {report['duplicates_removed']}")
    print(f"  - Nulls handled: {report['nulls_handled']}")
    print(f"  - Columns detected: {list(report['detected_columns'].keys())}")
    
except Exception as e:
    print(f"✗ Layer 1 failed: {e}")
    sys.exit(1)


# Test Layer 1.5: DSP Filtering
print("\n[Layer 1.5] Testing DSP Noise Filtering...")
try:
    from layers.layer1_5_dsp import filter_noise, simple_decompose
    
    filtered_df, dsp_report = filter_noise(cleaned_df)
    print(f"✓ Filtering successful:")
    print(f"  - Products filtered: {dsp_report['products_filtered']}")
    print(f"  - Outliers clipped: {dsp_report['outliers_clipped']}")
    print(f"  - Z-score anomalies: {dsp_report['z_score_anomalies']}")
    
    decomposed_df = simple_decompose(filtered_df)
    print(f"✓ Decomposition successful (trend + seasonal extracted)")
    
except Exception as e:
    print(f"✗ Layer 1.5 failed: {e}")
    sys.exit(1)


# Test Layer 2: Forecasting
print("\n[Layer 2] Testing Demand Forecasting...")
try:
    from layers.layer2_forecaster import forecast_all
    
    forecasts = forecast_all(decomposed_df, forecast_days=30)
    print(f"✓ Forecasting successful:")
    print(f"  - Products forecasted: {len(forecasts)}")
    
    # Show sample forecast
    for idx, (product_id, forecast_data) in enumerate(list(forecasts.items())[:2]):
        print(f"  - {product_id}:")
        print(f"    * 7-day avg: {np.mean(forecast_data['forecast_7d']):.2f} units")
        print(f"    * Method: {forecast_data.get('method', 'unknown')}")
        print(f"    * Spike score: {forecast_data['spike_score']:.2f}x")
    
except Exception as e:
    print(f"✗ Layer 2 failed: {e}")
    sys.exit(1)


# Test Layer 3: Classification
print("\n[Layer 3] Testing Risk Classification...")
try:
    from layers.layer3_classifier import classify_products
    
    classifications = classify_products(decomposed_df, forecasts)
    print(f"✓ Classification successful ({len(classifications)} products):")
    
    critical = [c for c in classifications if c['priority'] == 1]
    warning = [c for c in classifications if c['priority'] == 2]
    safe = [c for c in classifications if c['priority'] == 3]
    
    print(f"  - 🔴 CRITICAL: {len(critical)}")
    print(f"  - 🟡 WARNING: {len(warning)}")
    print(f"  - 🟢 SAFE: {len(safe)}")
    
    if critical:
        print(f"\n  Top CRITICAL:")
        for c in critical[:2]:
            print(f"    * {c['product_id']}: {c['risk_level']} | Reorder {c['reorder_qty']} by {c['reorder_by_date']}")
    
except Exception as e:
    print(f"✗ Layer 3 failed: {e}")
    sys.exit(1)


# Test Layer 4: Events
print("\n[Layer 4] Testing Event Signals...")
try:
    from layers.layer4_events import get_event_multipliers
    
    event_data = get_event_multipliers('600001', lookahead_days=14)
    print(f"✓ Event signals retrieved:")
    print(f"  - Region: {event_data['region']}")
    print(f"  - Upcoming events: {len(event_data['events'])}")
    if event_data['events']:
        for event in event_data['events'][:2]:
            print(f"    * {event['name']} ({event['days_until']} days)")
    print(f"  - Category multipliers: {list(event_data['multipliers'].keys())}")
    
except Exception as e:
    print(f"✗ Layer 4 failed: {e}")
    sys.exit(1)


# Test Layer 5: Weather
print("\n[Layer 5] Testing Weather Signals...")
try:
    from layers.layer5_weather import get_weather_multipliers
    
    weather_data = get_weather_multipliers('600001')
    print(f"✓ Weather data retrieved:")
    print(f"  - 7-day forecast available")
    print(f"  - Category multipliers: {list(weather_data['multipliers'].keys())}")
    
except Exception as e:
    print(f"✗ Layer 5 failed: {e}")
    sys.exit(1)


# Test Layer 6: Output
print("\n[Layer 6] Testing Output Generation...")
try:
    from layers.layer6_output import generate_dashboard, get_top_recommendations, generate_briefing
    
    dashboard = generate_dashboard(classifications)
    print(f"✓ Dashboard generated:")
    print(f"  - Total products: {dashboard['total_products']}")
    print(f"  - Critical count: {dashboard['critical_count']}")
    print(f"  - Warning count: {dashboard['warning_count']}")
    print(f"  - Safe count: {dashboard['safe_count']}")
    
    recommendations = get_top_recommendations(classifications, limit=5)
    print(f"✓ Top recommendations: {len(recommendations)}")
    
    briefing = generate_briefing(classifications, "Sample event", "Sample weather")
    print(f"✓ Manager briefing generated ({len(briefing)} characters)")
    
except Exception as e:
    print(f"✗ Layer 6 failed: {e}")
    sys.exit(1)


# Test Layer 7: Learning
print("\n[Layer 7] Testing Feedback & Learning...")
try:
    from layers.layer7_learning import record_feedback, get_learning_stats
    
    feedback = {
        'product_id': 'P0001',
        'recommendation_id': 'TEST_001',
        'accepted': True,
        'actual_qty_ordered': 100,
        'category': 'Groceries',
        'manager_note': 'Test feedback',
    }
    
    result = record_feedback(feedback)
    print(f"✓ Feedback recorded: {result['feedback_id']}")
    
    stats = get_learning_stats()
    print(f"✓ Learning stats retrieved:")
    print(f"  - Total feedback: {stats['total_feedback']}")
    print(f"  - Acceptance rate: {stats['acceptance_rate']:.1%}")
    
except Exception as e:
    print(f"✗ Layer 7 failed: {e}")
    sys.exit(1)


print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED ✓")
print("=" * 70)
print("\nNext steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Start server: uvicorn main:app --reload")
print("3. Upload CSV: POST /upload-csv")
print("4. Test endpoints at http://localhost:8000/docs")
