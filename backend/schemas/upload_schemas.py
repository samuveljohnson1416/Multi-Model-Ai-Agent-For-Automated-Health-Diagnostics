"""
Pydantic request/response schemas for the upload endpoint.
"""

from pydantic import BaseModel
from typing import Optional


class UploadResponse(BaseModel):
    """Response returned after a file is uploaded and OCR-processed."""

    filename: str
    file_type: str
    ocr_text: Optional[str] = None
    parsed_data: Optional[dict] = None
    validated_data: Optional[dict] = None
    phase1_csv: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    error: Optional[str] = None
    success: bool = True
