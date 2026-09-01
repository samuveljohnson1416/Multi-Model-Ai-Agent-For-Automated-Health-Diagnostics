# Health Diagnostics AI Agent (v3.0)

An AI-powered medical report analysis system that provides comprehensive blood
work interpretation through a **multi-agent pipeline** — specialist agents for
extraction, diagnosis, risk and nutrition, coordinated in parallel and merged
into a single report. Every agent degrades gracefully to rule-based logic when
no LLM provider is configured.

## Features

- **Advanced OCR Processing** - Extract text from PDF and image files (NVIDIA Nemotron + Tesseract fallback).
- **Comprehensive Blood Analysis** - Parse 30+ blood parameters including CBC, differential counts, and chemistry panels.
- **Multi-Agent Analysis** - Extraction, Diagnosis, Risk and Nutrition agents orchestrated by a Coordinator.
- **Agent Insights Page** - Inspect each agent's reasoning, the model it used, and its timing.
- **Conversational Agent** - Chat that can reference the other agents' findings.
- **Multi-Provider LLM Layer** - Groq + Google Gemini with per-agent model mapping and automatic fallback.

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **LLM**: Groq (`openai/gpt-oss-20b`, `openai/gpt-oss-120b`) + Google Gemini (`gemini-flash-latest`)
- **Validation**: Pydantic v2
- **Database**: Supabase (in-memory fallback)
- **Architecture**: Routes → Services → Agents → LLM Providers, with a Domain layer of pure functions

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

4. Environment Variables:
Copy `.env.example` to `.env` and fill in your credentials. All keys are
optional — with none set, the app runs entirely on rule-based logic. For
AI-powered agents set `GROQ_API_KEY` and/or `GEMINI_API_KEY`.

5. Install Tesseract OCR:
   - **Windows**: Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - **macOS**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

## Usage

### Development

You can run the backend and frontend separately:

**Backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
streamlit run app.py
```

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

## Project Structure

```
├── backend/            # FastAPI backend (Routes, Services, Domain, Repository)
├── frontend/           # Streamlit user interface components
├── docs/               # Project Documentation
├── tests/              # Test files
├── render.yaml         # Render Deployment Blueprint
├── Dockerfile.backend  # Backend container spec
├── Dockerfile.frontend # Frontend container spec
├── start-backend.sh    # Backend startup script
├── start-frontend.sh   # Frontend startup script
└── requirements.txt    # Project dependencies
```

## Disclaimer

This tool is for informational purposes only and should not replace professional medical advice. Always consult with healthcare professionals for medical decisions and interpretations.