"""
POST /api/analyze — upload and analyze a blood report file.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form

from ..models.report import AnalysisResult, ReportResponse, UserContext

router = APIRouter(prefix="/api", tags=["Analysis"])

VALID_FILE_TYPES = {"pdf", "png", "jpg", "jpeg", "json", "csv", "txt"}


@router.post("/analyze", response_model=ReportResponse)
async def analyze_report(
    request: Request,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
):
    """
    Upload and analyze a blood report file.

    **Supported formats:** PDF, PNG, JPG, JPEG, JSON, CSV, TXT

    **Optional context:** age, gender for personalized reference ranges.
    """
    analysis_service = request.app.state.analysis_service
    repository = request.app.state.repository

    # Validate file type
    ext = (file.filename or "unknown").rsplit(".", 1)[-1].lower()
    if ext not in VALID_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(VALID_FILE_TYPES))}",
        )

    # Read file
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Build user context
    user_context = None
    if age or gender:
        user_context = UserContext(age=age, gender=gender)

    # Run analysis
    try:
        result = await analysis_service.analyze(
            file_bytes=file_bytes,
            file_type=ext,
            user_context=user_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Save to database
    report_data = {
        "user_id": user_id,
        "file_name": file.filename,
        "file_type": ext,
        "parameters": [p.model_dump() for p in result.parameters],
        "analysis": result.model_dump(),
        "risks": result.risks.model_dump() if result.risks else {},
        "recommendations": result.recommendations,
        "summary": result.summary,
    }

    try:
        report_id = await repository.save_report(report_data)
    except Exception as e:
        # Don't fail the analysis if DB save fails
        report_id = str(uuid.uuid4())

    return ReportResponse(
        report_id=report_id,
        created_at=datetime.utcnow(),
        file_name=file.filename or "unknown",
        file_type=ext,
        analysis=result,
        user_context=user_context,
    )
