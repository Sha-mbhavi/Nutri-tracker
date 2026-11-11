"""
NutriTrack Production Gunicorn Configuration
Optimized for Azure App Service (Linux Web App) & Containerized Deployment.
"""
import multiprocessing
import os

# Server Socket Binding
# Azure App Service sets the PORT environment variable (default: 8000)
bind_port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{bind_port}"
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Worker Process & Concurrency Settings
# Dynamic worker sizing based on available CPU cores with manual override via WEB_CONCURRENCY
default_workers = max(2, min(multiprocessing.cpu_count() * 2 + 1, 8))
workers = int(os.getenv("WEB_CONCURRENCY", str(default_workers)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")
threads = int(os.getenv("GUNICORN_THREADS", "2"))
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))

# Lifecycle & Memory Management
# Periodically recycle workers to prevent memory leaks in long-running container pods
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Logging & Observability
# Stream all logs to stdout/stderr for ingestion by Azure Monitor / Application Insights / Log Stream
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Metadata
proc_name = "nutritrack-app"

# Reverse Proxy Security
# Azure Front Door & Azure App Service TLS termination proxy headers
forwarded_allow_ips = "*"
proxy_allow_ips = "*"
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
}
