"""
Health check models — for the /api/health endpoint.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ProviderStatus(BaseModel):
    """Status of an external provider (LLM, OCR, DB)."""
    name: str
    available: bool
    model: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Response from the health check endpoint."""
    status: str = Field(default="ok", pattern="^(ok|degraded|error)$")
    version: str = Field(default="3.0.0")
    providers: list[ProviderStatus] = Field(default_factory=list)
