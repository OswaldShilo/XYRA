# XYRA — Product Requirements Document
**Version:** 2.0  
**Status:** Active Development  
**Team:** 2Bits  
**Last Updated:** April 2026

---

## 1. Product Overview

XYRA is an AI-powered retail supply chain intelligence platform for small and medium-sized Indian retailers. It predicts demand spikes, classifies inventory risk, and automates reorder decisions — delivered through a clean dashboard with two distinct data modes: static CSV analysis and dynamic real-time monitoring.

**Tagline:** Predict the rush. Never run out.

---

## 2. Problem Statement

Indian SME retailers lose ₹1.2 Trillion annually to stockouts and dead inventory. 68% still rely on manual stock checks. Demand spikes from festivals, local events, and weather go undetected. Enterprise tools cost $200+/user/month and require IT teams.

XYRA solves this at under ₹3,000/store/month with zero IT setup.

---

## 3. User Journey

```
Landing → Auth → Onboarding (4 steps) → Mode Selection → Dashboard
```

### Onboarding — 4 Steps
1. Store type (Grocery / Pharmacy / FMCG / General)
2. Store name
3. Store location (pincode)
4. Product categories (multi-select)

After onboarding, user selects a data mode before reaching the dashboard.

---

## 4. Data Modes

### Mode 1 — Static (CSV Upload)
User uploads a historical sales CSV. XYRA runs the full 7-layer ML pipeline once and returns a complete analysis report. Best for retailers without live POS systems.

**Flow:**
```
CSV Upload → Layer 1 Clean → Layer 1.5 DSP Filter → Layer 2 Forecast →
Layer 3 Classify → Layer 4 Events → Layer 5 Weather → Layer 6 Output
```

**Output:** Full dashboard with demand forecast, risk classification, reorder recommendations, and weekly briefing.

---

### Mode 2 — Dynamic (Real-Time)
Connects to the store's POS system via two concurrent methods running in parallel for speed and reliability.

**Method A — Webhook (Primary)**
POS pushes sale events to XYRA in real time. Zero lag. Best for POS systems that support webhooks (Petpooja, Marg ERP, Vyapar).

```
POS Sale Event → POST /api/sale-event → Update Digital Twin → Threshold Check → Alert
```

**Method B — Polling API (Fallback)**
XYRA pulls latest sales from POS API every 15 minutes via APScheduler. Works with any POS that has an API. Runs concurrently with Method A so if the webhook misses an event, polling catches it.

```
APScheduler (15min) → GET /api/sales?since={last_sync} → Update Digital Twin → Threshold Check
```

**Why both concurrently:**
- Webhook gives sub-second updates on direct sales events
- Polling catches any events the webhook missed (network failure, POS delay)
- Together they guarantee no sale event is ever missed
- Dashboard reflects near-real-time state at all times

**Digital Twin Layer:**
Each SKU has a live Python object in memory that tracks current stock, rolling sales velocity, days-to-stockout, and risk level. Updates on every incoming sale event.

**Live Dashboard:**
WebSocket connection pushes dashboard updates to the frontend every 5 seconds. No page refresh needed.

---

## 5. Dashboard — Existing Panels

| Panel | Description |
|---|---|
| Executive Summary | Plain-English headline: demand surge %, category, action deadline |
| Demand Forecast Chart | Recharts area chart — actual vs predicted, 7-day window |
| Weather Impact | Current condition, temperature, demand impact note |
| Stock Alerts | Per-category risk level (Critical / Low / Healthy) with units remaining |
| Store Location | Pincode-based map marker with store name and district |
| Sales by Category | Donut chart — Grocery, Pharmacy, Retail, Other |
| In-House Events | Upcoming events with demand impact percentage |
| Prediction Accuracy | Rolling MAPE-based accuracy percentage |
| Items Tracked | Total SKU count |
| Supply Disruptions | Active disruption count |

---

## 6. New Graphs to Add (v2)

### Graph 1 — SKU-Level Risk Heatmap
**What it shows:** A 7-day forward-looking grid. Rows = top 10 SKUs by risk. Columns = days. Cells colored by predicted risk level (red/amber/green). Shows at a glance which products will become critical and when.

**Data source:** Layer 3 classifier output — `days_to_stockout` per SKU projected over 7 days with event and weather multipliers applied.

**Why it matters:** Existing forecast chart shows category-level demand. This shows SKU-level timeline — much more actionable for procurement decisions.

---

### Graph 2 — Demand Signal Breakdown (Stacked Bar)
**What it shows:** For each product category, a stacked bar showing how much of the predicted demand comes from each signal: baseline sales, event multiplier, weather multiplier. 

**Example:** Beverages bar = 60% baseline + 25% IPL event + 15% heatwave.

**Data source:** Layer 4 and Layer 5 multiplier outputs merged with Layer 2 forecast baseline.

**Why it matters:** Makes the AI reasoning transparent — managers can see exactly why a demand spike was predicted and which signal is driving it.

---

## 7. Backend — 7-Layer ML Pipeline

| Layer | File | Purpose |
|---|---|---|
| 1 | `layer1_cleaner.py` | CSV ingestion, column detection, null fill, deduplication |
| 1.5 | `layer1_5_dsp.py` | Savitzky-Golay smoothing, Z-score outlier clip, STL decomposition |
| 2 | `layer2_forecaster.py` | Prophet per-SKU, 7 + 30 day forecast, confidence intervals |
| 3 | `layer3_classifier.py` | Critical / Warning / Safe, reorder qty formula |
| 4 | `layer4_events.py` | Indian festival calendar, pincode-to-region, category multipliers |
| 5 | `layer5_weather.py` | OpenWeatherMap, rain/heat/cold demand rules |
| 6 | `layer6_output.py` | Dashboard JSON, plain-English briefing, PNG chart |
| 7 | `layer7_learning.py` | Manager feedback loop, multiplier recalibration, accuracy log |

---

## 8. REST API Endpoints

### Static Mode
| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload-csv` | Upload CSV, trigger full pipeline, return session_id |
| GET | `/session/{id}/dashboard` | Full dashboard data for session |
| GET | `/session/{id}/recommendations` | Top reorder actions |
| GET | `/session/{id}/briefing` | Plain-English weekly briefing |
| GET | `/session/{id}/forecast/{product_id}` | 30-day forecast per SKU |

### Dynamic Mode
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/sale-event` | Receive real-time sale from POS webhook |
| GET | `/api/sync` | Manual trigger for polling sync |
| GET | `/twin/{product_id}` | Current digital twin state for one SKU |
| GET | `/twin/snapshot` | All SKUs current state |
| GET | `/alerts` | All active Critical/Warning alerts |
| POST | `/restock-event` | Update twin when new stock arrives |
| WebSocket | `/ws/dashboard` | Live dashboard stream (5-second push) |

### Shared
| Method | Endpoint | Description |
|---|---|---|
| POST | `/feedback` | Manager accepts/rejects recommendation |
| GET | `/learning-stats` | Model accuracy and feedback history |
| GET | `/event-signals` | Festival multipliers for pincode |
| GET | `/weather-signals` | Weather adjustments for pincode |
| GET | `/health` | Health check |

---

## 9. Project File Structure

```
xyra/
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   ├── .env.example
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── lib/
│       │   └── utils.ts
│       ├── pages/
│       │   ├── Landing.tsx
│       │   ├── Auth.tsx
│       │   ├── Onboarding.tsx
│       │   ├── ModeSelect.tsx          ← NEW — Static vs Dynamic choice
│       │   └── Dashboard.tsx
│       ├── components/
│       │   ├── ui/
│       │   │   ├── StockAlertCard.tsx
│       │   │   ├── WeatherCard.tsx
│       │   │   ├── EventsPanel.tsx
│       │   │   ├── ForecastChart.tsx
│       │   │   ├── SalesByCategory.tsx
│       │   │   ├── RiskHeatmap.tsx     ← NEW Graph 1
│       │   │   └── SignalBreakdown.tsx ← NEW Graph 2
│       │   └── layout/
│       │       ├── Sidebar.tsx
│       │       └── Header.tsx
│       ├── hooks/
│       │   ├── useWebSocket.ts         ← NEW — live dashboard connection
│       │   ├── useDashboardData.ts
│       │   └── useOnboarding.ts
│       └── services/
│           ├── api.ts                  ← all REST calls
│           └── websocket.ts            ← WebSocket client
│
├── backend/
│   └── prod/
│       └── code/
│           ├── main.py                 ← FastAPI entry point (MISSING — needs creating)
│           ├── requirements.txt
│           ├── .env.example
│           ├── layers/
│           │   ├── __init__.py
│           │   ├── layer1_cleaner.py   ← MISSING — needs creating
│           │   ├── layer1_5_dsp.py     ← MISSING — needs creating
│           │   ├── layer2_forecaster.py
│           │   ├── layer3_classifier.py
│           │   ├── layer4_events.py
│           │   ├── layer5_weather.py
│           │   ├── layer6_output.py
│           │   └── layer7_learning.py
│           ├── dynamic/                ← NEW — dynamic mode modules
│           │   ├── __init__.py
│           │   ├── digital_twin.py     ← SKUDigitalTwin class
│           │   ├── webhook_receiver.py ← POST /api/sale-event handler
│           │   ├── poller.py           ← APScheduler polling job
│           │   └── ws_broadcaster.py   ← WebSocket dashboard stream
│           ├── data/
│           │   ├── sample_store_data.csv
│           │   ├── indian_festival_calendar.json
│           │   ├── pincode_state_map.json
│           │   └── feedback_log.json
│           └── utils/
│               ├── helpers.py
│               └── validators.py
│
├── notebooks/
│   └── XYRA_Analysis.ipynb
│
├── vercel.json
├── README.md
└── SystemArchitecture.png
```

---

## 10. Missing Files — Priority Build Order

| Priority | File | What to build |
|---|---|---|
| P0 | `backend/main.py` | FastAPI app with all endpoints wired |
| P0 | `layers/layer1_cleaner.py` | CSV ingestion and cleaning |
| P0 | `layers/layer1_5_dsp.py` | DSP noise filtering |
| P1 | `dynamic/digital_twin.py` | SKUDigitalTwin class |
| P1 | `dynamic/webhook_receiver.py` | POS webhook handler |
| P1 | `dynamic/poller.py` | APScheduler polling job |
| P1 | `dynamic/ws_broadcaster.py` | WebSocket broadcaster |
| P2 | `pages/ModeSelect.tsx` | Static vs Dynamic mode selection UI |
| P2 | `components/RiskHeatmap.tsx` | New Graph 1 |
| P2 | `components/SignalBreakdown.tsx` | New Graph 2 |
| P2 | `hooks/useWebSocket.ts` | Frontend WebSocket hook |
| P3 | `services/api.ts` | Wire frontend to backend |

---

## 11. Tech Stack

**Frontend**
- React 19, TypeScript 5.8, Vite 6
- TailwindCSS 4, Recharts, Motion, React Router 7
- Lucide React, clsx

**Backend**
- Python 3, FastAPI, Uvicorn
- Pandas, NumPy, SciPy, Prophet, Scikit-learn
- Pydantic, APScheduler, WebSockets
- OpenWeatherMap API, Google Calendar API

---

## 12. Success Metrics

| Metric | Target |
|---|---|
| Stockout reduction | 30–35% within 60 days |
| Forecast MAPE | Below 15% on clean data |
| Reorder acceptance rate | Above 70% by month 2 |
| API response time (full pipeline) | Under 8 seconds for 50 SKUs |
| WebSocket update latency | Under 5 seconds |
| ROI breakeven | 8–10 weeks per store |

---

*XYRA — Predict the rush. Never run out.*