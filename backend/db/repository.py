"""
Repository — CRUD operations for reports and chat history.

Supports both Supabase (persistent) and in-memory (fallback).
Replaces the old db/repository.py that was never wired in.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .client import get_client

logger = logging.getLogger(__name__)


class ReportRepository:
    """
    Report storage with dual-mode support:
    - Supabase mode: persistent cloud storage
    - Memory mode: fallback when Supabase is not configured
    """

    def __init__(self):
        self._memory_store: Dict[str, dict] = {}
        self._chat_store: Dict[str, List[dict]] = {}

    @property
    def _db(self):
        return get_client()

    @property
    def _using_supabase(self) -> bool:
        return self._db is not None

    # ──────────────────────────────────────────────────────────
    # Reports
    # ──────────────────────────────────────────────────────────

    async def save_report(self, report_data: dict) -> str:
        """
        Save a report. Returns the report ID.

        Args:
            report_data: Dict with keys: user_id, file_name, file_type,
                         parameters, analysis, risks, recommendations, summary
        """
        report_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        payload = {
            "id": report_id,
            "user_id": report_data.get("user_id"),
            "created_at": now,
            "file_name": report_data.get("file_name"),
            "file_type": report_data.get("file_type"),
            "parameters": report_data.get("parameters", []),
            "analysis": report_data.get("analysis", {}),
            "risks": report_data.get("risks", {}),
            "recommendations": report_data.get("recommendations", []),
            "summary": report_data.get("summary", {}),
            "status": "completed",
        }

        if self._using_supabase:
            try:
                result = self._db.table("reports").insert(payload).execute()
                if result.data:
                    logger.info(f"Report saved to Supabase: {report_id}")
                else:
                    raise ValueError("Supabase insert returned no data")
            except Exception as e:
                logger.error(f"Supabase save failed, falling back to memory: {e}")
                self._memory_store[report_id] = payload
        else:
            self._memory_store[report_id] = payload
            logger.info(f"Report saved to memory: {report_id}")

        return report_id

    async def get_report(self, report_id: str) -> Optional[dict]:
        """Get a report by ID."""
        if self._using_supabase:
            try:
                result = (
                    self._db.table("reports")
                    .select("*")
                    .eq("id", report_id)
                    .single()
                    .execute()
                )
                return result.data if result.data else None
            except Exception as e:
                logger.warning(f"Supabase get failed: {e}")

        return self._memory_store.get(report_id)

    async def get_user_reports(self, user_id: str) -> List[dict]:
        """Get all reports for a user, newest first."""
        if self._using_supabase:
            try:
                result = (
                    self._db.table("reports")
                    .select("id, created_at, file_name, file_type, summary, status")
                    .eq("user_id", user_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                return result.data or []
            except Exception as e:
                logger.warning(f"Supabase list failed: {e}")

        # Memory fallback
        return [
            r for r in self._memory_store.values()
            if r.get("user_id") == user_id
        ]

    # ──────────────────────────────────────────────────────────
    # Chat History
    # ──────────────────────────────────────────────────────────

    async def save_chat_message(
        self, report_id: str, role: str, content: str
    ) -> None:
        """Save a chat message for a report."""
        message = {
            "id": str(uuid.uuid4()),
            "report_id": report_id,
            "role": role,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }

        if self._using_supabase:
            try:
                self._db.table("chat_history").insert(message).execute()
                logger.info(f"Chat message saved to Supabase: {report_id}")
                return
            except Exception as e:
                logger.warning(f"Supabase chat save failed: {e}")

        # Memory fallback
        if report_id not in self._chat_store:
            self._chat_store[report_id] = []
        self._chat_store[report_id].append(message)

    async def get_chat_history(self, report_id: str) -> List[dict]:
        """Get chat history for a report."""
        if self._using_supabase:
            try:
                result = (
                    self._db.table("chat_history")
                    .select("*")
                    .eq("report_id", report_id)
                    .order("created_at")
                    .execute()
                )
                return result.data or []
            except Exception as e:
                logger.warning(f"Supabase chat get failed: {e}")

        return self._chat_store.get(report_id, [])

    async def delete_report(self, report_id: str) -> None:
        """Delete a report and its chat history."""
        if self._using_supabase:
            try:
                self._db.table("chat_history").delete().eq("report_id", report_id).execute()
                self._db.table("reports").delete().eq("id", report_id).execute()
                logger.info(f"Report deleted from Supabase: {report_id}")
                return
            except Exception as e:
                logger.warning(f"Supabase delete failed: {e}")

        self._memory_store.pop(report_id, None)
        self._chat_store.pop(report_id, None)
