# 🚂 Indian Railways AI Control System

<div align="center">

![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-REST%20API-red?style=for-the-badge&logo=django&logoColor=white)
![SIH](https://img.shields.io/badge/Smart%20India%20Hackathon-2025-FF6B00?style=for-the-badge)

<br/>

> **A production-grade, AI-powered Railway Traffic Control & Operations Management Platform**  
> Built with Django 4.2 · Machine Learning · Real-time Dashboards · Multi-role Access

</div>

---

> [!WARNING]
> ## 🚧 WORK IN PROGRESS — DO NOT USE IN PRODUCTION 🚧
>
> **This project is actively under development. Features are incomplete, APIs may change without notice, and the codebase is being refactored regularly.**
>
> **I push updates daily as I build and improve this system — this is a live, evolving project.**
>
> ⚠️ Not ready for real-world railway operations. For educational/portfolio purposes only.

---

## 📌 What Is This?

A **comprehensive railway operations management system** designed to simulate how Indian Railways could leverage AI and machine learning for real-time traffic control, delay prediction, conflict resolution, and scheduling optimization.

Originally conceived as a **Smart India Hackathon (SIH) 2025** problem statement, this project is now being independently developed and expanded as a **B.Tech Final Year Project** at BBDNIIT, Lucknow — engineered well beyond the hackathon prototype stage, toward production-grade standards.

---

## ✨ Features

### 🤖 AI / Machine Learning
- **Delay Prediction Engine** — Random Forest Regressor (R² = 0.84) trained on Indian Railways data
- **AI Priority Engine** — Smart train prioritization based on delay, type, and route importance
- **Conflict Detection** — Automated detection of scheduling and track conflicts
- **What-If Scenario Analysis** — Simulate impact of rain, signal failure, track closure, breakdowns
- **Feature Importance Visualization** — Understand which factors drive delays

### 📊 14 Operational Dashboards
| Dashboard | Description |
|-----------|-------------|
| 🏠 Home | System overview & live KPIs |
| 🚂 Train Fleet | Real-time fleet status & management |
| 🏛️ Stations | Station capacity & platform control |
| 📅 Scheduling | Train schedule management & conflict-free planning |
| ⚡ Conflict Management | Active conflict detection & resolution |
| 🤖 AI Priority Engine | AI-driven train prioritization |
| 📈 Analytics | Operational analytics & trends |
| 🔮 ML Prediction | Delay prediction command center |
| 🌐 Network Visualizer | Live network map & bottleneck visualization |
| 📋 Reports | Automated reporting & exports |
| 🔔 Notifications | Real-time alerts & notifications |
| 🎮 Simulation | Traffic simulation environment |
| 👤 Authentication | Role-based access control |
| ⚙️ Settings | System configuration |

### 🛡️ Role-Based Access Control
| Role | Access |
|------|--------|
| Admin | Full system control |
| Controller | Train operations & conflict management |
| Dispatcher | Scheduling & assignments |
| Analyst | Analytics & reports (read-only) |

### 🔌 REST API
- JWT Authentication
- Train, Station, Scheduling, Prediction endpoints
- CORS-enabled for external integrations

---

## 🏗️ Project Structure

```
railway_control/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
│
├── railway_control/          # Django project config
│   └── settings.py
│
└── apps/
    ├── authentication/       # Login, roles, JWT
    ├── trains/               # Train fleet & network visualizer
    ├── stations/             # Station & platform management
    ├── scheduling/           # Schedule engine
    ├── conflicts/            # Conflict detection & resolution
    ├── ai_engine/            # AI priority & optimization
    ├── ml_prediction/        # ML delay prediction (Random Forest)
    ├── analytics/            # Data analytics & trends
    ├── notifications/        # Alert system
    ├── reporting/            # PDF/CSV report generation
    └── simulation/           # Traffic simulation
```

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| ML / AI | scikit-learn, pandas, numpy, joblib |
| Frontend | HTML5, CSS3, Chart.js, Bootstrap Icons |
| Database | SQLite (dev) / MySQL 8.0 (prod) |
| Auth | JWT (djangorestframework-simplejwt) |
| Server | Gunicorn + WhiteNoise |
| Reports | ReportLab (PDF generation) |
| Visualizations | Matplotlib, Seaborn, Chart.js |
| Containerisation | Docker + docker-compose |

---

## 🚀 Quick Start (Local — SQLite)

### Prerequisites
- Python 3.10+
- pip
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/tripathik9559/AI-Train-Traffic-Control.git
cd AI-Train-Traffic-Control

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env — set SECRET_KEY at minimum

# 5. Run migrations
python manage.py migrate

# 6. Load seed data (Indian Railways stations & trains)
python manage.py seed_data

# 7. Train the ML model
python manage.py train_model

# 8. Create a superuser
python manage.py createsuperuser

# 9. Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

---

## 🐳 Docker Deployment (MySQL)

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env with your SECRET_KEY, DB credentials

# 2. Build and start containers
docker-compose up --build -d

# 3. Run migrations inside container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py createsuperuser
```

App available at **http://localhost:8000**

---

## ⚙️ Environment Variables

```env
# Core
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (leave blank for SQLite)
DB_ENGINE=django.db.backends.mysql
DB_NAME=railway_control
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306
```

---

## 🤖 ML Model Details

| Metric | Value |
|--------|-------|
| Algorithm | Random Forest Regressor |
| R² Score | 0.84 |
| Training Data | Indian Railways seed dataset |
| Features | Weather, Traffic Density, Train Type, Route, Day of Week, Historical Delays |
| Output | Predicted delay (minutes) + Risk Level (LOW / MEDIUM / HIGH / CRITICAL) |

```bash
# Train the model manually
python manage.py train_model

# Or trigger via admin panel: ML Prediction → Retrain Model
```

---

## 📡 API Endpoints (Partial — WIP)

```
POST   /api/auth/login/          → JWT token
GET    /api/trains/              → List all trains
GET    /api/stations/            → List all stations
POST   /api/ml/predict/          → Predict delay for a train
GET    /api/ml/model-info/       → Current model metrics
GET    /api/analytics/summary/   → System analytics summary
```

> Full API documentation coming soon.

---

## 🗺️ Roadmap

- [x] Core Django project structure with 11 apps
- [x] Authentication & role-based access
- [x] Train & Station management
- [x] ML delay prediction (Random Forest)
- [x] AI Priority Engine
- [x] Conflict detection
- [x] 14 dashboards (ongoing refinement)
- [x] Docker setup
- [ ] WebSocket real-time updates
- [ ] Complete REST API documentation
- [ ] Unit & integration tests
- [ ] CI/CD pipeline
- [ ] Mobile-responsive polish
- [ ] Live deployment (Render / Railway)

---

## 🏆 Origin Story

This project began as a problem statement for **Smart India Hackathon (SIH) 2025**, focused on AI-driven solutions for railway traffic management. Post-hackathon, development has continued independently — rebuilding the core architecture, adding the ML prediction pipeline, expanding to 14 dashboards, and containerizing the full stack with Docker — as an ongoing B.Tech final-year project.

---

## 👨‍💻 Author

**Kartikey**  
B.Tech CSE — BBDNIIT, Lucknow (2026 Batch)  
Building this daily. Commits = progress.

---

## 📝 License

© BBDNIIT — For educational and portfolio purposes only.  
Not affiliated with Indian Railways.
