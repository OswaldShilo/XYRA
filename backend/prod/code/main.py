"""
XYRA — main.py  v2.0
FastAPI application: Static mode (CSV pipeline) + Dynamic mode (real-time POS twin + WebSocket).
Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import (
    FastAPI, UploadFile, File, Form, HTTPException,
    WebSocket, WebSocketDisconnect, Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

# ── Layer imports ─────────────────────────────────────────────────────────────
from layers.layer1_cleaner import clean_csv
from layers.layer1_5_dsp import filter_noise, simple_decompose
from layers.layer2_forecaster import forecast_all
from layers.layer3_classifier import classify_products
from layers.layer4_events import get_event_multipliers, get_event_briefing
from layers.layer5_weather import get_weather_multipliers, get_weather_briefing
from layers.layer6_output import (
    generate_dashboard, get_top_recommendations,
    generate_briefing, generate_chart_png,
)
from layers.layer7_learning import record_feedback, get_learning_stats, get_learned_multipliers
from layers.layer_analytics import compute_all_analytics

# ── Dynamic mode imports ───────────────────────────────────────────────────────
from dynamic.digital_twin import SKUDigitalTwin, twin_registry
from dynamic.ws_broadcaster import ws_manager, broadcast_loop
from dynamic.poller import get_poller_status, start_poller

# ── Utils ─────────────────────────────────────────────────────────────────────
from utils import format_json_response

# ── Session store ─────────────────────────────────────────────────────────────
_sessions: dict = {}

# ── Lifespan: start background WebSocket broadcast loop ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    broadcast_task = asyncio.create_task(broadcast_loop(ws_manager, twin_registry))
    poller_task = asyncio.create_task(
        start_poller(twin_registry, os.getenv("POS_API_URL"))
    )
    yield
    broadcast_task.cancel()
    poller_task.cancel()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="XYRA API",
    description="AI-powered retail supply chain intelligence. Predict the rush. Never run out.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── Pydantic models ────────────────────────────────────────────────────────────
class FeedbackPayload(BaseModel):
    product_id: str
    recommendation_id: str
    accepted: bool
    actual_qty_ordered: Optional[float] = None
    category: Optional[str] = "general"
    manager_note: Optional[str] = ""

class SaleEvent(BaseModel):
    product_id: str
    qty_sold: float
    timestamp: Optional[str] = None
    store_id: Optional[str] = None

class RestockEvent(BaseModel):
    product_id: str
    qty_added: float
    timestamp: Optional[str] = None

class TwinProduct(BaseModel):
    product_id: str
    category: str = "general"
    current_stock: float = 0.0
    velocity: float = 0.0

class InitTwinsPayload(BaseModel):
    products: list[TwinProduct]

# ── Pipeline helper ────────────────────────────────────────────────────────────
def _run_pipeline(
    file_bytes: bytes, pincode: str, store_name: str, lead_time: int
) -> dict:
    """Run all 7 layers synchronously. Called in a thread pool."""

    # L1 — clean
    df, clean_report = clean_csv(file_bytes)
    if df.empty:
        raise ValueError(f"CSV cleaning failed: {clean_report.get('errors', [])}")

    df_cleaned = df.copy()  # snapshot before DSP — used for analytics

    # L1.5 — filter + decompose
    df, dsp_report = filter_noise(df)
    df = simple_decompose(df)

    # L4 + L5 — event & weather signals (needed before classification)
    event_data = get_event_multipliers(pincode)
    weather_data = get_weather_multipliers(pincode)
    learned = get_learned_multipliers()

    # Merge multipliers: take max per category, then scale by learned factor
    combined: dict = {}
    for cat, m in event_data.get("multipliers", {}).items():
        combined[cat] = m
    for cat, m in weather_data.get("multipliers", {}).items():
        combined[cat] = max(combined.get(cat, 1.0), m)
    for cat, m in learned.items():
        combined[cat] = combined.get(cat, 1.0) * m

    # L2 — forecast
    forecasts = forecast_all(df, forecast_days=30)

    # L3 — classify
    classifications = classify_products(df, forecasts, combined, lead_time)

    # L6 — output
    dashboard = generate_dashboard(classifications)
    recommendations = get_top_recommendations(classifications, limit=10)
    briefing = generate_briefing(
        classifications,
        get_event_briefing(event_data.get("events", [])),
        get_weather_briefing(weather_data.get("weather", [])),
    )
    chart = generate_chart_png(classifications)

    # Serialise forecast Timestamps → ISO strings
    serialisable_forecasts: dict = {}
    for pid, fc in forecasts.items():
        fc2 = dict(fc)
        if hasattr(fc2.get("last_date"), "isoformat"):
            fc2["last_date"] = fc2["last_date"].isoformat()
        serialisable_forecasts[pid] = fc2

    # Analytics layer — runs on pre-DSP cleaned data
    analytics = compute_all_analytics(df_cleaned, classifications, forecasts)

    return {
        "store_name": store_name,
        "pincode": pincode,
        "lead_time": lead_time,
        "processed_at": datetime.now().isoformat(),
        "clean_report": clean_report,
        "dsp_report": dsp_report,
        "forecasts": serialisable_forecasts,
        "classifications": classifications,
        "dashboard": dashboard,
        "recommendations": recommendations,
        "briefing": briefing,
        "chart": chart,
        "event_data": event_data,
        "weather_data": weather_data,
        "analytics": analytics,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# STATIC MODE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    store_name: str = Form("My Store"),
    pincode: str = Form("600001"),
    lead_time: int = Form(2),
):
    """Upload historical CSV and run the full 7-layer ML pipeline."""
    csv_bytes = await file.read()
    if not csv_bytes:
        raise HTTPException(400, "Empty file uploaded.")

    try:
        result = await run_in_threadpool(_run_pipeline, csv_bytes, pincode, store_name, lead_time)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Pipeline error: {exc}")

    session_id = str(uuid.uuid4())[:8]
    _sessions[session_id] = result

    d = result["dashboard"]
    return format_json_response({
        "session_id": session_id,
        "store_name": store_name,
        "message": "Pipeline executed successfully.",
        "quick_stats": {
            "total_products": d.get("total_products", 0),
            "critical": d.get("critical_count", 0),
            "warning": d.get("warning_count", 0),
            "safe": d.get("safe_count", 0),
        },
    })


@app.get("/session/{session_id}/dashboard")
def get_dashboard(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s["dashboard"])


@app.get("/session/{session_id}/recommendations")
def get_recommendations(session_id: str, limit: int = Query(5, ge=1, le=20)):
    s = _get_session(session_id)
    return format_json_response(s["recommendations"][:limit])


@app.get("/session/{session_id}/briefing")
def get_briefing(session_id: str):
    s = _get_session(session_id)
    return format_json_response({"briefing": s["briefing"], "store_name": s["store_name"]})


@app.get("/session/{session_id}/forecast/{product_id}")
def get_forecast(session_id: str, product_id: str):
    s = _get_session(session_id)
    fc = s["forecasts"].get(product_id)
    if not fc:
        raise HTTPException(404, f"Product {product_id} not found in session.")
    return format_json_response(fc)


@app.get("/session/{session_id}/chart")
def get_chart(session_id: str):
    s = _get_session(session_id)
    return format_json_response({"chart": s["chart"]})


@app.get("/session/{session_id}/analytics/inventory-health")
def analytics_inventory_health(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s.get("analytics", {}).get("inventory_health", []))


@app.get("/session/{session_id}/analytics/demand-patterns")
def analytics_demand_patterns(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s.get("analytics", {}).get("demand_patterns", {}))


@app.get("/session/{session_id}/analytics/spike-detection")
def analytics_spike_detection(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s.get("analytics", {}).get("spike_detection", []))


@app.get("/session/{session_id}/analytics/historical-comparison")
def analytics_historical_comparison(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s.get("analytics", {}).get("historical_comparison", {}))


@app.get("/session/{session_id}/analytics/forecast-accuracy")
def analytics_forecast_accuracy(session_id: str):
    s = _get_session(session_id)
    return format_json_response(s.get("analytics", {}).get("forecast_accuracy", []))


@app.get("/sessions")
def list_sessions(limit: int = Query(10, ge=1, le=100)):
    recent = [
        {
            "session_id": sid,
            "store_name": s["store_name"],
            "pincode": s["pincode"],
            "processed_at": s["processed_at"],
            "total_products": s["dashboard"].get("total_products", 0),
            "critical_count": s["dashboard"].get("critical_count", 0),
        }
        for sid, s in list(_sessions.items())[-limit:]
    ]
    return format_json_response(recent)


# ═══════════════════════════════════════════════════════════════════════════════
# DYNAMIC MODE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/init-twins")
def init_twins(payload: InitTwinsPayload):
    """Initialise digital twins for a set of SKUs."""
    for p in payload.products:
        twin_registry[p.product_id] = SKUDigitalTwin(
            product_id=p.product_id,
            category=p.category,
            current_stock=p.current_stock,
            velocity=p.velocity,
        )
    return format_json_response({
        "initialized": len(payload.products),
        "twins": list(twin_registry.keys()),
    })


@app.post("/api/sale-event")
def sale_event(event: SaleEvent):
    """Receive a real-time sale event from the POS (webhook)."""
    twin = twin_registry.get(event.product_id)
    if twin is None:
        twin = SKUDigitalTwin(product_id=event.product_id, category="general", current_stock=100.0)
        twin_registry[event.product_id] = twin
    twin.update_sale(event.qty_sold)
    return format_json_response(twin.snapshot())


@app.post("/restock-event")
def restock_event(event: RestockEvent):
    """Record a stock replenishment."""
    twin = twin_registry.get(event.product_id)
    if twin is None:
        raise HTTPException(404, f"Product {event.product_id} not tracked.")
    twin.restock(event.qty_added)
    return format_json_response(twin.snapshot())


@app.get("/api/sync")
def manual_sync():
    """Trigger an immediate poll cycle (for testing)."""
    return format_json_response({
        "status": "sync_triggered",
        "twins": len(twin_registry),
        "poller": get_poller_status(),
    })


@app.get("/twin/{product_id}")
def get_twin(product_id: str):
    """Get current digital twin state for one SKU."""
    twin = twin_registry.get(product_id)
    if twin is None:
        raise HTTPException(404, f"Product {product_id} not tracked.")
    return format_json_response(twin.snapshot())


@app.get("/twin/snapshot")
def get_all_twins():
    """Get all SKU twin states."""
    return format_json_response({pid: t.snapshot() for pid, t in twin_registry.items()})


@app.get("/alerts")
def get_alerts():
    """Get all active CRITICAL and WARNING alerts, sorted by severity."""
    alerts = [
        t.snapshot() for t in twin_registry.values()
        if t.risk_level in ("CRITICAL", "WARNING")
    ]
    alerts.sort(key=lambda a: 0 if a["risk_level"] == "CRITICAL" else 1)
    return format_json_response(alerts)


@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    """WebSocket endpoint — pushes live twin snapshots every 5 seconds."""
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive; client can send pings
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/feedback")
def submit_feedback(payload: FeedbackPayload):
    """Record manager acceptance / rejection for Layer 7 learning."""
    try:
        result = record_feedback(payload.model_dump())
        return format_json_response(result)
    except Exception as exc:
        raise HTTPException(500, str(exc))


@app.get("/learning-stats")
def learning_stats_ep():
    return format_json_response(get_learning_stats())


@app.get("/event-signals")
def event_signals(pincode: str = Query("600001"), lookahead_days: int = Query(14)):
    return format_json_response(get_event_multipliers(pincode, lookahead_days))


@app.get("/weather-signals")
def weather_signals(pincode: str = Query("600001")):
    return format_json_response(get_weather_multipliers(pincode))


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "sessions": len(_sessions),
        "twins": len(twin_registry),
        "ws_connections": len(ws_manager.active_connections),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_session(session_id: str) -> dict:
    s = _sessions.get(session_id)
    if not s:
        raise HTTPException(404, "Session not found.")
    return s


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
