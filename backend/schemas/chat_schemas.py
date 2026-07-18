"""
Pydantic request/response schemas for the chat endpoint.
"""

from pydantic import BaseModel
from typing import Optional, List


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""

    question: str
    report_data: dict
    analysis_result: Optional[dict] = None
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    """Response returned from the Q&A assistant."""

    answer: str
    provider_used: Optional[str] = None
    error: Optional[str] = None
    success: bool = True
