"""
UploadFile Adapter
==================
Bridges FastAPI's UploadFile to the interface expected by core.ocr_engine.

The OCR engine was originally designed for Streamlit's UploadedFile object,
which exposes:
  - .read()      → bytes
  - .name        → str (original filename)
  - .type        → str (MIME type, e.g. "application/pdf")

This adapter wraps FastAPI's UploadFile so the core module needs zero changes.
"""

from fastapi import UploadFile


class UploadFileAdapter:
    """
    Wraps FastAPI UploadFile to satisfy the interface consumed by
    core.ocr_engine.extract_text_from_file().

    Usage:
        adapter = UploadFileAdapter(upload_file, file_bytes)
        result  = extract_text_from_file(adapter)
    """

    def __init__(self, upload_file: UploadFile, file_bytes: bytes):
        self._bytes = file_bytes
        self.name: str = upload_file.filename or "upload"
        # FastAPI uses content_type; Streamlit used type — expose both
        self.type: str = upload_file.content_type or _infer_mime(self.name)

    # ------------------------------------------------------------------
    # Streamlit-compatible interface
    # ------------------------------------------------------------------

    def read(self) -> bytes:
        """Return the raw file bytes (Streamlit-compatible)."""
        return self._bytes

    def getvalue(self) -> bytes:
        """Alias used by some internal helpers."""
        return self._bytes

    def __repr__(self) -> str:
        return f"<UploadFileAdapter name={self.name!r} type={self.type!r} size={len(self._bytes)}>"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MIME_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".bmp": "image/bmp",
    ".json": "application/json",
}


def _infer_mime(filename: str) -> str:
    """Fallback MIME type inference from file extension."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _MIME_MAP.get(ext, "application/octet-stream")