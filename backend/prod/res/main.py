"""
FLUX — main.py
FastAPI application — all endpoints for the FLUX supply chain resilience backend
Run: uvicorn main:app --reload
"""

import os
import uuid
from io import BytesIO
from typing import Optional
from datetime import date

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Layer imports ─────────────────────────────────────────────────────────────
from layers.layer1_cleaner    import clean_csv
from layers.layer1_5_dsp      import filter_noise
from layers.layer2_forecaster import forecast_all
from layers.layer3_classifier import classify_products
from layers.layer4_events     import get_event_multipliers
from layers.layer5_weather    import get_weather_multipliers
from layers.layer6_output     import generate_dashboard, get_top_recommendations, generate_briefing
from layers.layer7_learning   import record_feedback, get_learning_stats, get_learned_multipliers


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
_sessions: dict = {}


# ── Pydantic models ───────────────────────────────────────────────────────────

class FeedbackPayload(BaseModel):
    product_id: str
    recommendation_id: str
    accepted: bool
    recommended_qty: int
    actual_qty_ordered: Optional[int] = None
    category: str = "general"
    manager_note: str = ""


class EventSignalRequest(BaseModel):
    pincode: str
    lookahead_days: int = 14


# ── Helper: run full pipeline ─────────────────────────────────────────────────

def _run_pipeline(file_bytes: bytes, pincode: str, store_name: str, lead_time: int):
    """Runs all 7 layers and returns a complete session result dict."""

    # Layer 1 — Clean
    df, clean_report = clean_csv(file_bytes)

    # Layer 1.5 — DSP filter
    df, dsp_report = filter_noise(df)

    # Layer 4 — Events (needed before classification)
    event_data = get_event_multipliers(pincode)
    event_multipliers = event_data.get("multipliers", {})

    # Layer 5 — Weather
    weather_data = get_weather_multipliers(pincode)
    weather_multipliers = weather_data.get("multipliers", {})

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
    recommendations = get_top_recommendations(classified)
    briefing = generate_briefing(
        classified,
        active_events=event_data.get("active_events", []),
        weather_condition=weather_data.get("condition", "normal"),
        store_name=store_name,
    )

    return {
        "dashboard": dashboard,
        "recommendations": recommendations,
        "briefing": briefing,
        "forecasts": forecasts,
        "event_data": event_data,
        "weather_data": weather_data,
        "clean_report": clean_report,
        "dsp_report": dsp_report,
        "classified": classified,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "FLUX API", "version": "1.0.0"}


@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    pincode: str = Query(..., description="Store pincode for event & weather signals"),
    store_name: str = Query("My Store", description="Store display name"),
    lead_time_days: int = Query(2, description="Supplier lead time in days"),
):
    """
    Upload a sales CSV and run the complete FLUX pipeline.
    Returns session_id to fetch results from other endpoints.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        result = _run_pipeline(file_bytes, pincode, store_name, lead_time_days)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = result

    return {
        "session_id": session_id,
        "store_name": store_name,
        "pincode": pincode,
        "summary": result["dashboard"]["summary"],
        "active_events": result["event_data"].get("active_events", []),
        "weather_condition": result["weather_data"].get("condition", "normal"),
        "message": f"Pipeline complete. Use session_id '{session_id}' to fetch results.",
    }


@app.get("/dashboard")
def get_dashboard(session_id: str = Query(...)):
    """Returns the full risk-classified product dashboard."""
    session = _get_session(session_id)
    return session["dashboard"]


@app.get("/recommendations")
def get_recommendations(session_id: str = Query(...), top_n: int = Query(5)):
    """Returns top N urgent reorder actions with plain-English reasons."""
    session = _get_session(session_id)
    return {
        "recommendations": get_top_recommendations(session["classified"], top_n),
        "generated_at": str(date.today()),
    }


@app.get("/briefing")
def get_briefing(session_id: str = Query(...)):
    """Returns the plain-text weekly manager briefing."""
    session = _get_session(session_id)
    return {
        "briefing": session["briefing"],
        "generated_at": str(date.today()),
    }


@app.get("/forecast/{product_id}")
def get_product_forecast(product_id: str, session_id: str = Query(...)):
    """Returns 30-day demand forecast for a specific product."""
    session = _get_session(session_id)
    fc = session["forecasts"].get(product_id)
    if not fc:
        raise HTTPException(status_code=404, detail=f"Product '{product_id}' not found.")
    return fc


@app.post("/event-signals")
def event_signals(payload: EventSignalRequest):
    """Get upcoming event multipliers for a pincode."""
    return get_event_multipliers(payload.pincode, payload.lookahead_days)


@app.get("/weather-signals")
def weather_signals(pincode: str = Query(...)):
    """Get weather-based demand adjustments for a pincode."""
    return get_weather_multipliers(pincode)


@app.post("/feedback")
def submit_feedback(payload: FeedbackPayload):
    """Manager submits accept/reject on a recommendation."""
    result = record_feedback(
        product_id=payload.product_id,
        recommendation_id=payload.recommendation_id,
        accepted=payload.accepted,
        recommended_qty=payload.recommended_qty,
        actual_qty_ordered=payload.actual_qty_ordered,
        category=payload.category,
        manager_note=payload.manager_note,
    )
    return result


@app.get("/learning-stats")
def learning_stats():
    """View model accuracy and feedback history."""
    return get_learning_stats()


# ── Utility ───────────────────────────────────────────────────────────────────

def _get_session(session_id: str) -> dict:
    if session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found. Upload a CSV first via POST /upload-csv."
        )
    return _sessions[session_id]
