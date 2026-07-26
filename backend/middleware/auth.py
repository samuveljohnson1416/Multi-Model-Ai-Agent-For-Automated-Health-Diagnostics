"""
API Key authentication middleware.

Security pattern: Secure by Default (patterns.md).
When API_KEY is configured, every /api/* request must include
the X-API-Key header with the correct value.

If API_KEY is not set (e.g. local development), the guard is
disabled and all requests pass through. This makes local
development frictionless while keeping production locked down.
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings

logger = logging.getLogger(__name__)

# Paths that are always public regardless of API key
_PUBLIC_PATHS = {"/health", "/", "/docs", "/redoc", "/openapi.json"}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware that enforces X-API-Key header on all /api/* routes.

    Fail-secure: if the key does not match, 401 is returned.
    Open paths (/health, /docs, /) bypass the check.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()

        # Guard is disabled when no key is configured (dev mode)
        if not settings.has_api_key:
            return await call_next(request)

        # Allow public paths through without a key
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # All /api/* paths require the key
        if request.url.path.startswith("/api"):
            provided_key = request.headers.get("X-API-Key", "")
            if provided_key != settings.api_key:
                logger.warning(
                    f"Unauthorized request to {request.url.path} "
                    f"from {request.client.host if request.client else 'unknown'}"
                )
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Unauthorized. Provide a valid X-API-Key header."},
                )

        return await call_next(request)
