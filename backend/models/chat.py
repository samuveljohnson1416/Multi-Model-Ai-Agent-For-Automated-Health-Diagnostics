"""
Chat models — request/response schemas for the chat endpoint.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    report_id: str = Field(description="UUID of the report to ask about")
    message: str = Field(min_length=1, max_length=2000)
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    message: str
    report_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
