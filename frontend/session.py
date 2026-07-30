"""
session.py — Centralised Streamlit session state initialisation.

Every page imports and calls init_session_state() at the top.
This guarantees all keys exist regardless of which page the user
lands on first — defensive against Streamlit's MPA execution model
where individual page scripts can run before app.py's inline guards
have a chance to execute.
"""

import uuid
import streamlit as st


def init_session_state() -> None:
    """
    Initialise all session state keys with safe defaults.

    Idempotent — safe to call multiple times; existing values are
    never overwritten.
    """
    defaults: dict = {
        # Unique anonymous identifier for this browser session
        "user_id": str(uuid.uuid4()),
        # ID of the most recently analysed report (set after upload)
        "report_id": None,
        # Full analysis payload returned by the backend
        "analysis_result": None,
        # List of {"role": "user"|"assistant", "content": str} dicts
        "chat_history": [],
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
