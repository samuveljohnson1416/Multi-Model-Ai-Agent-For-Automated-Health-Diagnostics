# Architecture — Health Diagnostics AI v2.0

## System Overview

```mermaid
graph TB
    subgraph "Frontend (Streamlit)"
        A[app.py] --> B[pages/upload.py]
        A --> C[pages/dashboard.py]
        A --> D[pages/chat.py]
        A --> E[pages/history.py]
        B & C & D & E --> F[api_client.py]
    end

    F -->|HTTP| G

    subgraph "Backend (FastAPI)"
        G[main.py] --> MW[middleware/auth.py]
        MW --> H[routes/analyze.py]
        MW --> I[routes/reports.py]
        MW --> J[routes/chat.py]
        MW --> K[routes/health.py]

        H --> L[services/analysis_service.py]
        J --> M[services/chat_service.py]

        L --> N[services/ocr_service.py]
        L --> O[services/parser_service.py]
        L --> P[services/validator_service.py]
        L --> Q[services/llm_service.py]
        M --> Q

        P --> R[domain/reference_ranges.py]
        P --> S[domain/unit_converter.py]
        L --> T[domain/risk_calculator.py]
        L --> U[domain/report_interpreter.py]

        H & I & J --> V[db/repository.py]
        V --> W[db/client.py]
    end

    W -->|Supabase API| X[(Supabase PostgreSQL)]
    Q -->|Groq API| Y[Groq Cloud]
    N -->|OCR.space API| Z[OCR.space]
```

## Layer Rules

| Layer | May call | Must NOT call |
|-------|----------|---------------|
| Routes | Services, Repository | Domain directly |
| Services | Domain, other Services | Routes, Repository directly (except analysis_service) |
| Domain | Nothing (pure functions) | Services, Routes, DB |
| Repository | DB Client | Services, Routes, Domain |

**Exception:** `analysis_service.py` orchestrates the full pipeline, so it calls multiple services.

## Data Flow

```
File Upload
    → OCR Service (extract text)
        → Parser Service (text → raw parameters dict)
            → Validator Service (raw params → BloodParameter objects)
                → Report Interpreter (parameters → summary + recommendations)
                → Risk Calculator (parameters → risk scores)
                → LLM Service (abnormal params → AI insights)
    → Repository (save to DB)
    → API Response (ReportResponse)
```

## Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend framework | FastAPI | Async, auto-docs, Pydantic native |
| Frontend framework | Streamlit | Quick iteration, Python-only, migrate to Next.js later |
| LLM | Groq (Llama 3.1) | Free tier, fast inference, simple API |
| Database | Supabase (PostgreSQL) | Free tier, auth built-in, REST API |
| OCR | Tesseract + OCR.space | Local + cloud fallback |
| Validation | Pydantic v2 | Type safety, serialization, OpenAPI |
| Config | pydantic-settings | Typed env vars, validation |
| Security | slowapi, custom middleware | Rate limiting, API key auth |
| Deployment | Docker → Render | Free hosting (blueprint with 2 services) |
