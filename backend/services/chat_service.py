"""
Chat Service
============
Thin wrapper around core.qa_assistant.BloodReportQAAssistant.

FastAPI route → chat_service.answer_question() → BloodReportQAAssistant → LLM provider
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def answer_question(
    question: str,
    report_data: dict,
    analysis_result: Optional[dict] = None,
    conversation_history: Optional[list] = None,
) -> dict:
    """
    Ask the Q&A assistant a question about the uploaded blood report.

    Args:
        question:             The user's natural-language question.
        report_data:          Validated parameter dict from the upload step.
        analysis_result:      Multi-model analysis result (optional context).
        conversation_history: Prior chat turns for context (optional).

    Returns:
        {"answer": str, "provider_used": str|None, "success": bool, "error": str|None}
    """
    try:
        from core.qa_assistant import BloodReportQAAssistant

        assistant = BloodReportQAAssistant()

        # Build context dict from analysis result
        context = {}
        if analysis_result:
            context["patterns"] = analysis_result.get("patterns_detected", [])
            context["risk_level"] = analysis_result.get("overall_risk_level")
            context["recommendations"] = analysis_result.get("recommendations", [])
            context["requires_attention"] = analysis_result.get("requires_attention", False)

        answer = assistant.answer_question(
            question=question,
            report_data=report_data,
            context=context,
            conversation_history=conversation_history or [],
        )

        # Determine which provider was used
        provider_used = None
        if hasattr(assistant, "_llm_provider") and assistant._llm_provider:
            provider_used = getattr(
                assistant._llm_provider, "active_provider", None
            )

        return {
            "answer": answer,
            "provider_used": str(provider_used) if provider_used else None,
            "success": True,
            "error": None,
        }

    except ImportError as exc:
        logger.error("Q&A assistant module unavailable: %s", exc)
        return {
            "answer": "The Q&A assistant is currently unavailable. Please ensure the core modules are installed.",
            "provider_used": None,
            "success": False,
            "error": str(exc),
        }
    except Exception as exc:
        logger.exception("Q&A assistant failed")
        return {
            "answer": "Unable to process your question at this time. Please try again.",
            "provider_used": None,
            "success": False,
            "error": str(exc),
        }
