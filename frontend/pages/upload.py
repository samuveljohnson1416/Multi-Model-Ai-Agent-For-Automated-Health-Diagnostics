"""
Upload Page — file upload with user context form.
"""

import streamlit as st
import api_client
from config import MAX_FILE_SIZE_MB


st.header("📤 Upload Blood Report")
st.markdown("Upload your blood test report for AI-powered analysis.")

# ── User Context Form ─────────────────────────────────────────
with st.expander("👤 Patient Information (optional — improves accuracy)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", min_value=0, max_value=150, value=None, step=1)
    with col2:
        gender = st.selectbox("Gender", options=[None, "male", "female", "other"], index=0)

# ── File Upload ───────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Choose a blood report file",
    type=["pdf", "png", "jpg", "jpeg", "json", "csv", "txt"],
    help=f"Max file size: {MAX_FILE_SIZE_MB}MB. Supported: PDF, images, JSON, CSV, TXT.",
)

# ── Analyze Button ────────────────────────────────────────────
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("File", uploaded_file.name)
    with col2:
        st.metric("Size", f"{file_size_mb:.1f} MB")
    with col3:
        st.metric("Type", uploaded_file.name.rsplit(".", 1)[-1].upper())

    if file_size_mb > MAX_FILE_SIZE_MB:
        st.error(f"File too large ({file_size_mb:.1f}MB). Max: {MAX_FILE_SIZE_MB}MB.")
    else:
        if st.button("🔬 Analyze Report", type="primary", use_container_width=True):
            with st.spinner("Analyzing your blood report... This may take 10-30 seconds."):
                result = api_client.analyze_report(
                    file_content=file_bytes,
                    filename=uploaded_file.name,
                    user_id=st.session_state.user_id,
                    age=age,
                    gender=gender,
                )

            if result:
                st.session_state.report_id = result.get("report_id")
                st.session_state.analysis_result = result.get("analysis")
                st.session_state.chat_history = []

                st.success(f"✅ Analysis complete! Report ID: `{st.session_state.report_id[:8]}...`")
                st.info("👈 Navigate to **Analysis Dashboard** to view results, or **Ask Questions** to chat.")
            else:
                st.error(
                    "❌ Analysis failed. Please check:\n"
                    "1. Is the backend running? (`uvicorn backend.main:app`)\n"
                    "2. Is the file a valid blood report?\n"
                    "3. Check terminal for error details."
                )
else:
    # Show helpful info when no file is uploaded
    st.divider()
    st.markdown("""
    ### How it works
    1. **Upload** your blood test report (PDF, image, or structured data)
    2. **OCR extracts** text from the document
    3. **AI parses** blood parameters (Hemoglobin, RBC, WBC, etc.)
    4. **Validates** against age/gender-adjusted reference ranges
    5. **Calculates** risk scores and generates recommendations
    6. **Chat** with AI about your results

    > ⚠️ This tool is for informational purposes only. Always consult a healthcare provider.
    """)
