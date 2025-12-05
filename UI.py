import streamlit as st
from ocr_engine import extract_text_from_file
from parser import parse_blood_report
from validator import validate_parameters
from interpreter import interpret_results

# Page configuration
st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

# Title and description
st.title("Blood Report Analyzer – Milestone 1")
st.markdown("""
This application analyzes blood test reports by extracting text, parsing parameters, 
validating values against reference ranges, and providing interpretations.
""")

st.divider()

# File uploader
uploaded_file = st.file_uploader(
    "Upload your blood test report",
    type=["pdf", "png", "jpg", "jpeg"],
    help="Supported formats: PDF, PNG, JPG, JPEG"
)

# Main logic
if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    with st.spinner("Processing your report..."):
        try:
            # Step 1: OCR - Extract text from file
            st.subheader("📄 Step 1: OCR Text Extraction")
            ocr_text = extract_text_from_file(uploaded_file)
            st.text_area("Extracted Text", ocr_text, height=200)
            
            st.divider()
            
            # Step 2: Parse parameters
            st.subheader("🔍 Step 2: Extracted Parameters")
            parsed_data = parse_blood_report(ocr_text)
            st.json(parsed_data)
            
            st.divider()
            
            # Step 3: Validate data
            st.subheader("✅ Step 3: Validated Data")
            validated_data = validate_parameters(parsed_data)
            st.json(validated_data)
            
            st.divider()
            
            # Step 4: Interpret results
            st.subheader("📊 Step 4: Final Interpretation")
            interpretation = interpret_results(validated_data)
            st.json(interpretation)
            
        except Exception as e:
            st.error(f"An error occurred during processing: {str(e)}")
            st.info("Please ensure your file is a valid blood report and try again.")
else:
    # Placeholder when no file is uploaded
    st.info("👆 Please upload a report to begin analysis.")
    st.markdown("""
    ### How to use:
    1. Click the **Browse files** button above
    2. Select your blood test report (PDF or image)
    3. Wait for the analysis to complete
    4. Review the extracted data and interpretations
    """)
