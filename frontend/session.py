"""
Centralised Streamlit session-state setup.

Every page calls init_session_state() at the top so all keys exist
regardless of which page the browser lands on first.
"""

import uuid

# pyrefly: ignore [missing-import]
import streamlit as st


def init_session_state() -> None:
    """Create session keys with safe defaults. Idempotent."""
    defaults = {
        "user_id": str(uuid.uuid4()),   # anonymous per-browser id
        "report_id": None,              # id of the open report
        "report_name": None,            # file name of the open report
        "analysis_result": None,        # full analysis payload from the backend
        "chat_history": [],             # [{"role": ..., "content": ...}]
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
