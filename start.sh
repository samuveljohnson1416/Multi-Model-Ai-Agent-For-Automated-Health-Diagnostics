#!/bin/bash
# Start both FastAPI backend and Streamlit frontend
# Used for HuggingFace Spaces deployment (single container)

# Start FastAPI in the background
echo "Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to be ready
sleep 10

# Start Streamlit on port 7860 (HF Spaces default)
echo "Starting Streamlit frontend on port 7860..."
cd frontend && streamlit run app.py \
    --server.port=7860 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
