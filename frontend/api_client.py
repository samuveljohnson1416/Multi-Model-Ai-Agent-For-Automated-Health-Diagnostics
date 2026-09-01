"""
API client — handles all communication with the FastAPI backend.

All HTTP calls go through here. The rest of the frontend
never touches httpx directly.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List

from config import API_BASE_URL

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0


def analyze_report(
    file_content: bytes,
    filename: str,
    user_id: Optional[str] = None,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Upload and analyze a blood report.

    Returns:
        API response dict with report_id, analysis, etc.
        None on error.
    """
    try:
        files = {"file": (filename, file_content)}
        data = {}
        if user_id:
            data["user_id"] = user_id
        if age:
            data["age"] = str(age)
        if gender:
            data["gender"] = gender

        response = httpx.post(
            f"{API_BASE_URL}/analyze",
            files=files,
            data=data,
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()

    except httpx.ConnectError:
        logger.error(f"Cannot connect to API at {API_BASE_URL}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.status_code} — {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def get_report(report_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a report by ID."""
    try:
        response = httpx.get(
            f"{API_BASE_URL}/reports/{report_id}",
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching report: {e}")
        return None


def get_user_reports(user_id: str) -> List[Dict[str, Any]]:
    """Get all reports for a user."""
    try:
        response = httpx.get(
            f"{API_BASE_URL}/reports",
            params={"user_id": user_id},
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("reports", [])
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        return []


def send_chat_message(
    report_id: str,
    message: str,
    user_id: Optional[str] = None,
) -> Optional[str]:
    """Send a chat message and get a response."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/chat",
            json={
                "report_id": report_id,
                "message": message,
                "user_id": user_id,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("message")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return None


def get_recent_reports() -> List[Dict[str, Any]]:
    """Recent analysis runs (for the internal /agent-review page)."""
    try:
        response = httpx.get(f"{API_BASE_URL}/debug/recent-reports", timeout=_TIMEOUT)
        response.raise_for_status()
        return response.json().get("reports", [])
    except Exception as e:
        logger.error(f"Error fetching recent reports: {e}")
        return []


def get_health() -> Optional[Dict[str, Any]]:
    """Check API health status."""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None
