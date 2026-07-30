"""
OCR service — simplified text extraction from medical documents.

Uses a sane 3-step fallback chain:
  1. Direct text extraction (PDF text layer / JSON / CSV / TXT)
  2. NVIDIA Nemotron OCR-v2 (cloud, high accuracy)
  3. Tesseract OCR with a single good preprocessing pipeline
     (can be disabled via OCR_DISABLE_TESSERACT=true for dev/testing)

"""

import io
import json
import csv
import base64
import logging
import platform
import shutil
from typing import Optional
from dataclasses import dataclass

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)

# Lazy imports — only loaded when needed
_PIL_Image = None
_pytesseract = None
_pdfplumber = None
_cv2 = None


def _lazy_import_pil():
    global _PIL_Image
    if _PIL_Image is None:
        from PIL import Image
        _PIL_Image = Image
    return _PIL_Image


def _lazy_import_tesseract():
    global _pytesseract
    if _pytesseract is None:
        import pytesseract

        settings = get_settings()
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        elif platform.system() == "Windows":
            # Common Windows install path
            default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            import os
            if os.path.exists(default):
                pytesseract.pytesseract.tesseract_cmd = default

        _pytesseract = pytesseract
    return _pytesseract


def _lazy_import_pdfplumber():
    global _pdfplumber
    if _pdfplumber is None:
        import pdfplumber as pp
        _pdfplumber = pp
    return _pdfplumber


def _lazy_import_cv2():
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    return _cv2


# ──────────────────────────────────────────────────────────────
# Data class for extraction results
# ──────────────────────────────────────────────────────────────


@dataclass
class ExtractionResult:
    """Result from text extraction."""
    text: str
    source: str  # "pdf_text", "tesseract", "nvidia_nemotron", "direct", "csv"
    confidence: Optional[float] = None
    page_count: Optional[int] = None


# ──────────────────────────────────────────────────────────────
# Main OCR Service
# ──────────────────────────────────────────────────────────────


class OCRService:
    """
    Simplified OCR service with a 3-step fallback chain.
    No more 36 brute-force preprocessing combinations.
    """

    def __init__(self):
        settings = get_settings()
        self._nvidia_api_key = settings.nvidia_api_key if settings.has_nvidia_ocr else None
        self._ocr_timeout = settings.ocr_timeout
        self._tesseract_enabled = settings.tesseract_enabled  # False when OCR_DISABLE_TESSERACT=true
        self._tesseract_available = self._check_tesseract() if self._tesseract_enabled else False
        if not self._tesseract_enabled:
            logger.info("[DEV] Tesseract OCR disabled via OCR_DISABLE_TESSERACT setting")

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available on the system."""
        try:
            tesseract = _lazy_import_tesseract()
            tesseract.get_tesseract_version()
            logger.info("Tesseract OCR available")
            return True
        except Exception:
            logger.info("Tesseract OCR not available — will use API fallback")
            return False

    async def extract_text(
        self, file_bytes: bytes, file_type: str
    ) -> ExtractionResult:
        """
        Extract text from a medical document.

        Fallback chain:
          1. Direct extraction (PDF text, JSON, CSV, TXT)
          2. Tesseract OCR (images and scanned PDFs)
          3. OCR.space API (cloud fallback)

        Args:
            file_bytes: Raw file content
            file_type: File extension (pdf, png, jpg, json, csv, txt)

        Returns:
            ExtractionResult with extracted text and source info.

        Raises:
            ValueError: If no text could be extracted.
        """
        file_type = file_type.lower().strip(".")

        # ── Direct extraction (structured formats) ─────────────
        if file_type == "json":
            return self._extract_json(file_bytes)

        if file_type == "csv":
            return self._extract_csv(file_bytes)

        if file_type == "txt":
            return self._extract_text_file(file_bytes)

        # ── PDF: try text layer first, then OCR ────────────────
        if file_type == "pdf":
            result = self._extract_pdf_text(file_bytes)
            if result and len(result.text.strip()) > 30:
                return result

            logger.info("PDF text layer empty/short — falling back to OCR")

        # ── Image or scanned PDF: OCR ──────────────────────────
        if file_type in ("png", "jpg", "jpeg", "pdf"):
            # Try NVIDIA API first
            if self._nvidia_api_key:
                result = await self._extract_nvidia_nemotron(file_bytes, file_type)
                if result and len(result.text.strip()) > 20:
                    return result

            # Try Tesseract fallback (skipped when OCR_DISABLE_TESSERACT=true)
            if self._tesseract_available:
                result = self._extract_tesseract(file_bytes, file_type)
                if result and len(result.text.strip()) > 20:
                    return result
            elif not self._tesseract_enabled:
                logger.debug("[DEV] Tesseract step skipped (OCR_DISABLE_TESSERACT=true)")

        raise ValueError(
            f"Could not extract text from {file_type} file. "
            "Please ensure the document is readable and not password-protected."
        )

    # ──────────────────────────────────────────────────────────
    # Extraction methods
    # ──────────────────────────────────────────────────────────

    def _extract_json(self, file_bytes: bytes) -> ExtractionResult:
        """Extract from JSON file."""
        try:
            text = file_bytes.decode("utf-8")
            # Validate it's parseable JSON
            json.loads(text)
            return ExtractionResult(text=text, source="json_direct")
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid JSON file: {e}")

    def _extract_csv(self, file_bytes: bytes) -> ExtractionResult:
        """Extract from CSV file — convert rows to readable text."""
        try:
            text = file_bytes.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            lines = []
            for row in reader:
                line_parts = [f"{k}: {v}" for k, v in row.items() if v]
                lines.append(" | ".join(line_parts))
            extracted = "\n".join(lines)
            return ExtractionResult(text=extracted, source="csv_direct")
        except Exception as e:
            raise ValueError(f"Invalid CSV file: {e}")

    def _extract_text_file(self, file_bytes: bytes) -> ExtractionResult:
        """Extract from plain text file."""
        try:
            text = file_bytes.decode("utf-8")
            return ExtractionResult(text=text, source="text_direct")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1")
            return ExtractionResult(text=text, source="text_direct")

    def _extract_pdf_text(self, file_bytes: bytes) -> Optional[ExtractionResult]:
        """Extract text from PDF using pdfplumber (text layer)."""
        try:
            pdfplumber = _lazy_import_pdfplumber()
            pages_text = []

            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                total_pages = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                        # ── [EXTRACTION CHECKPOINT] Raw text lines from pdfplumber ──
                        lines = text.splitlines()
                        logger.debug(
                            "[EXTRACTION CHECKPOINT] Page %d/%d: %d lines extracted",
                            page_num, total_pages, len(lines),
                        )
                        for i, line in enumerate(lines, start=1):
                            logger.debug(
                                "[EXTRACTION CHECKPOINT] Page %d, Line %02d: %r",
                                page_num, i, line,
                            )

                    # Also try extracting tables
                    tables = page.extract_tables()
                    for t_idx, table in enumerate(tables):
                        for r_idx, row in enumerate(table):
                            cleaned = [str(cell) if cell else "" for cell in row]
                            row_text = " | ".join(cleaned)
                            pages_text.append(row_text)
                            # ── [EXTRACTION CHECKPOINT] Raw table rows ──
                            logger.debug(
                                "[EXTRACTION CHECKPOINT] Page %d, Table %d, Row %02d: %r",
                                page_num, t_idx, r_idx, row_text,
                            )

            if pages_text:
                full_text = "\n".join(pages_text)
                # ── [EXTRACTION CHECKPOINT] Final assembled text summary ──
                logger.debug(
                    "[EXTRACTION CHECKPOINT] PDF assembled: %d total lines, %d chars",
                    full_text.count("\n") + 1,
                    len(full_text),
                )
                return ExtractionResult(
                    text=full_text,
                    source="pdf_text",
                    page_count=total_pages,
                )
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")

        return None

    async def _extract_nvidia_nemotron(
        self, file_bytes: bytes, file_type: str
    ) -> Optional[ExtractionResult]:
        """Extract text using NVIDIA Nemotron OCR-v2 API."""
        try:
            Image = _lazy_import_pil()

            if file_type == "pdf":
                try:
                    from pdf2image import convert_from_bytes
                    settings = get_settings()
                    # Convert all pages without last_page limit
                    images = convert_from_bytes(
                        file_bytes, 
                        dpi=200, 
                        poppler_path=settings.poppler_path
                    )
                except Exception as e:
                    logger.warning(f"pdf2image conversion failed for NVIDIA OCR: {e}")
                    return None
            else:
                images = [Image.open(io.BytesIO(file_bytes))]

            all_text = []

            async with httpx.AsyncClient(timeout=self._ocr_timeout) as client:
                for img in images:
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format="JPEG", quality=85)
                    b64_str = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                    quality = 85
                    scale = 1.0
                    while len(b64_str) > 175000:
                        scale *= 0.9
                        if scale < 0.2:
                            break
                        new_width = int(img.width * scale)
                        new_height = int(img.height * scale)
                        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        img_byte_arr = io.BytesIO()
                        resized_img.save(img_byte_arr, format="JPEG", quality=int(quality * scale))
                        b64_str = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                    invoke_url = "https://ai.api.nvidia.com/v1/cv/nvidia/nemotron-ocr-v2"
                    headers = {
                        "Authorization": f"Bearer {self._nvidia_api_key}",
                        "Accept": "application/json"
                    }
                    payload = {
                        "input": [
                            {
                                "type": "image_url",
                                "url": f"data:image/jpeg;base64,{b64_str}"
                            }
                        ]
                    }

                    response = await client.post(invoke_url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    result_json = response.json()
                    
                    extracted_text = ""
                    if "data" in result_json and isinstance(result_json["data"], list):
                        extracted_text = " ".join([str(item.get("text", "")) for item in result_json["data"]])
                    elif "choices" in result_json and isinstance(result_json["choices"], list):
                        extracted_text = result_json["choices"][0].get("message", {}).get("content", "")
                    else:
                        extracted_text = json.dumps(result_json)

                    if extracted_text.strip():
                        all_text.append(extracted_text.strip())

            if all_text:
                return ExtractionResult(
                    text="\\n".join(all_text),
                    source="nvidia_nemotron",
                    page_count=len(images),
                )

        except Exception as e:
            logger.warning(f"NVIDIA Nemotron OCR failed: {e}")

        return None

    def _extract_tesseract(
        self, file_bytes: bytes, file_type: str
    ) -> Optional[ExtractionResult]:
        """Extract text using Tesseract OCR with a single good preprocessing pipeline."""
        try:
            Image = _lazy_import_pil()
            pytesseract = _lazy_import_tesseract()
            cv2 = _lazy_import_cv2()
            import numpy as np

            # Convert to PIL Image
            if file_type == "pdf":
                try:
                    from pdf2image import convert_from_bytes
                    settings = get_settings()
                    images = convert_from_bytes(
                        file_bytes, 
                        dpi=300, 
                        first_page=1, 
                        last_page=5,
                        poppler_path=settings.poppler_path
                    )
                except Exception as e:
                    logger.warning(f"pdf2image conversion failed: {e}")
                    return None
            else:
                images = [Image.open(io.BytesIO(file_bytes))]

            all_text = []

            for img in images:
                # Convert to OpenCV format for preprocessing
                img_array = np.array(img.convert("RGB"))
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

                # Single high-quality preprocessing pipeline:
                # 1. Adaptive threshold (handles uneven lighting)
                # 2. Slight denoise
                denoised = cv2.fastNlMeansDenoising(gray, h=10)
                thresh = cv2.adaptiveThreshold(
                    denoised, 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2,
                )

                # Convert back to PIL
                processed = Image.fromarray(thresh)

                # Run Tesseract with a medical-friendly config
                text = pytesseract.image_to_string(
                    processed,
                    config="--oem 3 --psm 6",
                )

                if text.strip():
                    all_text.append(text.strip())

                # If preprocessing didn't help, try the raw image too
                if not all_text:
                    text = pytesseract.image_to_string(
                        img,
                        config="--oem 3 --psm 6",
                    )
                    if text.strip():
                        all_text.append(text.strip())

            if all_text:
                return ExtractionResult(
                    text="\n".join(all_text),
                    source="tesseract",
                    page_count=len(images),
                )

        except Exception as e:
            logger.warning(f"Tesseract extraction failed: {e}")

        return None

    def get_status(self) -> dict:
        """Get OCR provider status for health check."""
        return {
            "name": "ocr",
            "available": self._tesseract_available or bool(self._nvidia_api_key),
            "nvidia_nemotron": bool(self._nvidia_api_key),
            "tesseract": self._tesseract_available,
            "tesseract_disabled_by_dev_flag": not self._tesseract_enabled,
        }
