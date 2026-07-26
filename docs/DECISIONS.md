# Design Decisions — Health Diagnostics AI v2.0

## Decision Log

### D1: Groq instead of Ollama + HuggingFace

**Context:** Old system had a multi-provider fallback chain (Ollama → HF API) that was complex and unreliable.

**Decision:** Use Groq as single LLM provider.

**Rationale:**
- Groq has a generous free tier (30 req/min, 14,400 req/day)
- Sub-second inference latency (faster than Ollama on most hardware)
- Simple API (single SDK, no fallback chain needed)
- Supports Llama 3.1, Mixtral — same quality models

**Tradeoffs:**
- Requires internet (no offline mode)
- Single point of failure (mitigated by rule-based fallback in `chat_service.py`)

---

### D2: Supabase instead of SQLite

**Context:** Old system used both SQLite (local context) and Supabase (never connected). Two databases = confusion.

**Decision:** Supabase as primary DB with in-memory fallback.

**Rationale:**
- Cloud persistence (survives container restarts on HF Spaces)
- Built-in auth for future user accounts
- PostgreSQL (proper JSONB support for storing analysis results)
- Free tier sufficient for this project
- In-memory fallback means app works without DB config

**Tradeoffs:**
- Requires Supabase project setup for persistence
- No offline data persistence (in-memory only without Supabase)

---

### D3: Simplified OCR pipeline (3 steps, not 36)

**Context:** Old `ocr_engine.py` tried 6 preprocessing strategies × 6 Tesseract configs = 36 attempts.

**Decision:** Single good preprocessing pipeline + API fallback.

**Rationale:**
- Adaptive threshold + denoising handles 90% of cases
- If that fails, OCR.space API uses their own optimized pipeline
- 36 attempts took 30-60 seconds; 3 attempts take 3-5 seconds
- Diminishing returns after the first 2-3 strategies

**Tradeoffs:**
- May fail on edge-case images that the brute-force caught
- Mitigated by OCR.space cloud fallback

---

### D4: Separate FastAPI + Streamlit (not monolith)

**Context:** User wants to migrate to Next.js later.

**Decision:** FastAPI backend as independent service, Streamlit communicates via HTTP.

**Rationale:**
- Frontend is replaceable (swap Streamlit for Next.js without touching backend)
- API can serve other clients (mobile app, other UIs)
- Testable independently
- Clean separation of concerns

**Tradeoffs:**
- More complex deployment (two processes)
- Network hop adds latency vs direct function calls
- Mitigated by running both in same container for HF Spaces

---

### D5: Pydantic models as single source of truth

**Context:** Old system defined `BloodParameter` in 3 different files with slightly different schemas.

**Decision:** All schemas in `backend/models/`, imported everywhere.

**Rationale:**
- Eliminates schema drift
- Auto-generates OpenAPI docs
- Validates at every boundary
- Easy to evolve (change once, works everywhere)
