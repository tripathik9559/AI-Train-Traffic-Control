# ─── Railway Control System — Dockerfile ─────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="BBDNIIT Final Year Project"
LABEL description="AI-Assisted Train Traffic Control & Section Throughput Optimization System"

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/ml_models /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput --settings=railway_control.settings || true

# Expose port
EXPOSE 8000

# Entrypoint
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
