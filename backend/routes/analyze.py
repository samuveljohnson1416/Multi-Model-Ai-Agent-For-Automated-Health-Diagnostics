import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models.report import AnalysisResult, ReportResponse, UserContext
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])
limiter = Limiter(key_func=get_remote_address)

VALID_FILE_TYPES = {"pdf", "png", "jpg", "jpeg", "json", "csv", "txt"}


@router.post("/analyze", response_model=ReportResponse)
@limiter.limit("10/minute")  # Expensive AI call — strict limit per IP
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

    # Enforce file size limit (Finding 5 — DoS via large upload)
    settings = get_settings()
    if len(file_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.max_upload_mb} MB.",
        )

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
        # Log full details internally; never expose internals to caller
        logger.error(f"Analysis failed for file '{file.filename}' ({ext}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again later.")

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

    # Track recent runs for the internal /agent-review page (in-memory, best effort)
    recent = getattr(request.app.state, "recent_reports", None)
    if recent is not None:
        recent.appendleft({
            "id": report_id,
            "name": file.filename or "report",
            "at": datetime.utcnow().isoformat(timespec="seconds"),
        })

    return ReportResponse(
        report_id=report_id,
        created_at=datetime.utcnow(),
        file_name=file.filename or "unknown",
        file_type=ext,
        analysis=result,
        user_context=user_context,
    )
