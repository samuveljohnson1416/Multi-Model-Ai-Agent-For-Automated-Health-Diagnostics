"""
Upload routes — POST /api/upload
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.services.upload_service import process_upload
from backend.schemas.upload_schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/tiff",
    "image/bmp",
    "application/json",
}

MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=UploadResponse, summary="Upload a blood report file")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a blood report (PDF, image, or JSON) for OCR extraction and parsing.

    Returns extracted text, parsed parameters, validated data, and Phase-1 CSV.
    """
    # Basic content-type validation (browser may send octet-stream for some files)
    if file.content_type not in ALLOWED_TYPES and not (
        file.filename and file.filename.lower().rsplit(".", 1)[-1]
        in {"pdf", "png", "jpg", "jpeg", "tiff", "tif", "bmp", "json"}
    ):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   "Allowed: PDF, PNG, JPG, JPEG, TIFF, BMP, JSON.",
        )

    result = await process_upload(file)

    if not result.get("success") and result.get("error"):
        logger.warning("Upload returned error: %s", result["error"])

    return result
