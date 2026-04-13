# FLUX — Product Requirements Document
> *Predict the rush. Never run out.*

**Version:** 1.0  
**Domain:** Retail Supply Chain Resilience  
**Stack:** Python · FastAPI · Prophet · Scikit-learn · Pandas · OpenWeatherMap API  
**Cost:** ₹0 (all free-tier tools)

---

## 1. Product Overview

FLUX is an AI-powered retail supply chain resilience backend that ingests a store's historical sales CSV, cleans and filters the data, forecasts demand using ML, classifies product risk levels, overlays local event and weather signals, and outputs actionable reorder recommendations — all via REST API endpoints.

It is purpose-built for small and mid-size Indian retailers who cannot afford enterprise tools like Blue Yonder or Oracle SCM.

---

## 2. Problem Statement

- 15M+ small/mid retailers in India use manual stock checks
- ₹1.2 Trillion lost annually to stockouts and dead inventory
- Zero affordable AI-native tools exist for this segment
- Demand spikes from festivals, weather, and local events go completely undetected

---

## 3. Goals

- Predict demand spikes 7–30 days ahead per product SKU
- Classify each product as 🔴 Critical / 🟡 Warning / 🟢 Safe
- Generate plain-text reorder recommendations with quantities and dates
- Learn from manager feedback to improve future predictions
- Expose all functionality as clean REST API endpoints

---

## 4. Non-Goals (MVP Scope Limit)

- No real-time POS integration (CSV upload only for MVP)
- No mobile app (API-first; frontend built separately)
- No payment processing or vendor management portal
- No multi-tenant auth system (single store per deployment for MVP)

---

## 5. System Architecture

```
[Store Manager]
      │
      ▼ POST /upload-csv
[Layer 1 — Data Ingestion & Cleaning]
      │  pandas · numpy
      │  - column detection, null handling, deduplication
      ▼
[Layer 1.5 — DSP Noise Filtering]
      │  scipy · statsmodels
      │  - rolling average smoothing
      │  - outlier removal (IQR / z-score)
      │  - seasonal decomposition (STL)
      ▼
[Layer 2 — Demand Forecasting]
      │  prophet
      │  - per-SKU 7-day and 30-day forecast
      │  - confidence intervals
      │  - Indian festival & holiday regressors
      ▼
[Layer 3 — Risk Classification]
      │  scikit-learn · rule engine
      │  - days_of_stock / forecast_multiplier
      │  - 🔴 Critical / 🟡 Warning / 🟢 Safe
      │  - reorder quantity calculation
      ▼
[Layer 4 — Event Signals]
      │  hardcoded Indian festival calendar JSON
      │  + Google Calendar API (free tier)
      │  - pincode → state → upcoming events
      │  - spike multiplier per product category
      ▼
[Layer 5 — Weather Signals]
      │  OpenWeatherMap API (free tier)
      │  - 7-day forecast by pincode
      │  - rain / heatwave flags → demand adjustments
      ▼
[Layer 6 — Output & Recommendations]
      │  structured JSON + plain-text briefing
      │  - risk dashboard per SKU
      │  - top 5 reorder actions
      │  - weekly manager briefing paragraph
      ▼
[Layer 7 — Continuous Learning]
      │  feedback loop via POST /feedback
      │  - manager accepts / rejects recommendations
      │  - stores correction data in feedback_log.json
      │  - retrains multipliers based on accuracy history
      ▼
[FastAPI Endpoints — REST API]
```

---

## 6. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload-csv` | Upload store sales CSV, triggers full pipeline |
| GET | `/dashboard` | Returns risk-classified product list |
| GET | `/forecast/{product_id}` | Returns 30-day forecast for one SKU |
| GET | `/recommendations` | Returns top reorder actions with quantities |
| GET | `/briefing` | Returns plain-text weekly manager summary |
| POST | `/event-signals` | Input pincode, get upcoming event multipliers |
| GET | `/weather-signals` | Get weather-based demand adjustments by pincode |
| POST | `/feedback` | Manager submits accept/reject on recommendation |
| GET | `/learning-stats` | View model accuracy and feedback history |
| GET | `/health` | Health check |

---

## 7. Layer Specifications

### Layer 1 — Data Ingestion & Cleaning
**Input:** Raw CSV (any format)  
**Output:** Clean, standardized Pandas DataFrame  
**Operations:**
- Auto-detect columns: date, product_name, units_sold, current_stock, price
- Normalize date formats (DD/MM/YYYY, ISO, MM-DD-YY)
- Forward-fill missing stock values
- Fill missing sales with category median
- Remove duplicates and negative values
- Flag and quarantine anomalous rows (>5σ from mean)

---

### Layer 1.5 — DSP Noise Filtering
**Input:** Clean DataFrame from Layer 1  
**Output:** Smoothed, decomposed time series per SKU  
**Operations:**
- Rolling average smoothing (window=7 days)
- IQR-based outlier clipping (extreme one-off spikes removed before forecasting)
- Z-score filtering (|z| > 3.0 flagged as noise)
- STL decomposition: separates trend + seasonality + residual
- Residual stored separately for anomaly detection in Layer 3

**Why this layer matters:** Without noise filtering, a single promotional sale or data entry error can corrupt Prophet's forecast by 30–40%. DSP filtering ensures the ML model trains on signal, not noise.

---

### Layer 2 — Demand Forecasting (Prophet)
**Input:** Smoothed time series per SKU  
**Output:** 7-day and 30-day forecast with confidence intervals  
**Operations:**
- Individual Prophet model per SKU
- Indian public holiday regressor added
- Weekly + yearly seasonality enabled
- Confidence interval: 80% (yhat_lower, yhat_upper)
- Spike score = yhat / rolling_avg_28d (multiplier above baseline)

---

### Layer 3 — Risk Classification
**Input:** Forecast output + current stock levels  
**Output:** Risk label + reorder quantity per SKU  
**Logic:**
```
days_of_stock = current_stock / avg_daily_sales_7d
effective_days = days_of_stock / spike_multiplier

🔴 CRITICAL  → effective_days <= 3
🟡 WARNING   → effective_days <= 7
🟢 SAFE      → effective_days > 7

reorder_qty = ceil((predicted_demand_14d * lead_time_buffer) - current_stock)
```

---

### Layer 4 — Event Signals
**Input:** Store pincode  
**Output:** Upcoming events + category spike multipliers  
**Data Sources:**
- `indian_festival_calendar.json` (hardcoded, covers 50+ events)
- Google Calendar API free tier (national + state holidays)
- Pincode → State mapping for regional festivals

**Spike multipliers by category:**
```json
{
  "Pongal":     {"grains": 1.6, "sweets": 2.1, "beverages": 1.3},
  "IPL_match":  {"beverages": 1.8, "snacks": 1.9, "dairy": 1.1},
  "Diwali":     {"sweets": 2.5, "oil": 1.7, "snacks": 1.8},
  "Heatwave":   {"cold_drinks": 2.2, "ors": 1.9, "ice_cream": 1.6}
}
```

---

### Layer 5 — Weather Signals
**Input:** Pincode  
**Output:** Weather-adjusted demand multipliers  
**API:** OpenWeatherMap free tier (1000 calls/day)  
**Rules:**
- Rain > 5mm → footfall -15% → reduce all categories by 0.85×
- Temp > 38°C → cold drinks +120%, ORS +90%, dairy -10%
- Temp < 18°C → hot beverages +60%, soups +40%

---

### Layer 6 — Output & Recommendations
**Input:** All layer outputs merged  
**Output:** Structured JSON dashboard + plain-text briefing  
**Contents:**
- Per-SKU: risk_level, days_to_stockout, reorder_qty, reorder_by_date, reason
- Top 5 urgent reorder actions
- Plain-text briefing: "Product X needs reorder by Thursday due to Pongal spike. Current stock covers only 2 days."
- Visualizations: forecast chart, risk heatmap (returned as base64 PNG)

---

### Layer 7 — Continuous Learning
**Input:** Manager feedback via `/feedback` endpoint  
**Output:** Updated accuracy log + adjusted spike multipliers  
**Operations:**
- Stores: product_id, recommended_qty, actual_qty_ordered, accepted (bool), timestamp
- Calculates rolling accuracy score per product category
- Adjusts event spike multipliers based on over/under-prediction history
- Weekly recalibration job (APScheduler)
- Accuracy report available via `/learning-stats`

---

## 8. Data Schema

### Input CSV (expected columns)
```
date, product_name, product_id, units_sold, current_stock, category, price, supplier_id
```

### Feedback Payload
```json
{
  "product_id": "SKU_001",
  "recommendation_id": "REC_20260413_001",
  "accepted": true,
  "actual_qty_ordered": 120,
  "manager_note": "Ordered slightly more due to upcoming school reopening"
}
```

---

## 9. File Structure

```
flux/
├── main.py                          ← FastAPI app, all route definitions
├── PRD.md                           ← this file
├── requirements.txt
├── notebooks/
│   └── flux_analysis.ipynb          ← full pipeline as Jupyter notebook
├── layers/
│   ├── __init__.py
│   ├── layer1_cleaner.py            ← data ingestion & cleaning
│   ├── layer1_5_dsp.py              ← noise filtering & decomposition
│   ├── layer2_forecaster.py         ← Prophet forecasting
│   ├── layer3_classifier.py         ← risk classification
│   ├── layer4_events.py             ← event signals
│   ├── layer5_weather.py            ← weather signals
│   ├── layer6_output.py             ← recommendations & briefing
│   └── layer7_learning.py           ← feedback & continuous learning
├── data/
│   ├── sample_store_data.csv        ← demo data (Chennai grocery store)
│   ├── indian_festival_calendar.json
│   ├── pincode_state_map.json
│   └── feedback_log.json            ← persisted feedback store
└── utils/
    ├── validators.py
    └── helpers.py
```

---

## 10. Requirements

```
fastapi
uvicorn
pandas
numpy
prophet
scikit-learn
scipy
statsmodels
matplotlib
seaborn
plotly
requests
python-multipart
openpyxl
apscheduler
python-dotenv
```

---

## 11. Environment Variables

```
OPENWEATHER_API_KEY=your_free_key_here
GOOGLE_CALENDAR_API_KEY=your_free_key_here   # optional
STORE_PINCODE=600001
LEAD_TIME_DAYS=2
```

---

## 12. Success Metrics

| Metric | Target |
|--------|--------|
| Forecast MAPE | < 15% on clean data |
| Risk classification accuracy | > 85% after 30 days of feedback |
| API response time (full pipeline) | < 8 seconds for 50 SKUs |
| Reorder recommendation acceptance rate | > 70% by month 2 |
| Stockout reduction (pilot stores) | 30–35% within 60 days |

---

*FLUX — Predict the rush. Never run out.*