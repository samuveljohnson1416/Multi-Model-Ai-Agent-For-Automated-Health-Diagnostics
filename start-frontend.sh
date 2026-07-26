#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start-frontend.sh
# Render Web Service startup script for the Streamlit frontend.
#
# Render injects $PORT dynamically. Streamlit must listen on it.
# API_BASE_URL must point to the deployed backend Render URL.
# ─────────────────────────────────────────────────────────────

echo "Starting Health Diagnostics Dashboard (Streamlit)..."
echo "Port: ${PORT:-8501}"
echo "API: ${API_BASE_URL:-http://localhost:8000/api}"

cd frontend && exec streamlit run app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
