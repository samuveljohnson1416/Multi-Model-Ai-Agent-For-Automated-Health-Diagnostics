"""New analysis — upload a report and run it."""

# pyrefly: ignore [missing-import]
import streamlit as st

import api_client
from config import MAX_FILE_SIZE_MB, SUPPORTED_TYPES
from session import init_session_state
from theme import apply_chrome

apply_chrome()
init_session_state()

st.title("New analysis")

# A report is already open ------------------------------------------------
if st.session_state.get("report_id"):
    st.write(f"You have a report open: **{st.session_state.get('report_name', 'current report')}**")
    c1, c2 = st.columns(2)
    if c1.button("View results", use_container_width=True, type="primary"):
        st.switch_page("pages/dashboard.py")
    if c2.button("Start a new one", use_container_width=True):
        st.session_state.report_id = None
        st.session_state.report_name = None
        st.session_state.analysis_result = None
        st.session_state.chat_history = []
        st.rerun()
    st.stop()

# Upload form -----------------------------------------------------------
st.write(
    "Upload a blood test report. Digital or scanned PDFs, photos, and "
    "data files (CSV, JSON) all work."
)

with st.expander("Add age and sex for more accurate reference ranges"):
    c1, c2 = st.columns(2)
    age = c1.number_input("Age", min_value=0, max_value=120, value=None, step=1, placeholder="—")
    gender = c2.selectbox("Sex", options=[None, "male", "female", "other"],
                          format_func=lambda x: "—" if x is None else x.capitalize())

uploaded_file = st.file_uploader(
    "Report file",
    type=SUPPORTED_TYPES,
    label_visibility="collapsed",
    help=f"Up to {MAX_FILE_SIZE_MB} MB.",
)

if uploaded_file is None:
    st.stop()

file_bytes = uploaded_file.read()
size_mb = len(file_bytes) / (1024 * 1024)

if size_mb > MAX_FILE_SIZE_MB:
    st.error(f"That file is {size_mb:.1f} MB. The limit is {MAX_FILE_SIZE_MB} MB.")
    st.stop()

st.caption(f"{uploaded_file.name} · {size_mb:.1f} MB")

if st.button("Analyze", type="primary", use_container_width=True):
    with st.spinner("Reading the report and checking each value against its reference range…"):
        result = api_client.analyze_report(
            file_content=file_bytes,
            filename=uploaded_file.name,
            user_id=st.session_state.user_id,
            age=age,
            gender=gender,
        )

    if not result:
        st.error(
            "We couldn't analyze that file. Make sure it's a readable blood "
            "test report with numeric results, then try again."
        )
        st.stop()

    st.session_state.report_id = result.get("report_id")
    st.session_state.report_name = uploaded_file.name
    st.session_state.analysis_result = result.get("analysis")
    st.session_state.chat_history = []
    st.switch_page("pages/dashboard.py")
