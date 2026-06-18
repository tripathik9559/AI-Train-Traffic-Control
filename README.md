# 🚆 AI-Assisted Train Traffic Control & Section Throughput Optimization System

**Final Year B.Tech Project | BBDNIIT Lucknow | 2024–2025**  
**Branch:** Computer Science & Engineering  
**Tech Stack:** Django · MySQL · Scikit-Learn · Cytoscape.js · Chart.js · Docker

---

## 📋 Project Overview

A production-grade intelligent railway traffic management and decision-support system that helps section controllers:

- Manage train movements across a realistic simulated railway section
- Detect operational conflicts (track, platform, crossing, headway violations)
- Optimize train precedence using an AI-based multi-factor priority scoring engine
- Predict delays using a trained Random Forest Regressor (R² = 0.83, MAE = 5.3 min)
- Run disruption scenario simulations and compute cascade impacts
- Visualize the railway network interactively with Cytoscape.js
- Generate automated daily, conflict, and train-performance reports (PDF + CSV)

---

## 🏗️ Module Breakdown

| # | Module | Description |
|---|--------|-------------|
| 1 | Authentication & Roles | Login, register, RBAC (Admin / Section Controller / Supervisor) |
| 2 | Train Management | Full CRUD, search, filter, status updates |
| 3 | Station & Route Management | Stations, platforms, routes, track sections |
| 4 | Railway Network Visualizer | Interactive Cytoscape.js graph with zoom/pan/click |
| 5 | Train Scheduling Engine | Schedule CRUD, occupancy tracking, delay recording |
| 6 | Conflict Detection Engine | Automatic time-space analysis for 4 conflict types |
| 7 | AI Priority Engine | Weighted 5-factor scoring, rank at conflict point |
| 8 | ML Delay Prediction | Random Forest with 9 features, visual breakdown |
| 9 | Scenario Simulation | 8 scenario types, cascade analysis, recovery plan |
| 10 | Real-Time Operations Simulator | Animated live train positions and section heatmap |
| 11 | Analytics Dashboard | 6 Chart.js charts, live KPIs, section heatmap |
| 12 | Notification Centre | Broadcast alerts, conflict notifications, read/unread |
| 13 | Reporting System | Daily/conflict/train reports with PDF + CSV export |

---

## 🚀 Quick Start (Docker — Recommended)

### Prerequisites
- Docker Desktop 24+
- Docker Compose v2

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/tripathik9559/railway-control-system.git
cd railway-control-system

# 2. Copy environment file
cp .env.example .env
# Edit .env if needed (defaults work out of the box)

# 3. Start all services
docker-compose up --build

# 4. Open in browser
# App:   http://localhost:80
# Admin: http://localhost:8000/admin/
```

The entrypoint script automatically:
- Waits for MySQL to be ready
- Runs all migrations
- Trains the ML model (first run ~10 seconds)
- Seeds demo data (stations, trains, conflicts, notifications)

### Demo Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@2024` |
| Section Controller | `controller1` | `Pass@2024` |
| Section Controller | `controller2` | `Pass@2024` |

---

## 🛠️ Local Development (Without Docker)

### Requirements
- Python 3.11+
- MySQL 8.0 (or SQLite for quick dev)

### Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# For SQLite dev (no MySQL needed):
# Set DB_ENGINE=django.db.backends.sqlite3
# Set DB_NAME=./db_dev.sqlite3

# 4. Run migrations
python manage.py migrate --run-syncdb

# 5. Train ML model
python manage.py train_ml_model

# 6. Load seed data
python manage.py seed_data

# 7. Start development server
python manage.py runserver
```

---

## 🧪 Running Tests

```bash
python manage.py test apps
```

---

## 📁 Project Structure

```
railway_control/
├── apps/
│   ├── authentication/     # Custom User model, login, RBAC
│   ├── trains/             # Train CRUD + network visualizer
│   ├── stations/           # Stations, platforms, routes, track sections
│   ├── scheduling/         # Schedule engine, occupancy tracking
│   ├── conflicts/          # Conflict detection engine + services
│   ├── ai_engine/          # AI priority scoring engine
│   ├── ml_prediction/      # Random Forest delay predictor
│   │   └── ml/             # trainer.py + predictor.py
│   ├── simulation/         # Scenario simulation engine
│   ├── analytics/          # Dashboard KPIs + chart APIs
│   ├── notifications/      # Notification centre + context processor
│   └── reporting/          # PDF/CSV report generation
├── railway_control/        # Django project config (settings, urls, wsgi)
├── templates/              # All HTML templates (36 files)
├── static/
│   ├── css/main.css        # Design system (dark/light, glassmorphism)
│   └── js/                 # app.js + charts.js
├── ml_models/              # Saved .pkl model files
├── data/                   # Sample CSV datasets
├── scripts/
│   ├── entrypoint.sh       # Docker startup script
│   ├── init.sql            # MySQL DB initialization
│   └── nginx.conf          # Nginx reverse proxy config
├── docs/
│   └── ARCHITECTURE.md     # System architecture diagrams
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🤖 AI Priority Engine

The priority score is computed using 5 weighted factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Train Type | 30% | Vande Bharat/Rajdhani score 10, Freight scores 2 |
| Delay Urgency | 25% | Scaled 0–10 based on current delay minutes |
| Operational Priority | 20% | Admin-set priority level (1–5) scaled to 10 |
| Speed Capability | 15% | Max speed normalized to 0–10 |
| Route Importance | 10% | Major city-pair routes score higher |

Trains with score ≥ 8.5 receive **IMMEDIATE PRIORITY**; score < 3.5 means **DEFER**.

---

## 🧠 ML Delay Prediction

**Algorithm:** Random Forest Regressor (200 estimators, max_depth=12)

**Features (9):**
1. `train_type_encoded` — categorical type (0–8)
2. `day_of_week` — 0 (Mon) to 6 (Sun)
3. `hour_of_day` — 0–23
4. `weather_code` — 0=Clear, 1=Light Rain, 2=Heavy Rain, 3=Fog, 4=Extreme
5. `traffic_density` — 0.0–1.0
6. `historical_avg_delay` — minutes
7. `section_congestion` — 0.0–1.0
8. `is_peak_hour` — binary
9. `scheduled_distance` — km

**Performance on 5000 synthetic samples:**
- R² = 0.84
- MAE = 5.3 minutes
- RMSE = 7.0 minutes
- 5-fold Cross-Val R² = 0.83

Risk classification: LOW (<10 min), MEDIUM (10–30), HIGH (30–60), CRITICAL (>60)

---

## 🐳 Docker Services

| Service | Image | Port | Description |
|---------|-------|------|-------------|
| `db` | mysql:8.0 | 3307 | MySQL database |
| `web` | custom | 8000 | Django + Gunicorn |
| `nginx` | nginx:alpine | 80 | Reverse proxy |

---

## 🔌 REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/trains/` | GET | List all active trains |
| `/api/trains/<id>/status/` | POST | Update train status/delay |
| `/api/stations/` | GET | All stations JSON |
| `/api/stations/sections/` | GET | All track sections |
| `/api/stations/sections/<id>/status/` | POST | Update section status |
| `/api/scheduling/today/` | GET | Today's schedules |
| `/api/conflicts/detect/` | POST | Run conflict detection |
| `/api/conflicts/report/` | GET | Conflict stats report |
| `/api/ai-engine/rank/` | POST | Rank trains by priority |
| `/api/ai-engine/priority/<id>/` | GET | Single train priority score |
| `/api/ml/predict/` | POST | Predict delay |
| `/api/ml/model-info/` | GET | Model metadata |
| `/api/ml/retrain/` | POST | Retrain ML model |
| `/api/simulation/run/` | POST | Run scenario simulation |
| `/api/simulation/state/` | GET | Live simulator state |
| `/api/analytics/delay-trend/` | GET | 14-day delay trend |
| `/api/analytics/throughput/` | GET | Hourly throughput chart |
| `/api/analytics/kpis/` | GET | Live KPI summary |
| `/api/notifications/unread-count/` | GET | Unread count |

---

## 🗄️ Database Schema (14 Tables)

`auth_users` · `auth_user_activities` · `trains` · `stations` · `platforms` · `routes` · `track_sections` · `schedules` · `track_occupancies` · `conflicts` · `recommendations` · `delay_predictions` · `simulations` · `simulation_results` · `notifications` · `analytics_snapshots` · `reports`

---

## 👨‍💻 Authors

**Kartikey Tripathi** — Backend, ML, DevOps  
GitHub: [@tripathik9559](https://github.com/tripathik9559)  
Institution: BBDNIIT Lucknow, B.Tech CSE 2022–2026

---

## 📜 License

MIT License — Free to use for academic and portfolio purposes.
