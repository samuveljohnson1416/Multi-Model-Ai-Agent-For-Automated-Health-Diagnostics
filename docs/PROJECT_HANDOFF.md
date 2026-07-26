# Project Handoff — Health Diagnostics AI v2.0

> Last updated: 2026-07-26
> Status: **Cleanup complete — ready for integration testing**

---

## Architecture

```
Presentation:  frontend/ (Streamlit multi-page app)
       ↕ HTTP (httpx)
API:           backend/routes/ (FastAPI REST endpoints)
       ↕ function calls
Services:      backend/services/ (business logic + I/O)
       ↕ function calls
Domain:        backend/domain/ (pure functions, medical logic)
       ↕ client
Database:      backend/db/ (Supabase with in-memory fallback)
```

### Key Design Decisions
- **Single LLM provider (Groq)** — replaces old Ollama/HF fallback chain
- **Pydantic models as single source of truth** — `backend/models/` is the only place schemas are defined
- **Dual-mode database** — Supabase when configured, in-memory fallback for local dev
- **Clean OCR pipeline** — 3-step fallback (direct text → Tesseract → OCR.space), not 36 brute-force
- **Frontend decoupled from backend** — frontend only communicates via HTTP API client

---

## Completed Phases

### Phase 1: Project Scaffold ✅
- `backend/config.py` — pydantic-settings, no scattered os.getenv()
- `backend/models/` — BloodParameter, Report, Chat, Health schemas
- `requirements.txt` — complete (37 packages, no missing deps)
- `.env.example` — template with setup instructions
- `.gitignore` — updated

### Phase 2: Domain Logic ✅
- `backend/domain/reference_ranges.py` — 47 parameters, age/gender adjusted
- `backend/domain/risk_calculator.py` — Framingham CVD, lipid ratios, basic risk
- `backend/domain/unit_converter.py` — 30+ unit conversions
- `backend/domain/report_interpreter.py` — deviation scoring, severity classification
- `backend/data/reference_ranges.json` — medical reference data

### Phase 3: Backend Services ✅
- `backend/services/llm_service.py` — Groq wrapper with error handling
- `backend/services/ocr_service.py` — 3-step OCR with lazy imports
- `backend/services/parser_service.py` — regex + JSON parsing, sanity bounds
- `backend/services/validator_service.py` — validates against reference ranges
- `backend/services/analysis_service.py` — single orchestrator (5-step pipeline)
- `backend/services/chat_service.py` — Groq-powered Q&A with fallback

### Phase 4: Database ✅
- `backend/db/client.py` — Supabase singleton, graceful when unconfigured
- `backend/db/repository.py` — CRUD with Supabase + in-memory fallback

### Phase 5: FastAPI Routes ✅
- `POST /api/analyze` — upload + analyze blood report
- `GET /api/reports/{id}` — retrieve report
- `GET /api/reports?user_id=x` — list user reports
- `DELETE /api/reports/{id}` — delete report
- `POST /api/chat` — ask about a report
- `GET /api/health` — provider status

### Phase 6: Streamlit Frontend ✅
- `frontend/app.py` — 60-line multi-page app (was 2,830 lines)
- `frontend/pages/upload.py` — file upload + user context
- `frontend/pages/dashboard.py` — parameter table, charts, risk gauge
- `frontend/pages/chat.py` — chat interface with suggested questions
- `frontend/pages/history.py` — past reports list
- `frontend/api_client.py` — centralized API communication
- `frontend/config.py` — frontend settings

### Phase 7: Deployment & Testing ✅
- `Dockerfile` — multi-service (FastAPI + Streamlit)
- `start.sh` — startup script for Docker
- `tests/test_v2.py` — 39 tests, all passing

---

## Files Created (v2 — new architecture)

| Directory | Files | Purpose |
|-----------|-------|---------|
| `backend/` | `__init__.py`, `config.py`, `main.py` | App scaffold |
| `backend/models/` | 5 files | Pydantic schemas |
| `backend/domain/` | 5 files | Pure medical logic |
| `backend/services/` | 7 files | Business logic + I/O |
| `backend/db/` | 3 files | Supabase integration |
| `backend/routes/` | 5 files | REST endpoints |
| `backend/data/` | 1 file | Reference ranges JSON |
| `frontend/` | `app.py`, `config.py`, `api_client.py` | Streamlit app |
| `frontend/pages/` | 4 files | Individual pages |
| `tests/` | `test_v2.py` | 39 passing tests |
| Root | `Dockerfile`, `start.sh`, `.env.example` | Deployment |

**Total new files: 36**

---

## Cleanup (Completed 2026-07-26)

All old v1 code has been deleted:
- ✅ `src/`, `ui/`, `api/`, `db/`, `config/` — removed
- ✅ Old markdown docs (9 files, ~200KB) — removed
- ✅ `app.py`, `start_project.py`, `user_context.db` — removed
- ✅ `tests/test_suite.py` (old tests) — removed
- ✅ `.env` rebuilt for v2 (Groq, not Ollama/HF)

---

## How to Run Locally

```bash
# 1. Create .env from template
cp .env.example .env
# Fill in GROQ_API_KEY (required), SUPABASE_URL/KEY (optional)

# 2. Start the backend
uvicorn backend.main:app --reload --port 8000

# 3. In another terminal, start the frontend
cd frontend && streamlit run app.py
```

## How to Run Tests

```bash
python -m pytest tests/test_v2.py -v
```

---

## Known Issues

1. **Supabase not yet tested** — the repository has Supabase code but needs a real project to verify writes/reads
2. **Old files still present** — `src/`, `ui/`, `api/`, `db/` should be moved to `_legacy/` after verification
3. **Frontend components directory** — planned but not yet created (pages work without it)
4. **No CI/CD pipeline** — no GitHub Actions or similar

---

## Next Immediate Tasks

1. Set up Groq API key in `.env` and test LLM features end-to-end
2. Full end-to-end test: upload PDF → analyze → chat
3. Set up Supabase project and verify database persistence
4. Test HuggingFace Spaces deployment with Docker
5. Add frontend components for reusable chart/table widgets
