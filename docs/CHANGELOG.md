# Changelog — Health Diagnostics AI

All notable changes to this project are documented here.

---

## [2.0.2] — 2026-07-26

### 🛡️ Security Hardening
- Added `APIKeyMiddleware` to lock down all `/api/*` endpoints via `X-API-Key`.
- Added `slowapi` rate limiting (10/min for `/analyze`, 30/min for `/chat`).
- Enforced max upload size limit (`MAX_UPLOAD_MB`).
- Sanitized 500 error responses to prevent internal stack trace leakage.
- Disabled Swagger/OpenAPI docs in production mode.

### 🚀 Deployment Migration (HuggingFace to Render)
- Split single monolith container into two separate services for Render deployment.
- Created `render.yaml` Infrastructure as Code blueprint.
- Added `Dockerfile.backend` and `start-backend.sh`.
- Added `Dockerfile.frontend` and `start-frontend.sh`.
- Removed old `Dockerfile` and `start.sh`.

---

## [2.0.1] — 2026-07-26

### 🧹 Project Cleanup

- Deleted all old v1 directories: `src/`, `ui/`, `api/`, `db/`, `config/`
- Deleted old scripts: `app.py`, `start_project.py`
- Deleted 9 outdated markdown docs (~200KB freed)
- Deleted old `user_context.db` (SQLite, 45KB)
- Deleted old `tests/test_suite.py` (imported from deleted `src/core/`)
- Rebuilt `.env` for Groq (removed Ollama, HuggingFace, Google Vision keys)
- Updated `.env.example` with step-by-step setup instructions

---

## [2.0.0] — 2026-07-26

### 🏗️ Complete Architecture Rebuild

**Breaking Changes:**
- Entire project restructured from `src/` to `backend/` + `frontend/`
- LLM provider changed from Ollama/HuggingFace to **Groq**
- Database changed from SQLite to **Supabase** (with in-memory fallback)
- Frontend rewritten as multi-page Streamlit app (60 lines vs 2,830)
- API contract changed (see `backend/routes/`)

### Added
- `backend/config.py` — centralized config via pydantic-settings
- `backend/models/` — single source of truth for all Pydantic schemas
- `backend/domain/` — pure domain logic (no I/O dependencies)
  - `reference_ranges.py` — 47 parameters with age/gender adjustment
  - `risk_calculator.py` — Framingham CVD risk, lipid ratios
  - `unit_converter.py` — 30+ unit conversions
  - `report_interpreter.py` — deviation scoring, severity classification
- `backend/services/` — business logic layer
  - `llm_service.py` — Groq API with proper error handling
  - `ocr_service.py` — simplified 3-step pipeline (was 36 brute-force)
  - `parser_service.py` — merged parser with sanity bounds
  - `validator_service.py` — validates against dynamic reference ranges
  - `analysis_service.py` — single orchestrator replacing 3 old ones
  - `chat_service.py` — Groq-powered Q&A replacing hardcoded responses
- `backend/db/` — Supabase with in-memory fallback
- `backend/routes/` — clean FastAPI endpoints (analyze, reports, chat, health)
- `backend/main.py` — FastAPI app with proper lifespan management
- `frontend/` — decoupled Streamlit app
  - Multi-page navigation (upload, dashboard, chat, history)
  - Centralized API client (no direct backend imports)
- `tests/test_v2.py` — 39 tests covering domain, services, and models
- `render.yaml` — Render infrastructure blueprint
- `Dockerfile.backend`, `Dockerfile.frontend` — separate containers
- `start-backend.sh`, `start-frontend.sh` — Render startup scripts
- `.env.example` — template with setup instructions
- `docs/PROJECT_HANDOFF.md` — complete project context
- `docs/TODO.md` — task tracking
- `docs/CHANGELOG.md` — this file

### Removed (from active use — old files still present)
- `src/core/orchestrator.py` — replaced by `analysis_service.py`
- `src/core/enhanced_ai_agent.py` (691 lines) — replaced by `chat_service.py`
- `src/core/advanced_context_manager.py` (857 lines) — replaced by Supabase
- `src/core/ocr_engine.py` (1,023 lines) — replaced by `ocr_service.py`
- `src/ui/UI.py` (2,830 lines) — replaced by `frontend/` (6 files, ~400 lines total)
- `src/utils/llm_provider.py` — replaced by `llm_service.py`
- `src/utils/ocr_provider.py` — merged into `ocr_service.py`
- `src/phase1/`, `src/phase2/` — merged into single pipeline

### Fixed
- Missing dependencies in requirements.txt (supabase, httpx, plotly, etc.)
- Duplicate Pydantic models (was defined in 3 places, now 1)
- Hardcoded Tesseract path (now auto-detected with env var override)
- sys.path hacks (replaced by proper package structure)
- API keys in .env (now only in .env.example, .env is gitignored)
- Silent error swallowing (bare except blocks replaced with specific handling)

---

## [1.0.0] — 2026-05 (Original)

Initial implementation with:
- Streamlit monolith UI (2,830 lines)
- Tesseract OCR with 36 preprocessing strategies
- Ollama + HuggingFace LLM fallback
- SQLite for local session context
- Never-connected Supabase layer
- HuggingFace Spaces deployment
