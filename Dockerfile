FROM python:3.11-slim-bullseye

# ── System dependencies (Tesseract + Poppler for PDF) ──────
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ───────────────────────────────────────
COPY backend/ backend/
COPY frontend/ frontend/

# ── Startup script ─────────────────────────────────────────
# Runs both FastAPI (port 8000) and Streamlit (port 7860)
COPY start.sh .
RUN chmod +x start.sh

# ── Environment defaults for HF Spaces ────────────────────
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV API_BASE_URL=http://localhost:8000/api
ENV CORS_ORIGINS=*
ENV DEBUG=false

EXPOSE 7860

CMD ["./start.sh"]