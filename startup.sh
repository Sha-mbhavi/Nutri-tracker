#!/usr/bin/env bash
# =============================================================================
# NutriTrack Production Container Startup Script
# Optimized for Azure App Service Linux Custom Container & Container Instances
# =============================================================================

set -e

echo "=========================================================="
echo " Starting NutriTrack Enterprise Application"
echo " Platform: Azure App Service (Linux Web App)"
echo " Port: ${PORT:-8000}"
echo "=========================================================="

# Run database schema migrations, column inspect checks, and initial seeds
echo "[INFO] Verifying database schema and initial seeding..."
python -c "
import sys
from app import create_app

try:
    app = create_app()
    print('[SUCCESS] Database schema synchronized and seed verification completed.')
except Exception as exc:
    print(f'[ERROR] Database initialization failed: {exc}', file=sys.stderr)
    sys.exit(1)
"

# Launch Gunicorn WSGI HTTP Server
echo "[INFO] Booting Gunicorn WSGI server: gunicorn --config gunicorn.conf.py wsgi:app"
exec gunicorn --config gunicorn.conf.py wsgi:app
