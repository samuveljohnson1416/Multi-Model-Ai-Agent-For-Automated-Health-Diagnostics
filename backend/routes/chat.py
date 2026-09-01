"""
POST /api/chat — ask questions about a blood report.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.chat import ChatRequest, ChatResponse
from ..models.blood_parameter import BloodParameter
from ..agents.agent_models import AgentResult

router = APIRouter(prefix="/api", tags=["Chat"])
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("30/minute")  # Groq API call — limit per IP
async def chat_with_report(request: Request, body: ChatRequest):
    """
    Ask a question about a previously analyzed blood report.

    Requires a valid report_id from a prior /api/analyze call.
    """
    repository = request.app.state.repository
    conversational_agent = request.app.state.conversational_agent

    # Validate message
    if len(body.message.strip()) < 3:
        raise HTTPException(status_code=400, detail="Message must be at least 3 characters")

    # Get the report
    report = await repository.get_report(body.report_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail=f"Report not found: {body.report_id}. Analyze a report first.",
        )

    # Reconstruct parameters from stored data
    try:
        raw_params = report.get("parameters", [])
        if isinstance(raw_params, list):
            parameters = [BloodParameter(**p) for p in raw_params]
        else:
            parameters = []
    except Exception:
        parameters = []

    # Get chat history
    chat_history = await repository.get_chat_history(body.report_id)
    history_messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in chat_history
    ]

    # Get recommendations + specialist agent reports from the stored analysis
    analysis = report.get("analysis", {})
    recommendations = analysis.get("recommendations", [])

    agent_reports = []
    for raw in analysis.get("agent_reports", []):
        try:
            agent_reports.append(AgentResult(**raw))
        except Exception:
            continue

    # Generate response
    try:
        answer = await conversational_agent.ask(
            question=body.message,
            parameters=parameters,
            agent_reports=agent_reports or None,
            chat_history=history_messages,
            recommendations=recommendations,
        )
    except Exception as e:
        logger.error(f"Chat failed for report '{body.report_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat failed. Please try again later.")

    # Save both messages to history
    await repository.save_chat_message(body.report_id, "user", body.message)
    await repository.save_chat_message(body.report_id, "assistant", answer)

    return ChatResponse(
        message=answer,
        report_id=body.report_id,
        timestamp=datetime.utcnow(),
    )
