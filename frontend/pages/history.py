"""
History Page — view past report analyses.
"""

# pyrefly: ignore [missing-import]
import streamlit as st
import api_client


st.header("📋 Report History")

# ── Fetch Reports ─────────────────────────────────────────────
user_id = st.session_state.get("user_id")

if not user_id:
    st.info("No user session. Upload a report to start.")
    st.stop()

reports = api_client.get_user_reports(user_id)

if not reports:
    st.info("No reports found. Upload your first report to get started!")
    st.stop()

# ── Display Reports ───────────────────────────────────────────
st.markdown(f"Found **{len(reports)}** report(s).")

for report in reports:
    report_id = report.get("id", "N/A")
    created = report.get("created_at", "N/A")
    filename = report.get("file_name", "Unknown")
    status = report.get("status", "unknown")
    summary = report.get("summary", {})

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.markdown(f"**{filename}**")
            st.caption(f"ID: `{report_id[:8]}...`")

        with col2:
            st.caption(f"📅 {created[:10] if isinstance(created, str) else 'N/A'}")

        with col3:
            total = summary.get("total_parameters", "?")
            abnormal = summary.get("abnormal_count", "?")
            st.caption(f"📊 {total} params, {abnormal} abnormal")

        with col4:
            if st.button("View", key=f"view_{report_id}"):
                # Load full report
                full_report = api_client.get_report(report_id)
                if full_report:
                    st.session_state.report_id = report_id
                    st.session_state.analysis_result = full_report.get("analysis")
                    st.session_state.chat_history = []
                    st.success("Report loaded!")
                    st.info("Navigate to **Analysis Dashboard** to view results.")
                else:
                    st.error("Failed to load report.")
