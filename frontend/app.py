"""
Health Diagnostics AI — Streamlit Multi-Page Application

Entry point. Configures page layout and navigation.
This is 50 lines, not 2,830.
"""

import streamlit as st

from config import APP_TITLE, APP_SUBTITLE
from session import init_session_state


# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Health Diagnostics AI",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session State ─────────────────────────────────────────────
# Centralised in session.py — safe to call here and in every page.
init_session_state()



# ── Navigation ────────────────────────────────────────────────
upload_page = st.Page("pages/upload.py", title="Upload Report", icon="📤")
dashboard_page = st.Page("pages/dashboard.py", title="Analysis Dashboard", icon="📊")
agent_insights_page = st.Page("pages/agent_insights.py", title="Agent Insights", icon="🧠")
chat_page = st.Page("pages/chat.py", title="Ask Questions", icon="💬")
history_page = st.Page("pages/history.py", title="Report History", icon="📋")

pg = st.navigation([upload_page, dashboard_page, agent_insights_page, chat_page, history_page])


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
    st.caption("v3.0.0 · Multi-agent · Groq + Gemini")


# ── Run Page ──────────────────────────────────────────────────
pg.run()
