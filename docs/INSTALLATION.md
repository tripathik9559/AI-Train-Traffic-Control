# Installation & Deployment Guide

## Railway Control System — BBDNIIT Final Year Project

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Installation (Recommended)](#docker-installation)
3. [Local Development Setup](#local-development-setup)
4. [MySQL Setup](#mysql-setup)
5. [Environment Variables](#environment-variables)
6. [Management Commands](#management-commands)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Docker Installation
- Docker Desktop 24.0+
- Docker Compose v2.20+
- 4 GB RAM minimum, 8 GB recommended
- 3 GB free disk space

### Local Development
- Python 3.11 or 3.12
- pip 23+
- MySQL 8.0+ (or SQLite for quick start)
- Git

---

## Docker Installation

This is the fastest and most reliable way to run the project.

### Step 1 — Clone the repository

```bash
git clone https://github.com/tripathik9559/railway-control-system.git
cd railway-control-system
```

### Step 2 — Configure environment

```bash
cp .env.example .env
```

The default `.env` works out of the box for Docker. No changes needed.

### Step 3 — Build and start

```bash
docker-compose up --build
```

First run will take 2–3 minutes. The entrypoint script:
- Waits for MySQL to be healthy
- Applies all database migrations
- Trains the ML model (~10 seconds, first run only)
- Seeds demo data automatically

### Step 4 — Open in browser

| URL | Description |
|-----|-------------|
| http://localhost | Main application (via Nginx) |
| http://localhost:8000 | Django directly |
| http://localhost:8000/admin | Django admin |

### Step 5 — Login

| Role | Username | Password |
|------|----------|----------|
| Administrator | admin | Admin@2024 |
| Section Controller | controller1 | Pass@2024 |
| Section Controller | controller2 | Pass@2024 |

### Useful Docker commands

```bash
# View logs
docker-compose logs -f web

# Stop all services
docker-compose down

# Stop and delete database volume (full reset)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build --force-recreate

# Run Django management commands inside container
docker-compose exec web python manage.py seed_data --clear
docker-compose exec web python manage.py train_ml_model
docker-compose exec web python manage.py createsuperuser
```

---

## Local Development Setup

### Step 1 — Clone and enter project

```bash
git clone https://github.com/tripathik9559/railway-control-system.git
cd railway-control-system
```

### Step 2 — Create virtual environment

```bash
python -m venv venv

# Activate
source venv/bin/activate           # Linux / macOS
venv\Scripts\activate              # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure .env for SQLite (quick start)

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=any-random-string-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# SQLite for local dev
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=./db_dev.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

ML_MODEL_PATH=./ml_models/delay_model.pkl
```

### Step 5 — Run migrations

```bash
python manage.py migrate
```

### Step 6 — Train ML model

```bash
python manage.py train_ml_model
```

Output:
```
✅ Model trained successfully!
   R² Score:      0.8358
   MAE:           5.341 minutes
   Cross-Val R²:  0.829
```

### Step 7 — Seed demo data

```bash
python manage.py seed_data
```

Output:
```
✅ Seed data loaded successfully!
  Admin login: admin / Admin@2024
  Controller login: controller1 / Pass@2024
```

### Step 8 — Start development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000

---

## MySQL Setup

### Install MySQL 8.0

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mysql-server-8.0
sudo systemctl start mysql
```

**macOS (Homebrew):**
```bash
brew install mysql@8.0
brew services start mysql@8.0
```

### Create database and user

```sql
-- Connect as root
mysql -u root -p

CREATE DATABASE railway_control_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'railway_user'@'localhost' IDENTIFIED BY 'railway_pass_2024';
GRANT ALL PRIVILEGES ON railway_control_db.* TO 'railway_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Update .env for MySQL

```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=railway_control_db
DB_USER=railway_user
DB_PASSWORD=railway_pass_2024
DB_HOST=localhost
DB_PORT=3306
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | Django secret key |
| `DEBUG` | `True` | Debug mode — set False in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hostnames |
| `DB_ENGINE` | `django.db.backends.mysql` | Database backend |
| `DB_NAME` | `railway_control_db` | Database name |
| `DB_USER` | `railway_user` | Database username |
| `DB_PASSWORD` | `railway_pass_2024` | Database password |
| `DB_HOST` | `db` | Database host (use `db` for Docker) |
| `DB_PORT` | `3306` | Database port |
| `ML_MODEL_PATH` | `./ml_models/delay_model.pkl` | Path to trained model pickle |

---

## Management Commands

### seed_data

Loads demo data: 12 stations, 15 trains, 47 schedules, conflicts, notifications.

```bash
python manage.py seed_data           # Load data (skip if exists)
python manage.py seed_data --clear   # Clear all + reload fresh
```

### train_ml_model

Trains a new Random Forest model with 5000 synthetic samples.

```bash
python manage.py train_ml_model
```

Run this after each deployment or after modifying `trainer.py`.

### Django standard commands

```bash
python manage.py migrate              # Apply migrations
python manage.py makemigrations       # Create new migrations
python manage.py createsuperuser      # Create admin user
python manage.py collectstatic        # Collect static files
python manage.py shell                # Django interactive shell
python manage.py test apps            # Run all tests
```

---

## Production Deployment

### 1. Set environment variables

```env
DEBUG=False
SECRET_KEY=a-long-random-50-char-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 2. Build and deploy with Docker Compose

```bash
docker-compose -f docker-compose.yml up -d --build
```

### 3. Nginx is pre-configured

The `nginx` service in `docker-compose.yml` handles:
- Static file serving with 30-day cache headers
- Reverse proxy to Gunicorn on port 8000
- Upload size limit: 20 MB

### 4. Gunicorn settings (in entrypoint.sh)

- Workers: 3 (adjust to 2×CPU+1 for production)
- Threads: 2
- Timeout: 120 seconds
- Worker class: gthread

---

## Troubleshooting

### "No module named 'mysqlclient'"

```bash
# Ubuntu/Debian
sudo apt install default-libmysqlclient-dev build-essential
pip install mysqlclient

# macOS
brew install mysql-connector-c
pip install mysqlclient
```

### "ML model not found" warnings

The model will auto-train on first startup via entrypoint. To force retrain:
```bash
python manage.py train_ml_model
# or via API:
POST /api/ml/retrain/
```

### Migrations inconsistency

```bash
python manage.py migrate --run-syncdb
# or reset (DEV only):
rm db_dev.sqlite3
python manage.py migrate
python manage.py seed_data
python manage.py train_ml_model
```

### Container database connection refused

The `web` service waits for the MySQL healthcheck to pass before starting.
If still failing, increase `start_period` in `docker-compose.yml`:
```yaml
healthcheck:
  start_period: 60s
```

### Static files not loading

```bash
python manage.py collectstatic --noinput
```

In Docker, this runs automatically inside the container build.
