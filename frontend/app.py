"""Health Diagnostics — Streamlit entry point (navigation + sidebar)."""

# pyrefly: ignore [missing-import]
import streamlit as st

from config import APP_TITLE, APP_SUBTITLE
from session import init_session_state
from theme import apply_chrome

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="expanded",
)
apply_chrome()
init_session_state()

analyze_page = st.Page("pages/upload.py", title="New analysis", icon=":material/upload_file:", default=True)
results_page = st.Page("pages/dashboard.py", title="Results", icon=":material/description:")
questions_page = st.Page("pages/chat.py", title="Questions", icon=":material/chat:")
history_page = st.Page("pages/history.py", title="History", icon=":material/history:")

pg = st.navigation([analyze_page, results_page, questions_page, history_page])

with st.sidebar:
    st.markdown(f"### {APP_TITLE}")
    st.caption(APP_SUBTITLE)
    st.divider()

    result = st.session_state.get("analysis_result")
    name = st.session_state.get("report_name")
    if result and name:
        st.caption("Open report")
        st.markdown(f"**{name}**")
    else:
        st.caption("No report open yet.")

    st.divider()
    st.caption(
        "Automated reading of a lab report. Not a diagnosis and not a "
        "substitute for review by a doctor."
    )

pg.run()
