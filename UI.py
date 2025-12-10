import streamlit as st
import pandas as pd
import io
from ocr_engine import extract_text_from_file
from parser import parse_blood_report
from validator import validate_parameters
from interpreter import interpret_results
from csv_converter import json_to_ml_csv

st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

st.title("Blood Report Analyzer – Milestone 1")
st.markdown("Analyzes blood test reports and provides interpretations.")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your blood test report",
    type=["pdf", "png", "jpg", "jpeg", "json"],
    help="PDF, PNG, JPG, JPEG, JSON"
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
            if not parsed_data:
                st.warning("No parameters detected. Check if the report format is supported.")
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
            
            st.divider()
            
            # ML-Ready CSV Export Section
            st.subheader("📊 ML-Ready CSV Export")
            
            # Convert OCR JSON to ML CSV format
            ml_csv = json_to_ml_csv(ocr_text)
            
            # Display CSV preview
            st.write("**ML-Ready CSV Preview:**")
            try:
                df_preview = pd.read_csv(io.StringIO(ml_csv))
                st.dataframe(df_preview, use_container_width=True)
                
                # Download button
                st.download_button(
                    label="📥 Download ML-Ready CSV",
                    data=ml_csv,
                    file_name=f"ml_ready_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )
                
                # Show raw CSV text
                with st.expander("View Raw ML CSV Data"):
                    st.text(ml_csv)
                    
            except Exception as e:
                st.error(f"Error creating ML CSV: {str(e)}")
                st.text(ml_csv)
            
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
