"""
Analysis routes — POST /api/analyze
"""

import logging
from fastapi import APIRouter, HTTPException
from backend.services.analysis_service import run_analysis
from backend.schemas.analysis_schemas import AnalysisRequest, AnalysisResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, summary="Run multi-model medical analysis")
def analyze(request: AnalysisRequest):
    """
    Run the full multi-model analysis pipeline on validated blood report data.

    Models executed:
    - Model 1: Rule-based parameter classification
    - Model 2: Pattern recognition across parameter combinations
    - Model 3: Risk score computation (anaemia, infection, bleeding, CVD, renal)
    - Model 4 (optional): Contextual analysis based on demographics and lifestyle
    - Phase-2 (optional): LLM-powered explanation text via Ollama/HuggingFace

    All medical decisions are rule-based and auditable.
    LLM is used only for explanation text generation.
    """
    if not request.validated_data:
        raise HTTPException(
            status_code=422,
            detail="validated_data is required and must not be empty.",
        )

    user_context = (
        request.user_context.model_dump() if request.user_context else None
    )

    result = run_analysis(
        validated_data=request.validated_data,
        phase1_csv=request.phase1_csv,
        user_context=user_context,
        run_phase2=request.run_phase2,
        run_contextual=request.run_contextual,
    )

    if not result.get("success"):
        logger.warning("Analysis returned error: %s", result.get("error"))

    return result
