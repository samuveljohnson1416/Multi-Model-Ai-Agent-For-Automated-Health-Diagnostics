# Health Diagnostics AI Agent (v3.0)

A web app that reads a blood test report — PDF, photo, or a structured data
file — extracts the individual values, checks each one against an age- and
sex-adjusted reference range, estimates health risk, and produces a
plain-language interpretation through a small **multi-agent pipeline**.
Every step has a deterministic, rule-based fallback, so the app works even
with **no AI provider configured**.

This is informational only. It does not diagnose and is not a substitute for
a healthcare provider.

## Features

- **OCR pipeline** — direct text extraction for digital PDFs/JSON/CSV; NVIDIA
  Nemotron OCR (cloud) or Tesseract (local, with OpenCV preprocessing) for
  scans and photos.
- **Blood parameter parsing** — 30+ parameters (CBC, differential count,
  lipids, liver/kidney panels, thyroid, vitamins) with sanity-bound checks
  against OCR misreads.
- **Age/sex-adjusted validation** — status (normal/low/high/critical) and
  deviation severity computed by pure functions in `backend/domain/`.
- **Risk scoring** — a basic abnormal-value score, Framingham 10-year
  cardiovascular risk, and lipid ratios.
- **Multi-agent interpretation** — an `Extraction` agent runs first, then
  `Diagnosis`, `Risk`, and `Nutrition` agents run in parallel and are merged
  by a `Coordinator`; a `Conversational` agent answers follow-up questions
  with access to the other agents' findings. Every agent falls back to
  rule-based logic if no model answers.
- **Multi-provider LLM layer** — Groq and Google Gemini behind one interface,
  with per-agent provider preference and automatic fallback between them.
- **Plain, task-focused UI** — four pages (analyze, results, questions,
  history); no jargon, no raw model output on screen.
- **Internal `/agent-review` page** — an unlisted diagnostic view of the last
  pipeline run: which agent answered, which model, how long it took, and what
  it produced. Reachable only by typing the URL (its nav link is hidden).
- **Security basics** — an optional API-key guard on `/api/*`, per-IP rate
  limiting, and an upload size limit.

## Technology Stack

| Area | Technology |
|------|-----------|
| Backend | FastAPI, Pydantic v2, pydantic-settings |
| Frontend | Streamlit, pandas, Plotly |
| LLM providers | Groq (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`) + Google Gemini (`gemini-flash-latest`) |
| OCR | pdfplumber, pytesseract (Tesseract), pdf2image, OpenCV, Pillow, NVIDIA Nemotron OCR-v2 |
| Database | Supabase (optional — falls back to in-memory storage) |
| Security | `slowapi` rate limiting, custom API-key middleware |
| Testing | `pytest`, `pytest-asyncio` |
| Deployment | Docker, Render (Blueprint) |

Architecture: `routes → services → agents → LLM providers`, with a pure-function
`domain` layer underneath. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the full diagram and pipeline description.

## Project Structure

```
backend/
  main.py              FastAPI app factory + lifespan (wires providers, agents, services)
  config.py             Typed settings (pydantic-settings), loaded from .env
  routes/                analyze.py, chat.py, reports.py, health.py
  services/               ocr_service, parser_service, validator_service,
                           analysis_service, chat_service, llm_service
  services/llm/            provider_base, groq_provider, gemini_provider, provider_registry
  agents/                  base_agent, agent_models, coordinator_agent,
                           extraction_agent, diagnosis_agent, risk_agent,
                           nutrition_agent, conversational_agent
  domain/                  reference_ranges, unit_converter, risk_calculator, report_interpreter
  models/                  blood_parameter, report, chat, health
  db/                      client (Supabase), repository (Supabase or in-memory)
  middleware/              auth.py (API-key guard)

frontend/
  app.py                 Navigation + sidebar
  theme.py                 Shared stylesheet + helpers
  session.py               Session-state defaults
  api_client.py             All calls to the backend
  pages/                    upload, dashboard, chat, history, agent_review (unlisted)

tests/
  test_v3.py              Domain + service tests
  test_agents_v3.py        LLM provider, agent, and wired-API tests

render.yaml, Dockerfile.backend, Dockerfile.frontend, Dockerfile (single-container),
start-backend.sh, start-frontend.sh, start.sh, requirements.txt, .env.example
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Multi-Model-Ai-Agent-For-Automated-Health-Diagnostics
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Environment variables — copy `.env.example` to `.env`. All keys are
   optional; with none set, the app runs entirely on rule-based logic.

   | Variable | Purpose |
   |----------|---------|
   | `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_RISK_MODEL` | Groq access and model choices |
   | `GEMINI_API_KEY`, `GEMINI_MODEL` | Google Gemini access and model |
   | `NVIDIA_API_KEY` | Optional cloud OCR for scans/photos |
   | `AGENT_EXTRACTION_PROVIDER`, `AGENT_DIAGNOSIS_PROVIDER`, `AGENT_RISK_PROVIDER`, `AGENT_NUTRITION_PROVIDER`, `AGENT_CHAT_PROVIDER` | Override which provider (`groq`/`gemini`) each agent prefers |
   | `SUPABASE_URL`, `SUPABASE_KEY` | Optional persistent storage |
   | `API_KEY` | If set, every `/api/*` request needs an `X-API-Key` header |
   | `MAX_UPLOAD_MB` | Upload size limit (default 10) |
   | `CORS_ORIGINS`, `DEBUG`, `API_HOST`, `API_PORT` | Standard web-app settings |

5. Install Tesseract OCR (for local scanned-document OCR):
   - **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

## Usage

### Development

Run the backend and frontend in separate terminals:

**Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
```

Then open http://localhost:8501. The diagnostic view is at
http://localhost:8501/agent-review after you've analyzed at least one report.

### Tests

```bash
pytest -q
```

Tests marked `requires_groq` make real Groq API calls and are skipped
automatically if `GROQ_API_KEY` isn't set — no test doubles are used for the
LLM/agent layer.

### Production / Render Deployment

The repo ships a Render Blueprint (`render.yaml`) that creates two services from
`Dockerfile.backend` and `Dockerfile.frontend`.

**To deploy:**
1. Push this repository to GitHub.
2. In Render, choose **New + → Blueprint** and select the repo. Render reads
   `render.yaml` and creates `health-diagnostics-api` and `health-diagnostics-ui`.
3. When prompted, provide the secret values you want. `GROQ_API_KEY` is the one
   that matters; everything else is optional (the app runs rule-only without it).
4. After the **backend** finishes its first deploy, copy its URL, then on the
   **frontend** service set `API_BASE_URL` to `https://<backend-url>/api` and
   redeploy the frontend.
5. If you set `API_KEY` on the backend, set the **same** value on the frontend.

Notes:
- The free plan sleeps idle services; the first request after a pause takes
  ~30–60 s while the container wakes.
- The backend health check is `/api/health` (stays public even with `API_KEY` set).
- The two Gemini-preferred agents are routed to Groq by default
  (`AGENT_EXTRACTION_PROVIDER` / `AGENT_NUTRITION_PROVIDER` in `render.yaml`);
  remove those lines if you have a working Gemini key.

## Supported File Formats

- **PDF files** - Scanned or digital blood reports
- **Image files** - PNG, JPG, JPEG format medical reports
- **JSON files** - Structured medical data
- **CSV files** - Tabular blood work data

## Disclaimer

This tool is for informational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical decisions and interpretations.
