# =============================================================================
# NutriTrack Multi-Stage Production Dockerfile
# Base: Python 3.10 Slim
# Target: Azure App Service (Linux Web App) & Azure Container Apps (ACA)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build & Dependency Wheel Compilation
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies for compiling binary wheels (e.g. psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create isolated Python virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install application dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Minimal Production Runtime
# -----------------------------------------------------------------------------
FROM python:3.10-slim AS runtime

LABEL maintainer="NutriTrack Cloud Architecture Team" \
      app="nutritrack" \
      version="2.0.0" \
      description="Production image for NutriTrack Web Application on Azure App Service"

# Runtime shared libraries only (PostgreSQL client runtime & curl for container health probes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group (Least Privilege Security Standard)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m -d /home/appuser appuser

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Configure runtime environment
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    FLASK_ENV=production

WORKDIR /app

# Copy application source code
COPY . /app

# Ensure correct file permissions and create instance directory for local storage fallback
RUN mkdir -p /app/instance && \
    chmod +x /app/startup.sh && \
    chown -R appuser:appgroup /app /home/appuser

# Switch to non-root execution context
USER appuser

# Expose default HTTP application port
EXPOSE 8000

# Container health probe checking HTTP endpoint responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Launch startup script containing schema verification and Gunicorn WSGI server
ENTRYPOINT ["/app/startup.sh"]
