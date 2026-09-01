"""
FastAPI application — entry point for the backend.

Clean lifespan management, CORS, and router registration.
No global mutable state, no sys.path hacks.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings, Settings
from .db.client import init_supabase, close_supabase
from .db.repository import ReportRepository
from .services.ocr_service import OCRService
from .services.parser_service import ParserService
from .services.validator_service import ValidatorService
from .services.llm_service import LLMService
from .services.analysis_service import AnalysisService
from .services.chat_service import ChatService
from .services.llm import ProviderRegistry, GroqProvider, GeminiProvider
from .agents import (
    ExtractionAgent,
    DiagnosisAgent,
    RiskAgent,
    NutritionAgent,
    ConversationalAgent,
    CoordinatorAgent,
)
from .routes import analyze, reports, chat, health
from .middleware.auth import APIKeyMiddleware

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ──────────────────────────────────────────────
# Keyed by client IP address. Limits are applied per-route.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ── Provider / agent wiring ───────────────────────────────────
def build_registry(settings: Settings) -> ProviderRegistry:
    """Construct the LLM provider registry from configured API keys."""
    groq = GroqProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
        timeout=settings.groq_timeout,
    ) if settings.has_groq else None

    gemini = GeminiProvider(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_tokens,
    ) if settings.has_gemini else None

    return ProviderRegistry(groq_provider=groq, gemini_provider=gemini)


def build_coordinator(registry: ProviderRegistry, settings: Settings) -> CoordinatorAgent:
    """Wire the specialist agents with their preferred providers."""
    # Each agent uses its preferred provider, then falls back to any other
    # configured provider, then (inside the agent) to rule-based logic.
    def pick(preferred: str):
        return registry.get_provider(preferred, "groq", "gemini")

    # Risk Agent prefers a larger Groq model when Groq is available.
    groq = registry.get_groq()
    risk_provider = (
        groq.with_model(settings.groq_risk_model)
        if groq is not None and settings.agent_risk_provider == "groq"
        else pick(settings.agent_risk_provider)
    )

    return CoordinatorAgent(
        extraction_agent=ExtractionAgent(pick(settings.agent_extraction_provider)),
        diagnosis_agent=DiagnosisAgent(pick(settings.agent_diagnosis_provider)),
        risk_agent=RiskAgent(risk_provider),
        nutrition_agent=NutritionAgent(pick(settings.agent_nutrition_provider)),
    )


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("Starting Health Diagnostics API v3.0")
    logger.info("=" * 60)

    # Initialize services
    init_supabase()

    registry = build_registry(settings)
    llm = LLMService(registry)

    ocr = OCRService()
    parser = ParserService()
    validator = ValidatorService()

    coordinator = build_coordinator(registry, settings)
    conversational = ConversationalAgent(registry.get_provider(settings.agent_chat_provider))

    analysis = AnalysisService(ocr, parser, validator, llm, coordinator=coordinator)
    chat_svc = ChatService(llm)
    repo = ReportRepository()

    # Attach to app state
    app.state.analysis_service = analysis
    app.state.chat_service = chat_svc
    app.state.conversational_agent = conversational
    app.state.llm_service = llm
    app.state.repository = repo
    app.state.ocr_service = ocr
    app.state.limiter = limiter

    logger.info(f"LLM providers: {registry.list_available() or '✗ none (rule-based fallback)'}")
    logger.info(f"Supabase: {'✓ connected' if settings.has_supabase else '✗ using in-memory'}")
    tesseract_status = "✓" if ocr._tesseract_available else ("✗ [DEV: disabled]" if not ocr._tesseract_enabled else "✗ not found")
    logger.info(f"OCR: nvidia_nemotron={'✓' if ocr._nvidia_api_key else '✗'}, tesseract={tesseract_status}")
    logger.info(f"API Key guard: {'✓ enabled' if settings.has_api_key else '✗ disabled (set API_KEY to enable)'}")
    logger.info(f"Max upload size: {settings.max_upload_mb} MB")
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
        version="3.0.0",
        lifespan=lifespan,
        # Disable interactive docs in production (Finding 8)
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    # ── Rate limiting (Finding 6) ──────────────────────────────
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."},
        )

    # ── API Key guard (Finding 1) ──────────────────────────────
    app.add_middleware(APIKeyMiddleware)

    # ── CORS (Finding 4) ──────────────────────────────────────
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

