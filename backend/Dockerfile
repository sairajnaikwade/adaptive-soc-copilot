# =============================================================================
# Adaptive SOC CoPilot — Backend Dockerfile
# Multi-stage build: development target for Docker Compose,
# production target for Render deployment.
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — Base: Install system deps + Python packages
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS base

LABEL maintainer="SOC CoPilot Team"
LABEL description="Adaptive SOC CoPilot Backend — FastAPI + SQLAlchemy"

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies required by psycopg2 and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — Development: Used by Docker Compose (supports hot reload)
# ---------------------------------------------------------------------------
FROM base AS development

# Copy application source code
COPY . .

# Create directory for ML model storage
RUN mkdir -p /app/ml_models

EXPOSE 8000

# Development server with hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------------------
# Stage 3 — Production: Optimized image for Render deployment
# ---------------------------------------------------------------------------
FROM base AS production

# Copy application source code
COPY . .

# Create non-root user for security
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser && \
    mkdir -p /app/ml_models && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Production server — no reload, multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
