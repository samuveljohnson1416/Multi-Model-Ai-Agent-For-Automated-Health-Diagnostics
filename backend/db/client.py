"""
Supabase client — singleton with proper lifecycle management.
Replaces the old db/client.py that was wired up but never connected.
"""

import logging
from typing import Optional

from ..config import get_settings

logger = logging.getLogger(__name__)

_client = None


def init_supabase():
    """
    Initialize the Supabase client singleton.
    Call once during app startup.
    """
    global _client
    settings = get_settings()

    if not settings.has_supabase:
        logger.warning(
            "SUPABASE_URL/SUPABASE_KEY not set — database features disabled. "
            "Reports will be stored in-memory only."
        )
        return None

    try:
        # pyrefly: ignore [missing-import]
        from supabase import create_client
        _client = create_client(settings.supabase_url, settings.supabase_key)
        logger.info(f"✓ Supabase connected: {settings.supabase_url}")
        return _client
    except Exception as e:
        logger.error(f"✗ Supabase connection failed: {e}")
        return None


def get_client():
    """Get the Supabase client (may be None if not configured)."""
    return _client


def close_supabase():
    """Cleanup on shutdown."""
    global _client
    _client = None
    logger.info("Supabase client closed")
