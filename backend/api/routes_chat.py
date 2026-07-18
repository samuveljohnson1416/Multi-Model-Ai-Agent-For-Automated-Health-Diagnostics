"""
Chat routes — POST /api/chat
"""

import logging
from fastapi import APIRouter, HTTPException
from backend.services.chat_service import answer_question
from backend.schemas.chat_schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Ask the medical Q&A assistant")
def chat(request: ChatRequest):
    """
    Ask a natural-language question about the analysed blood report.

    The assistant:
    - ONLY uses data from the provided report and analysis
    - Does NOT make independent medical decisions
    - Always includes a medical disclaimer
    - Uses the LLM solely for generating explanatory text
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    if not request.report_data:
        raise HTTPException(
            status_code=422,
            detail="report_data is required to answer questions.",
        )

    history = (
        [m.model_dump() for m in request.conversation_history]
        if request.conversation_history
        else []
    )

    result = answer_question(
        question=request.question,
        report_data=request.report_data,
        analysis_result=request.analysis_result,
        conversation_history=history,
    )

    return result
