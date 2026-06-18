# REST API Documentation

## Railway Control System — API Reference

Base URL: `http://localhost:8000`  
Authentication: Session (cookie) or JWT Bearer token  
Content-Type: `application/json`

---

## Authentication

All API endpoints require authentication. Use session cookie (after web login) or JWT.

### Obtain JWT Token

```
POST /api/token/
```

**Request:**
```json
{ "username": "admin", "password": "Admin@2024" }
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

Include in requests:
```
Authorization: Bearer <access_token>
```

---

## Train Management

### GET /api/trains/

List all active trains.

**Response:**
```json
{
  "trains": [
    {
      "id": 1,
      "number": "12301",
      "name": "Howrah Rajdhani Express",
      "type": "RAJDHANI",
      "status": "RUNNING",
      "delay": 0,
      "priority": 5,
      "source": "NDLS",
      "destination": "HWH",
      "type_color": "#e74c3c"
    }
  ],
  "count": 15
}
```

### POST /api/trains/{id}/status/

Update a train's status and delay.

**Request:**
```json
{
  "status": "DELAYED",
  "delay": 25
}
```

**Response:**
```json
{ "success": true, "status": "DELAYED", "delay": 25 }
```

**Status values:** `SCHEDULED`, `RUNNING`, `DELAYED`, `ARRIVED`, `CANCELLED`, `HELD`, `MAINTENANCE`

---

## Station & Route Management

### GET /api/stations/

All active stations.

**Response:**
```json
{
  "stations": [
    {
      "id": 1, "code": "LKO", "name": "Lucknow Charbagh",
      "lat": 26.8467, "lng": 80.9462,
      "type": "MAJOR", "platforms": 9
    }
  ]
}
```

### GET /api/stations/sections/

All track sections with status.

**Response:**
```json
{
  "sections": [
    {
      "code": "LKO-ETW-01", "name": "LKO-ETW Section",
      "from_code": "LKO", "to_code": "ETW",
      "status": "CLEAR", "color": "#10b981",
      "length": 110.0, "lines": 2
    }
  ]
}
```

### POST /api/stations/sections/{id}/status/

Update track section status.

**Request:**
```json
{ "status": "BLOCKED" }
```

**Status values:** `CLEAR`, `OCCUPIED`, `BLOCKED`, `MAINTENANCE`, `SIGNAL_FAILURE`

**Response:**
```json
{ "success": true, "status": "BLOCKED", "color": "#ef4444" }
```

---

## Scheduling

### GET /api/scheduling/today/

Today's scheduled train movements.

**Response:**
```json
{
  "schedules": [
    {
      "id": 1,
      "train_number": "12301",
      "train_name": "Howrah Rajdhani Express",
      "station_code": "LKO",
      "station_name": "Lucknow Charbagh",
      "scheduled_arrival": "14:30",
      "scheduled_departure": "14:35",
      "current_delay": 0,
      "status": "RUNNING",
      "platform": "2"
    }
  ],
  "date": "2025-06-02"
}
```

### POST /api/scheduling/{id}/time/

Record actual arrival or departure time.

**Request:**
```json
{ "type": "arrival" }
```
or
```json
{ "type": "departure" }
```

**Response:**
```json
{ "success": true, "delay": 12, "status": "ARRIVED" }
```

---

## Conflict Detection

### POST /api/conflicts/detect/

Run full conflict detection for today's schedules.

**Response:**
```json
{
  "success": true,
  "detected": 3,
  "message": "3 conflict(s) detected for 2025-06-02."
}
```

### GET /api/conflicts/report/?from=2025-05-26&to=2025-06-02

Conflict statistics for a date range.

**Response:**
```json
{
  "total": 18,
  "by_type": { "TRACK": 8, "PLATFORM": 5, "CROSSING": 2, "HEADWAY": 3 },
  "by_severity": { "CRITICAL": 2, "HIGH": 6, "MEDIUM": 7, "LOW": 3 },
  "by_status": { "RESOLVED": 12, "ACTIVE": 4, "ACKNOWLEDGED": 2 },
  "resolved": 12,
  "active": 4,
  "resolution_rate": 66.7
}
```

### POST /api/conflicts/{id}/resolve/

Mark a conflict as resolved.

**Request:**
```json
{ "notes": "Trains given crossing order per AI recommendation." }
```

**Response:**
```json
{ "success": true, "message": "Conflict #5 resolved." }
```

### POST /api/conflicts/{id}/acknowledge/

Acknowledge a conflict (set to acknowledged state).

**Response:**
```json
{ "success": true }
```

---

## AI Priority Engine

### POST /api/ai-engine/rank/

Rank multiple trains by AI priority score at a conflict point.

**Request:**
```json
{ "train_ids": [1, 3, 7] }
```

**Response:**
```json
{
  "success": true,
  "ranked": [
    {
      "rank": 1,
      "rank_label": "🚀 FIRST PRIORITY",
      "train_number": "12301",
      "train_name": "Howrah Rajdhani Express",
      "total_score": 8.73,
      "action": "IMMEDIATE PRIORITY",
      "action_detail": "Clear all crossings...",
      "action_color": "#e74c3c",
      "scores": {
        "train_type": 10.0,
        "delay_urgency": 8.0,
        "operational_priority": 10.0,
        "speed_capability": 7.22,
        "route_importance": 9.0
      }
    },
    {
      "rank": 2,
      "rank_label": "⚡ SECOND PRIORITY",
      "train_number": "14015",
      "train_name": "Sadhbhavna Express",
      "total_score": 5.41,
      "action": "NORMAL OPERATION",
      "action_detail": "Follow standard protocol.",
      "action_color": "#3b82f6",
      "scores": { ... }
    }
  ]
}
```

### GET /api/ai-engine/priority/{train_id}/

Get priority score for a single train.

**Response:**
```json
{
  "train_id": 1,
  "train_number": "12301",
  "total_score": 8.73,
  "score_percentage": 87.3,
  "action": "IMMEDIATE PRIORITY",
  "action_detail": "Train 12301 requires immediate precedence...",
  "action_color": "#e74c3c",
  "scores": {
    "train_type": 10.0,
    "delay_urgency": 8.0,
    "operational_priority": 10.0,
    "speed_capability": 7.22,
    "route_importance": 9.0
  },
  "delay_minutes": 25
}
```

---

## ML Delay Prediction

### POST /api/ml/predict/

Predict delay for given operational features.

**Request:**
```json
{
  "train_id": 1,
  "train_type_encoded": 7,
  "day_of_week": 4,
  "hour_of_day": 9,
  "weather_code": 1,
  "traffic_density": 0.6,
  "historical_avg_delay": 15.0,
  "section_congestion": 0.4,
  "is_peak_hour": 1,
  "scheduled_distance": 497.0
}
```

**Response:**
```json
{
  "success": true,
  "prediction_id": 42,
  "train_number": "12301",
  "predicted_delay_minutes": 34.2,
  "risk_level": "HIGH",
  "risk_color": "#f97316",
  "risk_icon": "🔶",
  "confidence_pct": 82.0,
  "breakdown": [
    { "feature": "Weather (Light Rain)", "importance": 34.1, "contribution": 11.7 },
    { "feature": "Traffic Density (60%)", "importance": 27.6, "contribution": 9.4 },
    { "feature": "Section Congestion (40%)", "importance": 9.8, "contribution": 3.3 }
  ],
  "model_version": "v1.0"
}
```

**Weather codes:** 0=Clear, 1=Light Rain, 2=Heavy Rain, 3=Dense Fog, 4=Extreme

**Risk levels:** `LOW` (<10 min), `MEDIUM` (10–30 min), `HIGH` (30–60 min), `CRITICAL` (>60 min)

### GET /api/ml/model-info/

Get ML model metadata and performance metrics.

**Response:**
```json
{
  "ready": true,
  "version": "v1.0",
  "trained_at": "2025-06-02T14:30:00",
  "r2_score": 0.8358,
  "mae": 5.341,
  "rmse": 7.018,
  "cv_score": 0.829,
  "feature_importances": {
    "weather_code": 0.3414,
    "traffic_density": 0.2759,
    "section_congestion": 0.0976,
    "historical_avg_delay": 0.0764,
    "day_of_week": 0.0702,
    "is_peak_hour": 0.0577,
    "train_type_encoded": 0.0326,
    "scheduled_distance": 0.0298,
    "hour_of_day": 0.0184
  }
}
```

### POST /api/ml/retrain/

Retrain the ML model with fresh synthetic data. Admin only.

**Response:**
```json
{
  "success": true,
  "metrics": {
    "r2_score": 0.841,
    "mean_absolute_error": 5.21,
    "root_mean_squared_error": 6.89,
    "cross_val_score": 0.835,
    "training_samples": 4000
  }
}
```

### GET /api/ml/train/{train_id}/

Quick prediction for a specific train using current conditions.

**Response:**
```json
{
  "train_number": "12301",
  "train_name": "Howrah Rajdhani Express",
  "predicted_delay_minutes": 28.4,
  "risk_level": "MEDIUM",
  "confidence_pct": 78.5,
  "model_version": "v1.0"
}
```

---

## Scenario Simulation

### POST /api/simulation/run/

Create and execute a scenario simulation.

**Request:**
```json
{
  "name": "Monsoon Delay Cascade",
  "scenario_type": "HEAVY_RAIN",
  "delay_minutes": 45,
  "duration_hours": 3.0,
  "train_ids": [1, 2, 3, 4]
}
```

**Scenario types:** `TRAIN_DELAY`, `PLATFORM_FAILURE`, `MAINTENANCE_BLOCK`, `SIGNAL_FAILURE`, `HEAVY_RAIN`, `ROUTE_CONGESTION`, `MASS_DELAY`, `CUSTOM`

**Response:**
```json
{
  "success": true,
  "simulation_id": 7,
  "status": "COMPLETED",
  "throughput_impact": 38.5,
  "trains_affected": 12,
  "recovery_time": 94,
  "summary": "SIMULATION RESULT — Monsoon Delay Cascade\n...",
  "recommendations": "1. Enforce speed restrictions...",
  "results": [
    {
      "train_number": "12301",
      "train_name": "Howrah Rajdhani",
      "simulated_delay": 45,
      "cascaded_delay": 18,
      "status_change": "DELAYED",
      "platform_conflict": false,
      "track_conflict": false,
      "recommended_action": "Hold at LKO..."
    }
  ]
}
```

### GET /api/simulation/state/

Get current real-time state for the simulator.

**Response:**
```json
{
  "timestamp": "2025-06-02T17:30:00+05:30",
  "trains": [
    {
      "id": 1, "number": "12301", "name": "Howrah Rajdhani",
      "type": "RAJDHANI", "status": "RUNNING",
      "delay": 0, "speed": 112.3, "progress": 42.7,
      "priority": 5, "type_color": "#e74c3c",
      "source": "NDLS", "destination": "HWH"
    }
  ],
  "sections": [
    {
      "code": "LKO-ETW-01", "name": "LKO-ETW Section",
      "status": "OCCUPIED", "color": "#f59e0b",
      "from": "LKO", "to": "ETW"
    }
  ]
}
```

---

## Analytics

### GET /api/analytics/kpis/

Live KPI summary for dashboard.

**Response:**
```json
{
  "total_trains": 15,
  "running_trains": 8,
  "delayed_trains": 4,
  "cancelled_trains": 0,
  "on_time_trains": 11,
  "avg_delay": 12.3,
  "active_conflicts": 2,
  "total_conflicts_today": 5,
  "resolved_conflicts_today": 3,
  "punctuality_rate": 73.3,
  "total_stations": 12,
  "total_sections": 10,
  "section_availability": 80.0
}
```

### GET /api/analytics/delay-trend/

Average delay for the last 14 days.

**Response:**
```json
{
  "labels": ["20 May", "21 May", "22 May", "..."],
  "data": [8.2, 12.5, 7.3, 15.8, 9.1, "..."]
}
```

### GET /api/analytics/throughput/

Hourly train throughput for today (24 data points).

### GET /api/analytics/train-types/

Train count by type for doughnut chart.

### GET /api/analytics/conflicts/

Conflict count by type for chart.

### GET /api/analytics/platforms/

Platform utilization percentage by station.

### GET /api/analytics/sections/

All section statuses for heatmap display.

---

## Notifications

### GET /api/notifications/unread-count/

**Response:**
```json
{ "count": 3 }
```

### POST /api/notifications/{id}/read/

Mark a notification as read.

**Response:**
```json
{ "success": true }
```

### POST /api/notifications/mark-all/

Mark all notifications as read.

**Response:**
```json
{ "success": true }
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 302 | Redirect (requires authentication) |
| 400 | Bad Request — invalid parameters |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 500 | Internal Server Error |

---

## Error Response Format

```json
{
  "error": "Descriptive error message here",
  "detail": "Optional technical detail"
}
```

---

*API documentation for Railway Control System v1.0 — BBDNIIT Final Year Project 2025*
