#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start-backend.sh
# Render Web Service startup script for the FastAPI backend.
#
# Render injects $PORT dynamically. We must listen on it.
# ─────────────────────────────────────────────────────────────

echo "Starting Health Diagnostics API (FastAPI)..."
echo "Host: 0.0.0.0 | Port: ${PORT:-8000}"

exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}"
