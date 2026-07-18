"""
Upload Service
==============
Handles file ingestion, OCR extraction, and Phase-1 parsing.

Flow:
    FastAPI UploadFile
        → UploadFileAdapter  (bridge to core interface)
        → core.ocr_engine.extract_text_from_file()
        → core.parser.parse_blood_report()
        → core.validator.validate_parameters()
        → phase1.phase1_extractor.extract_phase1_medical_image()
        → UploadResponse

The service is intentionally thin — it orchestrates existing core modules
without adding medical logic.
"""

import logging
from typing import Optional

from fastapi import UploadFile, HTTPException

from backend.adapters.upload_adapter import UploadFileAdapter
from core.ocr_engine import extract_text_from_file
from core.parser import parse_blood_report
from core.validator import validate_parameters
from phase1.phase1_extractor import extract_phase1_medical_image

logger = logging.getLogger(__name__)


async def process_upload(upload_file: UploadFile) -> dict:
    """
    Main upload pipeline:
      1. Read raw bytes
      2. Wrap in adapter for core compatibility
      3. Extract text via OCR engine
      4. Parse blood report structure
      5. Validate parameters against reference ranges
      6. Run Phase-1 extraction → CSV
      7. Return structured result dict

    Raises:
        HTTPException 400 – if file type is unsupported
        HTTPException 422 – if OCR extraction completely fails
        HTTPException 500 – on unexpected errors
    """
    # ── Read file bytes ───────────────────────────────────────────────────
    try:
        file_bytes: bytes = await upload_file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=500, detail=f"Could not read file: {exc}")

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Wrap in adapter ───────────────────────────────────────────────────
    adapted_file = UploadFileAdapter(upload_file, file_bytes)
    logger.info(
        "Processing upload: name=%s  type=%s  size=%d bytes",
        adapted_file.name,
        adapted_file.type,
        len(file_bytes),
    )

    # ── OCR extraction ────────────────────────────────────────────────────
    try:
        ocr_result = extract_text_from_file(adapted_file)
    except Exception as exc:
        logger.exception("OCR extraction failed")
        raise HTTPException(status_code=500, detail=f"OCR extraction error: {exc}")

    # extract_text_from_file returns a dict or raises; normalise
    if isinstance(ocr_result, dict):
        ocr_text: str = ocr_result.get("text", "") or ocr_result.get("ocr_text", "")
        age: Optional[int] = ocr_result.get("age")
        gender: Optional[str] = ocr_result.get("gender")
    else:
        ocr_text = str(ocr_result) if ocr_result else ""
        age = None
        gender = None

    if not ocr_text.strip():
        logger.warning("OCR produced no text for file: %s", adapted_file.name)
        return {
            "filename": adapted_file.name,
            "file_type": adapted_file.type,
            "ocr_text": "",
            "parsed_data": {},
            "validated_data": {},
            "phase1_csv": "",
            "age": age,
            "gender": gender,
            "success": False,
            "error": "OCR produced no readable text. Please upload a clearer image or PDF.",
        }

    # ── Parse blood report ────────────────────────────────────────────────
    try:
        parsed_data: dict = parse_blood_report(ocr_text)
    except Exception as exc:
        logger.exception("Blood report parsing failed")
        parsed_data = {}

    # ── Validate parameters ───────────────────────────────────────────────
    try:
        validated_data: dict = validate_parameters(parsed_data) if parsed_data else {}
    except Exception as exc:
        logger.exception("Parameter validation failed")
        validated_data = {}

    # ── Phase-1 CSV extraction ────────────────────────────────────────────
    try:
        phase1_csv: str = extract_phase1_medical_image(ocr_text)
    except Exception as exc:
        logger.exception("Phase-1 extraction failed")
        phase1_csv = ""

    # ── Extract demographics from Phase-1 CSV if not in OCR result ────────
    if (age is None or gender is None) and phase1_csv:
        age, gender = _extract_demographics_from_csv(phase1_csv, age, gender)

    logger.info(
        "Upload processed: parsed=%d params  validated=%d params  csv_rows=%d",
        len(parsed_data),
        len(validated_data),
        phase1_csv.count("\n") - 1 if phase1_csv else 0,
    )

    return {
        "filename": adapted_file.name,
        "file_type": adapted_file.type,
        "ocr_text": ocr_text,
        "parsed_data": parsed_data,
        "validated_data": validated_data,
        "phase1_csv": phase1_csv,
        "age": age,
        "gender": gender,
        "success": True,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_demographics_from_csv(
    csv_text: str,
    existing_age: Optional[int],
    existing_gender: Optional[str],
) -> tuple[Optional[int], Optional[str]]:
    """
    Pull age/gender from the first data row of the Phase-1 CSV.
    Returns the original values unchanged if nothing useful is found.
    """
    try:
        lines = [l.strip() for l in csv_text.splitlines() if l.strip()]
        if len(lines) < 2:
            return existing_age, existing_gender

        header = [h.strip().lower() for h in lines[0].split(",")]
        age_idx = header.index("age") if "age" in header else -1
        gender_idx = header.index("gender") if "gender" in header else -1

        # Use first data row
        first_row = lines[1].split(",")

        age = existing_age
        gender = existing_gender

        if age_idx >= 0 and age_idx < len(first_row):
            val = first_row[age_idx].strip()
            if val not in ("NA", "", "None"):
                try:
                    age = int(float(val))
                except ValueError:
                    pass

        if gender_idx >= 0 and gender_idx < len(first_row):
            val = first_row[gender_idx].strip()
            if val not in ("NA", "", "None"):
                gender = val.capitalize()

        return age, gender
    except Exception:
        return existing_age, existing_gender
