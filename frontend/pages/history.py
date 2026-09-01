"""History — previously analysed reports."""

# pyrefly: ignore [missing-import]
import streamlit as st

import api_client
from session import init_session_state
from theme import apply_chrome

apply_chrome()
init_session_state()

st.title("History")

reports = api_client.get_user_reports(st.session_state.user_id)

if not reports:
    st.write("No reports yet.")
    if st.button("Start an analysis", type="primary"):
        st.switch_page("pages/upload.py")
    st.stop()

for report in reports:
    rid = report.get("id", "")
    name = report.get("file_name", "Report")
    created = report.get("created_at", "")
    s = report.get("summary", {}) or {}
    total = s.get("total_parameters", "—")
    flagged = s.get("abnormal_count", "—")

    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.markdown(f"**{name}**")
            date = created[:10] if isinstance(created, str) else "—"
            st.caption(f"{date}  ·  {total} values, {flagged} flagged")
        with c2:
            if st.button("Open", key=f"open_{rid}", use_container_width=True):
                full = api_client.get_report(rid)
                if full:
                    st.session_state.report_id = rid
                    st.session_state.report_name = name
                    st.session_state.analysis_result = full.get("analysis")
                    st.session_state.chat_history = []
                    st.switch_page("pages/dashboard.py")
                else:
                    st.error("Couldn't load that report.")
