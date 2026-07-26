"""
FastAPI application — entry point for the backend.

Clean lifespan management, CORS, and router registration.
No global mutable state, no sys.path hacks.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db.client import init_supabase, close_supabase
from .db.repository import ReportRepository
from .services.ocr_service import OCRService
from .services.parser_service import ParserService
from .services.validator_service import ValidatorService
from .services.llm_service import LLMService
from .services.analysis_service import AnalysisService
from .services.chat_service import ChatService
from .routes import analyze, reports, chat, health

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Application state (set during lifespan) ───────────────────
class AppState:
    """Container for shared services — injected via app.state."""
    analysis_service: AnalysisService
    chat_service: ChatService
    llm_service: LLMService
    repository: ReportRepository


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("Starting Health Diagnostics API v2.0")
    logger.info("=" * 60)

    # Initialize services
    init_supabase()

    ocr = OCRService()
    parser = ParserService()
    validator = ValidatorService()
    llm = LLMService()
    analysis = AnalysisService(ocr, parser, validator, llm)
    chat_svc = ChatService(llm)
    repo = ReportRepository()

    # Attach to app state
    app.state.analysis_service = analysis
    app.state.chat_service = chat_svc
    app.state.llm_service = llm
    app.state.repository = repo
    app.state.ocr_service = ocr

    logger.info(f"Groq LLM: {'✓ ' + llm.model_name if llm.available else '✗ not configured'}")
    logger.info(f"Supabase: {'✓ connected' if settings.has_supabase else '✗ using in-memory'}")
    logger.info(f"OCR: tesseract={'✓' if ocr._tesseract_available else '✗'}, "
                f"ocr.space={'✓' if ocr._ocr_space_key else '✗'}")
    logger.info("API ready!")

    yield

    # Cleanup
    close_supabase()
    logger.info("Shutdown complete")


# ── Create app ────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Factory function for the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Health Diagnostics API",
        description="Multi-Model AI Agent for Blood Report Analysis",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(analyze.router)
    app.include_router(reports.router)
    app.include_router(chat.router)
    app.include_router(health.router)

    return app


# Module-level app instance (for uvicorn)
app = create_app()
