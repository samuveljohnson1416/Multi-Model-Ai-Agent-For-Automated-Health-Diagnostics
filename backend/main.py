"""
FastAPI Application Entry Point
================================
Multi-Model AI Health Diagnostics — Backend API

Run with:
    uvicorn backend.main:app --reload

API prefix:  /api
Docs:        http://localhost:8000/docs
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config.settings import settings
from backend.api.routes_upload import router as upload_router
from backend.api.routes_analysis import router as analysis_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_health import router as health_router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "AI-powered automated health diagnostics API. "
        "Supports OCR extraction, multi-model blood report analysis, "
        "and natural-language Q&A via local/cloud LLMs."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow the React dev server and any production origins
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_PREFIX = "/api"

app.include_router(health_router, prefix=API_PREFIX, tags=["Health"])
app.include_router(upload_router, prefix=API_PREFIX, tags=["Upload"])
app.include_router(analysis_router, prefix=API_PREFIX, tags=["Analysis"])
app.include_router(chat_router, prefix=API_PREFIX, tags=["Chat"])

# ---------------------------------------------------------------------------
# Root redirect to docs
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
def root():
    return {
        "message": f"{settings.app_title} API is running",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/health",
    }


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("=" * 60)
    logger.info("%s v%s", settings.app_title, settings.app_version)
    logger.info("Debug mode : %s", settings.debug)
    logger.info("CORS origins: %s", settings.cors_origins)
    logger.info("Ollama URL : %s", settings.ollama_url)
    logger.info("=" * 60)


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down %s", settings.app_title)