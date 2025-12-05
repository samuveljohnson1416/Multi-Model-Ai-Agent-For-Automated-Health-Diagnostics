import streamlit as st
from ocr_engine import extract_text_from_file
from parser import parse_blood_report
from validator import validate_parameters
from interpreter import interpret_results

st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

st.title("Blood Report Analyzer – Milestone 1")
st.markdown("Analyzes blood test reports and provides interpretations.")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your blood test report",
    type=["pdf", "png", "jpg", "jpeg"],
    help="PDF, PNG, JPG, JPEG"
)

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    with st.spinner("Processing..."):
        try:
            # Extract text
            st.subheader("📄 Step 1: Text Extraction")
            ocr_text = extract_text_from_file(uploaded_file)
            st.text_area("Extracted Text", ocr_text, height=200)
            st.caption(f"{len(ocr_text)} characters")
            
            st.divider()
            
            # Parse data
            st.subheader("🔍 Step 2: Parameters")
            parsed_data = parse_blood_report(ocr_text)
            st.json(parsed_data)
            
            st.divider()
            
            # Validate
            st.subheader("✅ Step 3: Validation")
            validated_data = validate_parameters(parsed_data)
            st.json(validated_data)
            
            st.divider()
            
            # Results
            st.subheader("📊 Step 4: Results")
            interpretation = interpret_results(validated_data)
            
            summary = interpretation["summary"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", summary["total_parameters"])
            with col2:
                st.metric("Normal", summary["normal"], delta="✓" if summary["normal"] > 0 else None)
            with col3:
                st.metric("Low", summary["low"], delta="⚠" if summary["low"] > 0 else None, delta_color="inverse")
            with col4:
                st.metric("High", summary["high"], delta="⚠" if summary["high"] > 0 else None, delta_color="inverse")
            
            if interpretation["abnormal_parameters"]:
                st.warning("**Abnormal Parameters:**")
                for param in interpretation["abnormal_parameters"]:
                    status_emoji = "🔻" if param["status"] == "LOW" else "🔺"
                    st.write(f"{status_emoji} **{param['parameter']}**: {param['value']} ({param['status']}) - Normal: {param['reference']}")
            
            st.info("**Recommendations:**")
            for rec in interpretation["recommendations"]:
                st.write(f"• {rec}")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please upload a valid blood report.")
else:
    st.info("👆 Upload a report to begin.")
    st.markdown("""
    ### How to use:
    1. Click **Browse files**
    2. Select your blood report
    3. Wait for analysis
    4. Review results
    """)
