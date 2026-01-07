import streamlit as st
import pandas as pd
import io
import json
import sys
import os
import time
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.ocr_engine import extract_text_from_file
from core.parser import parse_blood_report
from core.validator import validate_parameters
from core.interpreter import interpret_results
from utils.csv_converter import json_to_ml_csv
from utils.ollama_manager import auto_start_ollama, get_ollama_manager
from phase2.phase2_integration_safe import integrate_phase2_analysis, check_phase2_requirements
from phase2.csv_schema_adapter import safe_percentage
from ui.chat_interface import create_medical_chat_interface


def generate_clean_text_report(filename, validated_data, interpretation, phase2_result=None, age=None, gender=None):
    """Generate clean text-based medical report without HTML styling"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Safely extract summary with defaults
    summary = interpretation.get("summary", {})
    total_params = summary.get("total_parameters", 0)
    normal_count = summary.get("normal", 0)
    low_count = summary.get("low", 0)
    high_count = summary.get("high", 0)
    abnormal_count = low_count + high_count
    
    # Phase-2 information
    phase2_available = False
    phase2_summary = {}
    if phase2_result and phase2_result.get("phase2_summary", {}).get("available"):
        phase2_available = True
        phase2_summary = phase2_result["phase2_summary"]
    
    # Build clean text report
    report_lines = []
    
    # Header
    report_lines.append("🩺 MEDICAL REPORT SUMMARY")
    report_lines.append("=" * 50)
    report_lines.append("")
    
    # Report Information
    report_lines.append("📄 Report Information:")
    report_lines.append(f"   File: {filename}")
    report_lines.append(f"   Date: {timestamp}")
    report_lines.append(f"   AI Analysis: {'✅ Enhanced' if phase2_available else '❌ Basic'}")
    report_lines.append("")
    
    # Results Summary
    report_lines.append("📊 Results Summary:")
    report_lines.append(f"   Total Tests: {total_params}")
    report_lines.append(f"   Normal: {normal_count}")
    report_lines.append(f"   Abnormal: {abnormal_count}")
    report_lines.append("")
    
    # Patient Information
    if age is not None or gender is not None:
        report_lines.append("👤 Patient Information:")
        report_lines.append(f"   Age: {age if age is not None else 'Not found'}")
        report_lines.append(f"   Gender: {gender if gender is not None else 'Not found'}")
        report_lines.append("")
    
    # AI Analysis
    if phase2_available:
        overall_status = phase2_summary.get("overall_status", "Unknown")
        risk_level = phase2_summary.get("risk_level", "Unknown")
        ai_confidence = phase2_summary.get("ai_confidence", "Unknown")
        
        report_lines.append("🤖 AI Analysis:")
        report_lines.append(f"   Overall Status: {overall_status}")
        report_lines.append(f"   Risk Level: {risk_level}")
        report_lines.append(f"   AI Confidence: {ai_confidence}")
        report_lines.append("")
        
        # AI Recommendations
        recommendations = phase2_summary.get("recommendations", {})
        lifestyle_recs = recommendations.get("lifestyle", [])
        if lifestyle_recs:
            report_lines.append("💡 AI Recommendations:")
            for i, rec in enumerate(lifestyle_recs, 1):
                report_lines.append(f"   {i}. {rec}")
            report_lines.append("")
    
    # Abnormal Results
    abnormal_findings = interpretation.get("abnormal_parameters", [])
    if abnormal_findings:
        report_lines.append("⚠️ Abnormal Results:")
        for finding in abnormal_findings:
            status_emoji = "🔻" if finding.get("status") == "LOW" else "🔺"
            param_name = finding.get('parameter', 'Unknown')
            value = finding.get('value', 'Unknown')
            status = finding.get('status', 'Unknown')
            reference = finding.get('reference', 'Unknown')
            
            report_lines.append(f"   {status_emoji} {param_name}: {value} ({status})")
            report_lines.append(f"      Normal Range: {reference}")
        report_lines.append("")
    
    # Medical Disclaimer
    report_lines.append("⚠️ Medical Disclaimer:")
    report_lines.append("   This analysis is for informational purposes only.")
    report_lines.append("   Always consult healthcare professionals for medical decisions.")
    
    return "\n".join(report_lines)



st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

# Custom CSS for modern interface
st.markdown("""
<style>
.stButton > button {
    border-radius: 20px;
    border: none;
    background: linear-gradient(90deg, #0084ff, #00a8ff);
    color: white;
    font-weight: 500;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 132, 255, 0.3);
}

.stMetric {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #e9ecef;
}
</style>
""", unsafe_allow_html=True)

# Auto-start Ollama
@st.cache_resource
def initialize_ollama():
    """Initialize Ollama service on app startup"""
    with st.spinner("🚀 Starting AI service..."):
        setup_result = auto_start_ollama()
        return setup_result

# Initialize Ollama
ollama_setup = initialize_ollama()

st.title("🩺 Blood Report Analyzer")
st.markdown("AI-powered medical report analysis with automatic demographic extraction")

# Show Ollama status
if ollama_setup["ready"]:
    st.success("🤖 AI Analysis Ready")
else:
    st.warning("⚠️ AI Analysis Limited")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your medical report",
    type=["pdf", "png", "jpg", "jpeg", "json", "csv"],
    help="Supported: PDF, PNG, JPG, JPEG, JSON, CSV"
)

if uploaded_file is not None:
    st.success(f"📄 Processing: {uploaded_file.name}")
    
    with st.spinner("🔍 Analyzing your medical report..."):
        try:
            # Extract data and demographics automatically
            ingestion_result = extract_text_from_file(uploaded_file)
            
            # Parse ingestion result
            try:
                result_data = json.loads(ingestion_result)
                
                # Handle different file types
                if "file_type" in result_data:
                    file_type = result_data["file_type"]
                    
                    if file_type == "CSV":
                        st.success(f"✅ {file_type} file processed")
                        st.info("CSV files are processed as-is. For medical analysis, please upload a blood report image or PDF.")
                        st.stop()
                
                # Extract demographics and medical data
                age = None
                gender = None
                
                # Initialize parsed_data if not already set by JSON processing
                if 'parsed_data' not in locals():
                    parsed_data = {}
                
                # For medically processed files with automatic demographic extraction
                if "medical_parameters" in result_data or "phase1_extraction_csv" in result_data:
                    # Get Phase-1 extraction with demographics
                    phase1_csv = result_data.get("phase1_extraction_csv", "")
                    
                    if phase1_csv and phase1_csv.strip():
                        # Extract demographics from CSV
                        try:
                            import pandas as pd
                            csv_df = pd.read_csv(io.StringIO(phase1_csv))
                            if not csv_df.empty and 'age' in csv_df.columns and 'gender' in csv_df.columns:
                                # Get demographics from first row
                                age_val = csv_df['age'].iloc[0]
                                gender_val = csv_df['gender'].iloc[0]
                                
                                if age_val != 'NA':
                                    age = int(age_val)
                                if gender_val != 'NA':
                                    gender = gender_val
                        except Exception as e:
                            pass  # Continue without demographics if extraction fails
                    
                    # Convert medical parameters to parser format
                    medical_params = result_data.get("medical_parameters", [])
                    for param in medical_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param.get("confidence", "0.95"),
                            "status": param.get("status", "UNKNOWN")
                        }
                
                # For OCR-processed files (fallback)
                elif "parameters" in result_data:
                    extracted_params = result_data["parameters"]
                    for param in extracted_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param["confidence"]
                        }
                else:
                    # Fallback to old format
                    parsed_data = parse_blood_report(ingestion_result)
                    
            except json.JSONDecodeError:
                # Fallback for plain text
                parsed_data = parse_blood_report(ingestion_result)
            
            # Show extracted demographics if found
            if age is not None or gender is not None:
                st.success("👤 **Demographics automatically extracted:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Age", f"{age} years" if age is not None else "Not found")
                with col2:
                    st.metric("Gender", gender if gender is not None else "Not found")
            else:
                st.info("👤 Demographics not found in report")
            
            st.divider()
            
            # Validate and analyze
            if not parsed_data:
                st.error("❌ No medical parameters detected. Please check if the report format is supported.")
                st.info("**Possible reasons:**")
                st.info("• Image quality too low for OCR")
                st.info("• Report format not supported")
                st.info("• No tabular medical data found")
                st.stop()
            
            # Ensure we have valid data structure
            if not isinstance(parsed_data, dict) or len(parsed_data) == 0:
                st.error("❌ Invalid data structure detected.")
                st.stop()
            
            validated_data = validate_parameters(parsed_data)
            
            # Ensure validated_data is not empty
            if not validated_data:
                st.error("❌ No valid parameters after validation.")
                st.stop()
                
            interpretation = interpret_results(validated_data)
            
            # Show key results summary
            st.subheader("📊 Analysis Results")
            
            # Safely extract summary with defaults
            summary = interpretation.get("summary", {})
            total_params = summary.get("total_parameters", 0)
            normal_count = summary.get("normal", 0)
            low_count = summary.get("low", 0)
            high_count = summary.get("high", 0)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Tests", total_params)
            with col2:
                st.metric("Normal", normal_count, delta="✓" if normal_count > 0 else None)
            with col3:
                st.metric("Low", low_count, delta="⚠" if low_count > 0 else None, delta_color="inverse")
            with col4:
                st.metric("High", high_count, delta="⚠" if high_count > 0 else None, delta_color="inverse")
            
            # Show abnormal parameters if any
            abnormal_params = interpretation.get("abnormal_parameters", [])
            if abnormal_params:
                st.warning("⚠️ **Abnormal Results Found:**")
                for param in abnormal_params:
                    status_emoji = "🔻" if param.get("status") == "LOW" else "🔺"
                    st.write(f"{status_emoji} **{param.get('parameter', 'Unknown')}**: {param.get('value', 'Unknown')} ({param.get('status', 'Unknown')}) - Normal: {param.get('reference', 'Unknown')}")
            else:
                st.success("✅ All parameters are within normal ranges")
            
            st.divider()
            
            # AI Analysis Section (simplified)
            st.subheader("🤖 AI Analysis")
            
            # Convert to ML CSV for Phase-2
            ml_csv = json_to_ml_csv(ingestion_result)
            
            # Check Phase-2 requirements
            phase2_req = check_phase2_requirements()
            
            if phase2_req["status"] == "ready":
                with st.spinner("Running AI analysis..."):
                    try:
                        # Process through Phase-2 with demographic data
                        phase2_integration = integrate_phase2_analysis(ml_csv, age=age, gender=gender)
                        
                        if phase2_integration.get("phase2_summary", {}).get("available", False):
                            summary = phase2_integration["phase2_summary"]
                            
                            # Display key AI metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Overall Status", summary.get("overall_status", "Unknown"))
                            with col2:
                                st.metric("Risk Level", summary.get("risk_level", "Unknown"))
                            with col3:
                                st.metric("AI Confidence", summary.get("ai_confidence", "Unknown"))
                            
                            # Show AI recommendations if available
                            recommendations = summary.get("recommendations", {})
                            lifestyle_recs = recommendations.get("lifestyle", [])
                            if lifestyle_recs:
                                st.info("**AI Recommendations:**")
                                for rec in lifestyle_recs[:3]:  # Top 3
                                    st.write(f"• {rec}")
                            
                        else:
                            st.warning("AI analysis not available for this report")
                            
                    except Exception as e:
                        st.error(f"AI Analysis Error: {str(e)}")
                        phase2_integration = None
                        
            else:
                st.warning("⚠️ AI Analysis requires Ollama with Mistral 7B model")
                phase2_integration = None
            
            st.divider()
            
            # Generate and show clean text report with Read More functionality
            st.subheader("📋 Medical Report")
            
            # Generate the clean text report
            clean_report = generate_clean_text_report(
                uploaded_file.name,
                validated_data,
                interpretation,
                phase2_integration if 'phase2_integration' in locals() else None,
                age=age,
                gender=gender
            )
            
            # Create a summary version (first part of the report)
            summary_data = interpretation.get("summary", {})
            total_params = summary_data.get("total_parameters", 0)
            normal_count = summary_data.get("normal", 0)
            abnormal_count = summary_data.get("low", 0) + summary_data.get("high", 0)
            
            # Show compact summary first (clean text format)
            st.markdown(f"""
**🩺 Medical Report Summary**

**📊 Quick Overview:**
- Total Tests: {total_params}
- Normal: {normal_count}
- Abnormal: {abnormal_count}
            """)
            
            # Add Read More expandable section with clean text
            with st.expander("📄 Read More - Full Medical Report"):
                st.text(clean_report)
            
            # Download options
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate text report for download
                report_text = f"""
MEDICAL REPORT SUMMARY
{'='*50}

File: {uploaded_file.name}
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Patient Information:
- Age: {age if age is not None else 'Not found'}
- Gender: {gender if gender is not None else 'Not found'}

Results Summary:
- Total Tests: {total_params}
- Normal: {normal_count}
- Abnormal: {low_count + high_count}

Abnormal Results:
"""
                abnormal_params = interpretation.get("abnormal_parameters", [])
                for param in abnormal_params:
                    report_text += f"- {param.get('parameter', 'Unknown')}: {param.get('value', 'Unknown')} ({param.get('status', 'Unknown')}) - Normal: {param.get('reference', 'Unknown')}\n"
                
                report_text += """

MEDICAL DISCLAIMER:
This analysis is for informational purposes only. Always consult 
healthcare professionals for medical decisions.
"""
                
                st.download_button(
                    label="📄 Download Report",
                    data=report_text,
                    file_name=f"medical_report_{uploaded_file.name.split('.')[0]}.txt",
                    mime="text/plain"
                )
            
            with col2:
                st.download_button(
                    label="📊 Download CSV Data",
                    data=ml_csv,
                    file_name=f"medical_data_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv"
                )
            
            # Chat Interface Section
            st.divider()
            st.subheader("💬 AI Medical Assistant")
            
            # Initialize Q&A assistant if Phase-2 analysis is available
            if 'phase2_integration' in locals() and phase2_integration and phase2_integration.get("phase2_summary", {}).get("available", False):
                # Import Q&A assistant
                from core.qa_assistant import create_qa_assistant
                
                # Create assistant with analysis data
                qa_assistant = create_qa_assistant(phase2_integration)
                
                # Create and render chat interface
                chat_interface = create_medical_chat_interface(
                    qa_assistant, 
                    session_key=f"medical_chat_{uploaded_file.name}"
                )
                
                # Render the complete chat interface
                chat_interface.render_complete_interface()
                
            else:
                st.info("🤖 **AI Chat requires enhanced analysis**")
                st.markdown("Upload a blood report and ensure AI analysis is available to enable chat.")
            
        except Exception as e:
            st.error(f"❌ Processing Error: {str(e)}")
            
            # Add debug information
            with st.expander("🔍 Debug Information"):
                st.write("**Error Details:**")
                st.code(str(e))
                
                if 'parsed_data' in locals():
                    st.write(f"**Parsed Data Keys:** {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dictionary'}")
                    st.write(f"**Parsed Data Length:** {len(parsed_data) if parsed_data else 0}")
                
                if 'validated_data' in locals():
                    st.write(f"**Validated Data Keys:** {list(validated_data.keys()) if isinstance(validated_data, dict) else 'Not a dictionary'}")
                    st.write(f"**Validated Data Length:** {len(validated_data) if validated_data else 0}")
                
                if 'interpretation' in locals():
                    st.write(f"**Interpretation Structure:** {list(interpretation.keys()) if isinstance(interpretation, dict) else 'Not a dictionary'}")
                    if isinstance(interpretation, dict) and 'summary' in interpretation:
                        st.write(f"**Summary Keys:** {list(interpretation['summary'].keys())}")
            
            st.info("**Troubleshooting Tips:**")
            st.info("• Try uploading a clearer image")
            st.info("• Ensure the report contains tabular medical data")
            st.info("• Check if the file format is supported")
            st.info("• Try a different blood report format")

else:
    st.info("👆 Upload a report to begin analysis")
    st.markdown("""
    ### How it works:
    1. **Upload** your blood report (PDF, image, or data file)
    2. **Automatic extraction** of test results and demographics
    3. **AI analysis** with medical insights
    4. **Chat** with AI assistant about your results
    """)