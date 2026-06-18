# System Architecture

## Railway Control System

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE STACK                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐ │
│  │   Nginx      │───▶│  Django/Gunicorn  │───▶│  MySQL 8.0  │ │
│  │  :80 (proxy) │    │  :8000 (3 workers)│    │  :3306      │ │
│  └──────────────┘    └──────────────────┘    └──────────────┘ │
│         │                    │                                  │
│    /static/           /app/ml_models/                          │
│    /media/            delay_model.pkl                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Application Layer Architecture

```
railway_control/          ← Django Project (settings, urls, wsgi)
│
apps/
│
├── authentication/       ← Custom User (RBAC: Admin, Controller, Supervisor)
│   ├── models.py         ← User, UserActivity
│   ├── views.py          ← Login, Register, Profile, Password Change
│   └── forms.py
│
├── trains/               ← Train Management
│   ├── models.py         ← Train (15 type/status fields)
│   ├── views.py          ← CRUD + network data APIs
│   └── management/commands/seed_data.py
│
├── stations/             ← Infrastructure
│   └── models.py         ← Station, Platform, Route, TrackSection
│
├── scheduling/           ← Schedule Engine
│   └── models.py         ← Schedule, TrackOccupancy
│
├── conflicts/            ← Conflict Detection Engine
│   ├── models.py         ← Conflict, Recommendation
│   └── services.py       ← ConflictDetectionEngine (time-space analysis)
│
├── ai_engine/            ← AI Priority Scorer
│   └── services.py       ← PriorityEngine (5-factor weighted scoring)
│
├── ml_prediction/        ← ML Delay Predictor
│   ├── ml/trainer.py     ← RandomForestRegressor training
│   └── ml/predictor.py   ← Inference + risk classification
│
├── simulation/           ← Scenario Simulator
│   └── services.py       ← ScenarioSimulator (cascade analysis)
│
├── analytics/            ← Dashboard & Chart APIs
├── notifications/        ← Alert Centre
└── reporting/            ← PDF / CSV Export
```

---

## Database Schema

```
┌──────────────────┐     ┌───────────────┐     ┌─────────────────┐
│   auth_users     │     │    trains     │     │    stations     │
│──────────────────│     │───────────────│     │─────────────────│
│ id (PK)          │     │ id (PK)       │     │ id (PK)         │
│ username         │     │ train_number  │     │ name            │
│ email            │     │ train_name    │     │ code (UNIQUE)   │
│ role             │     │ train_type    │     │ station_type    │
│ employee_id      │─┐   │ speed         │     │ latitude        │
│ section_assigned │ │   │ priority_level│     │ longitude       │
│ is_on_duty       │ │   │ source_fk ───────▶  │ total_platforms │
└──────────────────┘ │   │ destination_fk───▶  └─────────────────┘
                      │   │ current_status│           │
                      │   │ current_delay │     ┌─────────────────┐
                      │   └───────────────┘     │   platforms     │
                      │          │              │─────────────────│
                      │          │              │ station_fk ─────┘
                      │   ┌──────────────────┐  │ platform_number │
                      │   │    schedules     │  │ status          │
                      │   │──────────────────│  └─────────────────┘
                      │   │ train_fk ────────┘
                      │   │ station_fk        ┌──────────────────┐
                      │   │ platform_fk       │  track_sections  │
                      │   │ track_section_fk──▶──────────────────│
                      │   │ scheduled_date    │ from_station_fk  │
                      │   │ status            │ to_station_fk    │
                      │   │ current_delay     │ status           │
                      │   └──────────────────┘ │ number_of_lines │
                      │                         └──────────────────┘
                      │   ┌──────────────────┐
                      │   │    conflicts     │
                      │   │──────────────────│
                      │   │ conflict_type    │
                      │   │ severity         │
                      │   │ train_a_fk       │
                      │   │ train_b_fk       │
                      │   │ station_fk       │
                      │   │ track_section_fk │
                      │   │ status           │
                      │   └──────────────────┘
                      │
                      │   ┌──────────────────────┐
                      └──▶│  delay_predictions   │
                          │──────────────────────│
                          │ train_fk             │
                          │ predicted_delay_min  │
                          │ risk_level           │
                          │ confidence_score     │
                          │ weather_code         │
                          │ traffic_density      │
                          └──────────────────────┘
```

---

## ML Pipeline

```
Raw Features (9)
     │
     ▼
┌─────────────────────────────────────┐
│     scikit-learn Pipeline           │
│                                     │
│  StandardScaler                     │
│       │                             │
│       ▼                             │
│  RandomForestRegressor              │
│  ├── n_estimators: 200              │
│  ├── max_depth: 12                  │
│  ├── min_samples_split: 5           │
│  ├── min_samples_leaf: 2            │
│  └── max_features: sqrt             │
└─────────────────────────────────────┘
     │
     ▼
Predicted Delay (minutes)
     │
     ▼
Risk Classification
  ├── LOW      (0–10 min)
  ├── MEDIUM   (10–30 min)
  ├── HIGH     (30–60 min)
  └── CRITICAL (>60 min)
```

**Feature Importance (trained model):**

| Feature | Importance |
|---------|-----------|
| weather_code | 34.1% |
| traffic_density | 27.6% |
| section_congestion | 9.8% |
| historical_avg_delay | 7.6% |
| day_of_week | 7.0% |
| is_peak_hour | 5.8% |
| train_type_encoded | 3.3% |
| scheduled_distance | 3.0% |
| hour_of_day | 1.8% |

---

## AI Priority Engine

```
Train Object
     │
     ▼
┌─────────────────────────────────────────────┐
│           PriorityEngine.calculate()        │
│                                             │
│  Factor 1: Train Type Score    × 0.30       │
│  Factor 2: Delay Urgency       × 0.25       │
│  Factor 3: Operational Priority × 0.20      │
│  Factor 4: Speed Capability    × 0.15       │
│  Factor 5: Route Importance    × 0.10       │
│                                             │
│  TOTAL = Σ(score × weight)  ∈ [0, 10]      │
└─────────────────────────────────────────────┘
     │
     ▼
Action Classification
  ≥ 8.5 → IMMEDIATE PRIORITY
  ≥ 7.0 → HIGH PRIORITY
  ≥ 5.5 → NORMAL OPERATION
  ≥ 3.5 → LOW PRIORITY — CAN HOLD
  <  3.5 → DEFER
```

---

## Conflict Detection Algorithm

```
For each scheduled_date:
  1. TRACK CONFLICTS
     ├── Group schedules by track_section
     └── For each section: check if time windows overlap (buffer=0 min)

  2. PLATFORM CONFLICTS
     ├── Group schedules by platform
     └── For each platform: check if time windows overlap (buffer=5 min)

  3. CROSSING CONFLICTS
     ├── Filter TrackSection.number_of_lines == 1
     └── For each single-line section: ≥2 trains in overlapping windows → CRITICAL

  4. HEADWAY VIOLATIONS
     ├── For each section: sort schedules by scheduled_arrival
     └── Check gap between consecutive trains < MIN_HEADWAY (10 min)
```

---

## Request Flow

```
Browser Request
     │
     ▼
Nginx (:80)
     │  ├── /static/ → served directly from filesystem
     │  └── /        → proxy_pass to Gunicorn
     ▼
Gunicorn (:8000, 3 workers)
     │
     ▼
Django Middleware Stack
  SecurityMiddleware → WhiteNoise → SessionMiddleware
  → CorsMiddleware → CsrfViewMiddleware
  → AuthenticationMiddleware → MessageMiddleware
     │
     ▼
URL Router (railway_control/urls.py)
     │  ├── /auth/     → authentication.urls
     │  ├── /trains/   → trains.urls
     │  ├── /api/*/    → *.api_urls
     │  └── ...
     ▼
View → Service Layer → Model → MySQL
     │
     ▼
Template (HTML) or JsonResponse (API)
     │
     ▼
Browser (Chart.js, Cytoscape.js, app.js)
```

---

## Technology Decisions

| Concern | Choice | Reason |
|---------|--------|--------|
| Web framework | Django 4.2 | Batteries included, ORM, admin |
| Database | MySQL 8.0 | Production-grade, relational constraints |
| ML | scikit-learn RF | Interpretable, fast inference, good for tabular data |
| Network viz | Cytoscape.js | Purpose-built graph library with physics layout |
| Charts | Chart.js | Lightweight, responsive, excellent docs |
| CSS | Custom (no Bootstrap UI) | Bespoke dark/light theme, glassmorphism |
| Auth | Custom User + Session + JWT | RBAC requirement with API support |
| Container | Docker + Gunicorn + Nginx | Industry-standard production stack |

