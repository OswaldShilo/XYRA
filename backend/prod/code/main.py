"""
FLUX — main.py
FastAPI application with all REST endpoints
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import uuid
from io import BytesIO
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ── Layer imports ─────────────────────────────────────────────────────────────
from layers.layer1_cleaner import clean_csv
from layers.layer1_5_dsp import filter_noise, simple_decompose
from layers.layer2_forecaster import forecast_all
from layers.layer3_classifier import classify_products
from layers.layer4_events import get_event_multipliers, get_event_briefing
from layers.layer5_weather import get_weather_multipliers, get_weather_briefing
from layers.layer6_output import generate_dashboard, get_top_recommendations, generate_briefing, generate_chart_png
from layers.layer7_learning import record_feedback, get_learning_stats, get_learned_multipliers

from utils import validate_csv_structure, validate_feedback, format_json_response
from utils.helpers import get_pincode_or_default, get_lead_time_or_default


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FLUX API",
    description="AI-powered retail supply chain resilience backend. Predict the rush. Never run out.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (for MVP — replace with Redis/DB in production)
_sessions = {}

# Store config
STORE_PINCODE = os.getenv("STORE_PINCODE", "600001")
LEAD_TIME_DAYS = int(os.getenv("LEAD_TIME_DAYS", "2"))


# ── Pydantic models ───────────────────────────────────────────────────────────

class FeedbackPayload(BaseModel):
    product_id: str
    recommendation_id: str
    accepted: bool
    recommended_qty: Optional[int] = None
    actual_qty_ordered: Optional[int] = None
    category: str = "general"
    manager_note: str = ""


class EventSignalRequest(BaseModel):
    pincode: str
    lookahead_days: int = 14


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


# ── Helper: run full pipeline ─────────────────────────────────────────────────

def _run_pipeline(file_bytes: bytes, pincode: str, store_name: str, lead_time: int):
    """Runs all 7 layers and returns a complete session result dict."""

    # Layer 1 — Clean
    df, clean_report = clean_csv(file_bytes)

    if df.empty:
        raise ValueError(f"CSV cleaning failed: {clean_report['errors']}")

    # Layer 1.5 — DSP filter
    df, dsp_report = filter_noise(df)
    df = simple_decompose(df)

    # Layer 4 — Events (needed before classification)
    event_data = get_event_multipliers(pincode)
    event_multipliers = event_data.get("multipliers", {})
    event_briefing_text = get_event_briefing(event_data.get("events", []))

    # Layer 5 — Weather
    weather_data = get_weather_multipliers(pincode)
    weather_multipliers = weather_data.get("multipliers", {})
    weather_briefing_text = get_weather_briefing(weather_data.get("weather", []))

    # Merge event + weather multipliers (take max per category)
    all_external_multipliers = {}
    for cat in set(list(event_multipliers.keys()) + list(weather_multipliers.keys())):
        all_external_multipliers[cat] = max(
            event_multipliers.get(cat, 1.0),
            weather_multipliers.get(cat, 1.0),
        )

    # Apply learned multipliers from Layer 7 on top
    learned = get_learned_multipliers()
    for cat, mult in learned.items():
        all_external_multipliers[cat] = all_external_multipliers.get(cat, 1.0) * mult

    # Layer 2 — Forecast
    forecasts = forecast_all(df)

    # Layer 3 — Classify
    classified = classify_products(df, forecasts, all_external_multipliers, lead_time)

    # Layer 6 — Output
    dashboard = generate_dashboard(classified)
    top_recommendations = get_top_recommendations(classified)
    briefing = generate_briefing(classified, event_briefing_text, weather_briefing_text)
    chart_base64 = generate_chart_png(classified)

    session_result = {
        'session_id': str(uuid.uuid4()),
        'store_name': store_name,
        'pincode': pincode,
        'processed_at': datetime.now().isoformat(),
        'data_quality': {
            'original_rows': clean_report['original_rows'],
            'final_rows': clean_report['final_rows'],
            'duplicates_removed': clean_report['duplicates_removed'],
            'nulls_handled': clean_report['nulls_handled'],
            'negatives_removed': clean_report.get('negatives_removed', 0),
        },
        'dashboard': dashboard,
        'top_recommendations': top_recommendations,
        'briefing': briefing,
        'chart': chart_base64,
        'layers': {
            'layer1': clean_report,
            'layer1_5': dsp_report,
            'layer4_events': event_data,
            'layer5_weather': weather_data,
        }
    }

    # Store session
    _sessions[session_result['session_id']] = session_result

    return session_result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    store_name: str = Query("Default Store"),
    pincode: str = Query(STORE_PINCODE),
    lead_time: int = Query(LEAD_TIME_DAYS),
):
    """
    Upload CSV and run full FLUX pipeline.
    
    Returns: Session with dashboard, recommendations, and briefing.
    """
    try:
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        result = _run_pipeline(file_bytes, pincode, store_name, lead_time)

        return format_json_response({
            "session_id": result['session_id'],
            "store_name": result['store_name'],
            "message": f"Pipeline executed successfully. Found {result['dashboard']['critical_count']} critical products.",
            "quick_stats": {
                "total_products": result['dashboard']['total_products'],
                "critical": result['dashboard']['critical_count'],
                "warning": result['dashboard']['warning_count'],
                "safe": result['dashboard']['safe_count'],
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/session/{session_id}/dashboard")
async def get_dashboard(session_id: str):
    """Get risk dashboard for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    return format_json_response(session['dashboard'])


@app.get("/session/{session_id}/recommendations")
async def get_recommendations(session_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get top reorder recommendations for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    recs = get_top_recommendations(session['dashboard']['products'], limit=limit)
    
    return format_json_response({
        "total_recommendations": len(recs),
        "recommendations": recs,
    })


@app.get("/session/{session_id}/briefing")
async def get_briefing_text(session_id: str):
    """Get plain-text manager briefing for a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    
    return format_json_response({
        "briefing": session['briefing'],
        "store_name": session['store_name'],
        "generated_at": session['processed_at'],
    })


@app.get("/session/{session_id}/forecast/{product_id}")
async def get_product_forecast(session_id: str, product_id: str):
    """Get 30-day forecast for a specific product."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    products = session['dashboard']['products']
    product = next((p for p in products if p['product_id'] == product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found in session")

    return format_json_response({
        "product_id": product_id,
        "forecast_7d_avg": product['forecast_7d_avg'],
        "forecast_14d_total": product['forecast_14d_total'],
        "current_stock": product['current_stock'],
        "risk_level": product['risk_level'],
        "days_to_stockout": product['days_to_stockout'],
    })


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackPayload):
    """
    Submit manager feedback on a recommendation for continuous learning.
    
    Returns: Feedback confirmation and updated learning stats.
    """
    is_valid, errors = validate_feedback(feedback.dict())
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation errors: {errors}")

    try:
        result = record_feedback(feedback.dict())
        return format_json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback recording error: {str(e)}")


@app.get("/learning-stats")
async def get_learning_stats_endpoint():
    """Get learning statistics: acceptance rate, accuracy by category, multipliers."""
    try:
        stats = get_learning_stats()
        return format_json_response(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving learning stats: {str(e)}")


@app.get("/event-signals")
async def get_events(pincode: str = Query(STORE_PINCODE), lookahead_days: int = Query(14)):
    """Get upcoming events and demand spike multipliers."""
    try:
        result = get_event_multipliers(pincode, lookahead_days)
        return format_json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event signal error: {str(e)}")


@app.get("/weather-signals")
async def get_weather(pincode: str = Query(STORE_PINCODE)):
    """Get weather forecast and demand adjustments."""
    try:
        result = get_weather_multipliers(pincode)
        return format_json_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather signal error: {str(e)}")


@app.get("/session/{session_id}/chart")
async def get_chart(session_id: str):
    """Get risk heatmap chart as base64 PNG."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    
    return format_json_response({
        "chart_base64": session['chart'],
        "format": "png",
    })


@app.get("/sessions")
async def list_sessions(limit: int = Query(10, ge=1, le=100)):
    """List recent pipeline sessions."""
    sessions_list = sorted(
        _sessions.values(),
        key=lambda x: x['processed_at'],
        reverse=True
    )[:limit]

    return format_json_response({
        "total_sessions": len(_sessions),
        "recent_sessions": [
            {
                "session_id": s['session_id'],
                "store_name": s['store_name'],
                "processed_at": s['processed_at'],
                "products_analyzed": s['dashboard']['total_products'],
                "critical_count": s['dashboard']['critical_count'],
            }
            for s in sessions_list
        ]
    })


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
