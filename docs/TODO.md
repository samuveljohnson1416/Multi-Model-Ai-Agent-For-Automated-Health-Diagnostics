# TODO — Health Diagnostics AI v2.0

> Last updated: 2026-07-26

---

## ✅ Completed

- [x] Phase 1: Project scaffold & configuration
- [x] Phase 2: Domain logic (reference ranges, risk calculator, unit converter, interpreter)
- [x] Phase 3: Backend services (LLM, OCR, parser, validator, analysis orchestrator, chat)
- [x] Phase 4: Database layer (Supabase client, repository with fallback)
- [x] Phase 5: FastAPI routes (analyze, reports, chat, health)
- [x] Phase 6: Streamlit frontend (multi-page app, 4 pages, API client)
- [x] Phase 7: Deployment config (render.yaml, Dockerfiles, start scripts) + Tests (39 passing)
- [x] Phase 8: Security Hardening (auth middleware, rate limits, size limits, sanitized errors)
- [x] Cleanup: Removed all old v1 code, rebuilt .env for Groq

---

## 🔲 Remaining Work

### High Priority
- [ ] Set up Groq API key in `.env` and verify LLM features end-to-end
- [ ] Full end-to-end test: upload PDF → analysis → chat
- [ ] Set up Supabase project and test database persistence
- [ ] Deploy to Render using the `render.yaml` blueprint

### Medium Priority
- [ ] Create `frontend/components/` (reusable parameter_table, risk_chart, sidebar)
- [ ] Improve error messages in frontend for common failure cases

### Low Priority
- [ ] Add CI/CD (GitHub Actions: lint, test, docker build)
- [ ] Add logging to file (not just console)
- [ ] Create Supabase migration SQL script
- [ ] Add PDF report export feature
- [ ] Add report comparison feature (compare two reports)

---

## 🐛 Known Issues

1. OCR.space free tier limited to 500 req/day
2. Groq free tier limited to 30 req/min — chat may hit limits under heavy use
3. Old `.env` file contains real API keys (already gitignored, but should rotate)
4. `user_context.db` (old SQLite) still in root — can be deleted
