"""History — previously analysed reports."""

# pyrefly: ignore [missing-import]
import streamlit as st

from datetime import datetime

import api_client
from session import init_session_state
from theme import apply_chrome

apply_chrome()
init_session_state()

st.title("History")

reports = api_client.get_user_reports(st.session_state.user_id)

if not reports:
    st.write("Reports you analyze are listed here.")
    if st.button("Analyze a report", type="primary"):
        st.switch_page("pages/upload.py")
    st.stop()

def _when(created) -> str:
    try:
        return datetime.fromisoformat(str(created)).strftime("%d %b %Y")
    except ValueError:
        return "an unknown date"


for i, report in enumerate(reports):
    rid = report.get("id", "")
    name = report.get("file_name", "Report")
    s = report.get("summary", {}) or {}
    total = s.get("total_parameters", "an unknown number of")
    flagged = s.get("abnormal_count", "an unknown number")

    if i:
        st.divider()
    c1, c2 = st.columns([4, 1], vertical_alignment="center")
    with c1:
        st.markdown(f"**{name}**")
        st.caption(f"Analyzed on {_when(report.get('created_at'))}. {total} values, {flagged} flagged.")
    with c2:
        if st.button("Open report", key=f"open_{rid}", use_container_width=True):
            full = api_client.get_report(rid)
            if full:
                st.session_state.report_id = rid
                st.session_state.report_name = name
                st.session_state.analysis_result = full.get("analysis")
                st.session_state.chat_history = []
                st.switch_page("pages/dashboard.py")
            else:
                st.error("That report could not be loaded. Reload this page and try again.")
