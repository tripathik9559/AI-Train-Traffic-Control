#!/bin/bash
# ─── Railway Control System — Docker Entrypoint ──────────────────────────────
set -e

echo "🚆 Railway Control System — Starting up..."

# Wait for MySQL
echo "⏳ Waiting for database..."
while ! python -c "
import sys, os, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railway_control.settings')
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "   Database not ready — retrying in 3s..."
    sleep 3
done
echo "✅ Database connection established."

# Run migrations
echo "📦 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Train ML model if not exists
if [ ! -f "/app/ml_models/delay_model.pkl" ]; then
    echo "🤖 Training ML delay prediction model (first run)..."
    python manage.py train_ml_model || echo "⚠️  ML training skipped — will retry on next request."
fi

# Seed data if database is empty
echo "🌱 Checking seed data..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'railway_control.settings')
import django
django.setup()
from apps.stations.models import Station
if not Station.objects.exists():
    from django.core.management import call_command
    print('   No data found — loading seed data...')
    call_command('seed_data')
    print('   ✅ Seed data loaded.')
else:
    print('   Data already exists — skipping seed.')
"

echo ""
echo "🚀 Starting Gunicorn server on 0.0.0.0:8000..."
echo "   Admin: http://localhost:8000/admin/"
echo "   App:   http://localhost:8000/"
echo ""

exec gunicorn railway_control.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --threads 2 \
    --worker-class gthread \
    --timeout 120 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
