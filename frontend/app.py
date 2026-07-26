"""
Health Diagnostics AI — Streamlit Multi-Page Application

Entry point. Configures page layout and navigation.
This is 50 lines, not 2,830.
"""

import streamlit as st
import uuid

from config import APP_TITLE, APP_SUBTITLE


# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Health Diagnostics AI",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session State ─────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "report_id" not in st.session_state:
    st.session_state.report_id = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── Navigation ────────────────────────────────────────────────
upload_page = st.Page("pages/upload.py", title="Upload Report", icon="📤")
dashboard_page = st.Page("pages/dashboard.py", title="Analysis Dashboard", icon="📊")
chat_page = st.Page("pages/chat.py", title="Ask Questions", icon="💬")
history_page = st.Page("pages/history.py", title="Report History", icon="📋")

pg = st.navigation([upload_page, dashboard_page, chat_page, history_page])


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    st.divider()

    if st.session_state.report_id:
        st.success(f"Active report: `{st.session_state.report_id[:8]}...`")
    else:
        st.info("No report loaded. Upload one to get started.")

    st.divider()
    st.caption("v2.0.0 · Powered by Groq AI")


# ── Run Page ──────────────────────────────────────────────────
pg.run()
