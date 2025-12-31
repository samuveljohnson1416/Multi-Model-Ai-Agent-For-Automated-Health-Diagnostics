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


def generate_final_report(filename, parsed_data, validated_data, interpretation, ml_csv, phase2_result=None, age=None, gender=None):
    """Generate comprehensive final medical report"""
    
    # Extract basic information
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_params = interpretation["summary"]["total_parameters"]
    normal_count = interpretation["summary"]["normal"]
    abnormal_count = interpretation["summary"]["low"] + interpretation["summary"]["high"]
    
    # Phase-2 information
    phase2_available = False
    phase2_summary = {}
    if phase2_result and phase2_result.get("phase2_summary", {}).get("available"):
        phase2_available = True
        phase2_summary = phase2_result["phase2_summary"]
    
    # Calculate success rate safely
    success_rate = safe_percentage(normal_count, total_params, 1)
    
    # Add demographic information if provided
    demographic_section = ""
    if age is not None or gender is not None:
        demographic_section = f"""
        <div style="background-color: #e8f5e8; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0;">
            <h4 style="color: #28a745; margin-bottom: 10px;">👤 Patient Demographics (Milestone-2 Enhanced)</h4>
            <p><strong>Age:</strong> {age if age is not None else 'Not provided'}</p>
            <p><strong>Gender:</strong> {gender if gender is not None else 'Not provided'}</p>
            <p><strong>Contextual Analysis:</strong> ✅ Model-3 Applied for age/gender-specific insights</p>
        </div>
        """
    
    # Generate HTML report
    report_html = f"""
    <div style="border: 2px solid #1f77b4; border-radius: 10px; padding: 20px; margin: 10px 0; background-color: #f8f9fa;">
        <h2 style="color: #1f77b4; text-align: center; margin-bottom: 20px;">
            🩺 COMPREHENSIVE MEDICAL REPORT
        </h2>
        
        {demographic_section}
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div>
                <h4 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">📄 Report Information</h4>
                <p><strong>File Name:</strong> {filename}</p>
                <p><strong>Analysis Date:</strong> {timestamp}</p>
                <p><strong>Processing Method:</strong> Multi-Agent AI System</p>
                <p><strong>AI Enhancement:</strong> {'✅ Phase-2 Mistral AI' if phase2_available else '❌ Phase-1 Only'}</p>
            </div>
            
            <div>
                <h4 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">📊 Summary Statistics</h4>
                <p><strong>Total Parameters:</strong> {total_params}</p>
                <p><strong>Normal Results:</strong> <span style="color: green;">{normal_count}</span></p>
                <p><strong>Abnormal Results:</strong> <span style="color: red;">{abnormal_count}</span></p>
                <p><strong>Success Rate:</strong> {success_rate}%</p>
            </div>
        </div>
    """
    
    # Add Phase-2 AI Analysis if available
    if phase2_available:
        overall_status = phase2_summary.get("overall_status", "Unknown")
        risk_level = phase2_summary.get("risk_level", "Unknown")
        ai_confidence = phase2_summary.get("ai_confidence", "Unknown")
        
        status_color = "#28a745" if overall_status == "Normal" else "#ffc107" if "Minor" in overall_status else "#dc3545"
        risk_color = "#28a745" if risk_level == "Low" else "#ffc107" if risk_level == "Moderate" else "#dc3545"
        
        report_html += f"""
        <div style="background-color: #e8f4fd; border-left: 4px solid #1f77b4; padding: 15px; margin: 15px 0;">
            <h4 style="color: #1f77b4; margin-bottom: 15px;">🤖 AI-Powered Analysis (Mistral 7B)</h4>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div style="text-align: center; padding: 10px; background-color: white; border-radius: 5px;">
                    <strong>Overall Status</strong><br>
                    <span style="color: {status_color}; font-size: 1.2em; font-weight: bold;">{overall_status}</span>
                </div>
                <div style="text-align: center; padding: 10px; background-color: white; border-radius: 5px;">
                    <strong>Risk Level</strong><br>
                    <span style="color: {risk_color}; font-size: 1.2em; font-weight: bold;">{risk_level}</span>
                </div>
                <div style="text-align: center; padding: 10px; background-color: white; border-radius: 5px;">
                    <strong>AI Confidence</strong><br>
                    <span style="color: #17a2b8; font-size: 1.2em; font-weight: bold;">{ai_confidence}</span>
                </div>
            </div>
        """
        
        # Add AI-detected abnormal findings
        abnormal_findings = phase2_summary.get("abnormal_findings", [])
        if abnormal_findings:
            report_html += """
            <h5 style="color: #dc3545; margin-bottom: 10px;">⚠️ AI-Detected Abnormal Findings:</h5>
            <ul style="margin-bottom: 15px;">
            """
            for finding in abnormal_findings[:5]:  # Top 5
                status_emoji = "🔻" if finding.get("status") == "Low" else "🔺" if finding.get("status") == "High" else "⚠️"
                report_html += f"""
                <li><strong>{finding.get('test', 'Unknown')}</strong>: {finding.get('value', 'Unknown')} 
                    <span style="color: #dc3545;">({finding.get('status', 'Unknown')})</span> 
                    - Reference: {finding.get('reference', 'Unknown')} {status_emoji}</li>
                """
            report_html += "</ul>"
        
        # Add AI recommendations
        recommendations = phase2_summary.get("recommendations", {})
        lifestyle_recs = recommendations.get("lifestyle", [])
        if lifestyle_recs:
            report_html += """
            <h5 style="color: #28a745; margin-bottom: 10px;">💡 AI Lifestyle Recommendations:</h5>
            <ul style="margin-bottom: 15px;">
            """
            for rec in lifestyle_recs[:3]:  # Top 3
                report_html += f"<li>{rec}</li>"
            report_html += "</ul>"
        
        report_html += "</div>"
    
    # Add detailed parameter results
    report_html += """
    <div style="margin-top: 20px;">
        <h4 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">🔬 Detailed Laboratory Results</h4>
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="background-color: #3498db; color: white;">
                        <th style="padding: 10px; border: 1px solid #ddd;">Parameter</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Value</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Unit</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Reference Range</th>
                        <th style="padding: 10px; border: 1px solid #ddd;">Status</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add parameter rows
    for param_name, param_data in validated_data.items():
        status = param_data.get("status", "Unknown")
        status_color = "#28a745" if status == "NORMAL" else "#dc3545"
        status_emoji = "✅" if status == "NORMAL" else "⚠️"
        
        report_html += f"""
        <tr style="background-color: {'#f8f9fa' if status == 'NORMAL' else '#fff5f5'};">
            <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{param_name}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{param_data.get('value', 'N/A')}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{param_data.get('unit', 'N/A')}</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{param_data.get('reference_range', 'N/A')}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: {status_color}; font-weight: bold;">
                {status} {status_emoji}
            </td>
        </tr>
        """
    
    report_html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    
    # Add medical disclaimer
    report_html += """
    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin-top: 20px;">
        <h5 style="color: #856404; margin-bottom: 10px;">⚠️ Important Medical Disclaimer</h5>
        <p style="color: #856404; margin: 0; font-size: 0.9em;">
            This automated analysis is for informational purposes only and does not constitute medical advice, 
            diagnosis, or treatment recommendations. Always consult with qualified healthcare professionals 
            for proper medical evaluation and treatment decisions. The AI analysis should be used as a 
            supplementary tool only.
        </p>
    </div>
    """
    
    # Add technical information
    report_html += f"""
    <div style="margin-top: 20px; padding: 15px; background-color: #f1f3f4; border-radius: 5px;">
        <h5 style="color: #5f6368; margin-bottom: 10px;">🔧 Technical Information</h5>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em; color: #5f6368;">
            <div>
                <strong>Processing Pipeline:</strong><br>
                • Phase-1: Multi-Agent OCR Extraction<br>
                • Medical Parameter Validation<br>
                {'• Phase-2: Mistral 7B AI Analysis<br>' if phase2_available else ''}
                • Completeness Guarantee Applied
            </div>
            <div>
                <strong>Data Safety:</strong><br>
                • Zero Hallucination Policy<br>
                • Local Processing Only<br>
                • No Data Upload to External Servers<br>
                • ML-Ready CSV Export Available
            </div>
        </div>
    </div>
    </div>
    """
    
    # Generate text version for download
    success_rate = ((normal_count / total_params) * 100) if total_params > 0 else 0
    
    report_text = f"""
COMPREHENSIVE MEDICAL REPORT
{'='*50}

Report Information:
- File Name: {filename}
- Analysis Date: {timestamp}
- Processing Method: Multi-Agent AI System
- AI Enhancement: {'Phase-2 Mistral AI' if phase2_available else 'Phase-1 Only'}

Patient Demographics:
- Age: {age if age is not None else 'Not provided'}
- Gender: {gender if gender is not None else 'Not provided'}
- Contextual Analysis: {'Milestone-2 Model-3 Applied' if (age is not None or gender is not None) else 'Not Available'}

Summary Statistics:
- Total Parameters: {total_params}
- Normal Results: {normal_count}
- Abnormal Results: {abnormal_count}
- Success Rate: {success_rate:.1f}%

"""
    
    if phase2_available:
        report_text += f"""
AI-Powered Analysis (Mistral 7B):
- Overall Status: {phase2_summary.get('overall_status', 'Unknown')}
- Risk Level: {phase2_summary.get('risk_level', 'Unknown')}
- AI Confidence: {phase2_summary.get('ai_confidence', 'Unknown')}

"""
        
        abnormal_findings = phase2_summary.get("abnormal_findings", [])
        if abnormal_findings:
            report_text += "AI-Detected Abnormal Findings:\n"
            for finding in abnormal_findings[:5]:
                report_text += f"- {finding.get('test', 'Unknown')}: {finding.get('value', 'Unknown')} ({finding.get('status', 'Unknown')}) - Ref: {finding.get('reference', 'Unknown')}\n"
            report_text += "\n"
        
        recommendations = phase2_summary.get("recommendations", {})
        lifestyle_recs = recommendations.get("lifestyle", [])
        if lifestyle_recs:
            report_text += "AI Lifestyle Recommendations:\n"
            for rec in lifestyle_recs[:3]:
                report_text += f"- {rec}\n"
            report_text += "\n"
    
    report_text += """
Detailed Laboratory Results:
"""
    for param_name, param_data in validated_data.items():
        status = param_data.get("status", "Unknown")
        report_text += f"- {param_name}: {param_data.get('value', 'N/A')} {param_data.get('unit', '')} ({status}) [Ref: {param_data.get('reference_range', 'N/A')}]\n"
    
    report_text += f"""

MEDICAL DISCLAIMER:
This automated analysis is for informational purposes only and does not constitute 
medical advice, diagnosis, or treatment recommendations. Always consult with qualified 
healthcare professionals for proper medical evaluation and treatment decisions.

Technical Information:
- Processing: Multi-Agent AI System with Completeness Guarantee
- Data Safety: Zero Hallucination, Local Processing Only
- AI Model: {'Mistral 7B Instruct' if phase2_available else 'Rule-based Analysis'}
- Generated: {timestamp}
"""
    
    # Generate complete JSON
    complete_analysis = {
        "report_metadata": {
            "filename": filename,
            "timestamp": timestamp,
            "total_parameters": total_params,
            "normal_count": normal_count,
            "abnormal_count": abnormal_count,
            "phase2_available": phase2_available
        },
        "parsed_data": parsed_data,
        "validated_data": validated_data,
        "interpretation": interpretation,
        "ml_csv_data": ml_csv,
        "phase2_analysis": phase2_result if phase2_available else None
    }
    
    return {
        "report_html": report_html,
        "report_text": report_text,
        "complete_json": json.dumps(complete_analysis, indent=2),
        "ai_analysis_json": json.dumps(phase2_result, indent=2) if phase2_available else "{}",
        "phase2_available": phase2_available
    }

st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

# Custom CSS for modern chat interface
st.markdown("""
<style>
/* Chat message styling */
.chat-message {
    padding: 10px;
    margin: 5px 0;
    border-radius: 10px;
    max-width: 80%;
    word-wrap: break-word;
}

.user-message {
    background-color: #0084ff;
    color: white;
    margin-left: auto;
    text-align: right;
}

.assistant-message {
    background-color: #f1f3f4;
    color: #333;
    margin-right: auto;
}

/* Chat input styling */
.stTextInput > div > div > input {
    border-radius: 20px;
    border: 2px solid #e0e0e0;
    padding: 10px 15px;
}

.stTextInput > div > div > input:focus {
    border-color: #0084ff;
    box-shadow: 0 0 0 2px rgba(0, 132, 255, 0.2);
}

/* Button styling */
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

/* Quick button styling */
div[data-testid="column"] .stButton > button {
    background: linear-gradient(90deg, #f8f9fa, #e9ecef);
    color: #495057;
    border: 1px solid #dee2e6;
    font-size: 0.9em;
}

div[data-testid="column"] .stButton > button:hover {
    background: linear-gradient(90deg, #e9ecef, #dee2e6);
    transform: translateY(-1px);
}

/* Chat container */
.chat-container {
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    background-color: #fafafa;
}

/* Typing indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    padding: 10px;
    color: #666;
    font-style: italic;
}

.typing-dots {
    display: inline-block;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background-color: #666;
    margin: 0 1px;
    animation: typing 1.4s infinite ease-in-out;
}

.typing-dots:nth-child(1) { animation-delay: -0.32s; }
.typing-dots:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
    0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
    40% { transform: scale(1); opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# Auto-start Ollama when the application launches
@st.cache_resource
def initialize_ollama():
    """Initialize Ollama service on app startup"""
    with st.spinner("🚀 Starting Ollama AI service..."):
        setup_result = auto_start_ollama()
        return setup_result

# Initialize Ollama
ollama_setup = initialize_ollama()

st.title("Blood Report Analyzer – Milestone-2 Compliant")
st.markdown("Advanced AI analysis with pattern recognition and contextual insights.")

# Show Ollama status
if ollama_setup["ready"]:
    st.success("🤖 AI Analysis Ready - Ollama & Mistral 7B loaded")
else:
    st.warning("⚠️ AI Analysis Limited - Ollama setup incomplete")
    with st.expander("Ollama Setup Details"):
        for message in ollama_setup["messages"]:
            st.write(message)

st.divider()

uploaded_file = st.file_uploader(
    "Upload your medical report",
    type=["pdf", "png", "jpg", "jpeg", "json", "csv"],
    help="Supported: PDF, PNG, JPG, JPEG, JSON, CSV"
)

# Demographic inputs for Milestone-2 contextual analysis
st.subheader("👤 Optional: Demographic Information (for enhanced AI analysis)")
col1, col2 = st.columns(2)

with col1:
    age = st.number_input(
        "Age (years)", 
        min_value=0, 
        max_value=120, 
        value=None,
        placeholder="Enter age for contextual analysis",
        help="Age helps provide age-specific reference context"
    )

with col2:
    gender = st.selectbox(
        "Gender",
        options=[None, "Male", "Female", "Other"],
        index=0,
        help="Gender helps provide gender-specific reference context"
    )

# Show demographic status
if age is not None or gender is not None:
    demo_info = []
    if age is not None:
        demo_info.append(f"Age: {age}")
    if gender is not None:
        demo_info.append(f"Gender: {gender}")
    st.info(f"🤖 Milestone-2 contextual analysis enabled: {', '.join(demo_info)}")
else:
    st.info("💡 Tip: Provide age/gender for enhanced AI contextual analysis (Milestone-2 Model-3)")

st.divider()

if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    with st.spinner("Processing..."):
        try:
            # Data Ingestion - Format-specific processing
            st.subheader("📄 Step 1: Data Ingestion")
            ingestion_result = extract_text_from_file(uploaded_file)
            
            # Parse ingestion result
            try:
                result_data = json.loads(ingestion_result)
                
                # Handle different file types
                if "file_type" in result_data:
                    file_type = result_data["file_type"]
                    
                    if file_type == "CSV":
                        st.success("✅ CSV file detected - returned as-is")
                        st.text_area("CSV Content", result_data["csv_content"], height=200)
                        st.info(result_data["message"])
                        
                        # Skip further processing for CSV
                        st.stop()
                        
                    elif file_type == "JSON":
                        st.success("✅ JSON file detected - parsed directly")
                        st.json(result_data["data"])
                        st.info(result_data["message"])
                        
                        # Skip further processing for JSON
                        st.stop()
                
                # For medically processed files with multiple extraction agents
                if "medical_parameters" in result_data or "phase1_extraction_csv" in result_data:
                    processing_agents = result_data.get("processing_agents", {})
                    phase1_agent = processing_agents.get("phase1_extractor", "")
                    validation_agent = processing_agents.get("validation_agent", "")
                    table_extractor = processing_agents.get("table_extractor", "")
                    
                    # Show processing status
                    agents_used = [agent for agent in [phase1_agent, validation_agent, table_extractor] if agent]
                    if len(agents_used) > 1:
                        st.success(f"✅ Multi-Agent Processing: {len(agents_used)} specialized agents used")
                    elif agents_used:
                        st.success(f"✅ {agents_used[0]}")
                    else:
                        st.success("✅ OCR and document processing completed")
                    
                    # Display Phase-1 Image Extraction (PRIMARY for scanned images)
                    phase1_csv = result_data.get("phase1_extraction_csv", "")
                    if phase1_csv and phase1_csv.strip():
                        st.subheader("🖼️ Phase-1 Medical Image Extraction (PRIMARY)")
                        st.info("**Image-aware OCR reconstruction - Optimized for scanned medical images**")
                        
                        # Display CSV content
                        try:
                            import pandas as pd
                            csv_df = pd.read_csv(io.StringIO(phase1_csv))
                            if not csv_df.empty:
                                st.dataframe(csv_df, width='stretch')
                                
                                # Highlight key features
                                st.success(f"✅ Extracted {len(csv_df)} laboratory tests using image-aware reconstruction")
                                
                                # Download button for Phase-1 extraction
                                st.download_button(
                                    label="📥 Download Phase-1 Image CSV",
                                    data=phase1_csv,
                                    file_name=f"phase1_image_extraction_{uploaded_file.name.split('.')[0]}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.warning("OCR failure detected - no valid laboratory data found")
                                st.info("This may indicate: low image quality, no tabular data, or unsupported format")
                        except Exception as e:
                            st.text_area("Raw Phase-1 CSV Data", phase1_csv, height=150)
                    
                    # Display additional table extraction if different from Phase-1
                    table_csv = result_data.get("table_extraction_csv", "")
                    if table_csv and table_csv.strip() and table_csv != phase1_csv:
                        st.subheader("📊 Alternative Table Extraction")
                        st.info("**Secondary extraction method - Pure table parsing**")
                        
                        try:
                            csv_df = pd.read_csv(io.StringIO(table_csv))
                            if not csv_df.empty:
                                st.dataframe(csv_df, width='stretch')
                                
                                st.download_button(
                                    label="📥 Download Alternative Table CSV",
                                    data=table_csv,
                                    file_name=f"table_extraction_{uploaded_file.name.split('.')[0]}.csv",
                                    mime="text/csv"
                                )
                        except Exception as e:
                            st.text_area("Raw Table CSV Data", table_csv, height=150)
                    
                    # Display medical validation summary if available
                    medical_params = result_data.get("medical_parameters", [])
                    if medical_params:
                        st.subheader("🔬 Medical Validation Summary")
                        st.info("**Clinical interpretation with status classification**")
                        
                        # Count status types
                        status_counts = {"Normal": 0, "Low": 0, "High": 0, "UNKNOWN": 0}
                        for param in medical_params:
                            status = param.get("status", "UNKNOWN")
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total Tests", len(medical_params))
                        with col2:
                            st.metric("Normal", status_counts["Normal"], delta="✓" if status_counts["Normal"] > 0 else None)
                        with col3:
                            st.metric("Low", status_counts["Low"], delta="⚠" if status_counts["Low"] > 0 else None, delta_color="inverse")
                        with col4:
                            st.metric("High", status_counts["High"], delta="⚠" if status_counts["High"] > 0 else None, delta_color="inverse")
                        with col5:
                            st.metric("Unknown", status_counts["UNKNOWN"], delta="?" if status_counts["UNKNOWN"] > 0 else None, delta_color="off")
                        
                        # Show abnormal results
                        abnormal_params = [p for p in medical_params if p.get("status") in ["Low", "High"]]
                        if abnormal_params:
                            st.warning("**Abnormal Results Detected:**")
                            for param in abnormal_params:
                                status_emoji = "🔻" if param["status"] == "Low" else "🔺"
                                st.write(f"{status_emoji} **{param['name']}**: {param['value']} {param['unit']} ({param['status']}) - Reference: {param['reference_range']}")
                    
                    # Convert medical parameters to parser format for downstream processing
                    parsed_data = {}
                    for param in medical_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param.get("confidence", "0.95"),
                            "status": param.get("status", "UNKNOWN")
                        }
                
                # For OCR-processed files (old format)
                elif "parameters" in result_data:
                    st.success("✅ OCR and extraction completed")
                    extracted_params = result_data["parameters"]
                    
                    if "raw_text" in result_data:
                        st.text_area("Extracted Text", result_data["raw_text"], height=200)
                    
                    # Convert to parser format
                    parsed_data = {}
                    for param in extracted_params:
                        parsed_data[param["name"]] = {
                            "value": param["value"],
                            "unit": param["unit"],
                            "reference_range": param["reference_range"],
                            "confidence": param["confidence"]
                        }
                else:
                    # Fallback to old format
                    st.text_area("Extracted Text", ingestion_result, height=200)
                    parsed_data = parse_blood_report(ingestion_result)
                    
            except json.JSONDecodeError:
                # Fallback for plain text
                st.text_area("Extracted Text", ingestion_result, height=200)
                parsed_data = parse_blood_report(ingestion_result)
            
            st.caption(f"Processing completed")
            
            st.divider()
            
            # Parse data
            st.subheader("🔍 Step 2: Extracted Parameters")
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
            ml_csv = json_to_ml_csv(ingestion_result)
            
            # Display CSV preview
            st.write("**ML-Ready CSV Preview:**")
            try:
                df_preview = pd.read_csv(io.StringIO(ml_csv))
                st.dataframe(df_preview, width='stretch')
                
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
            
            st.divider()
            
            # Phase-2 AI Analysis Section
            st.subheader("🤖 Phase-2 AI Analysis (Mistral 7B)")
            
            # Check Phase-2 requirements
            phase2_req = check_phase2_requirements()
            
            if phase2_req["status"] == "ready":
                st.success("✅ Mistral 7B Instruct model available")
                
                with st.spinner("Running Phase-2 AI analysis..."):
                    try:
                        # Debug: Check CSV content
                        if not ml_csv or ml_csv.strip() == "":
                            st.warning("No CSV data available for Phase-2 analysis")
                        else:
                            # Show CSV info for debugging
                            try:
                                debug_df = pd.read_csv(io.StringIO(ml_csv))
                                st.info(f"Processing {len(debug_df)} rows through Phase-2 AI...")
                            except:
                                st.warning("CSV format issue detected")
                        
                        # Process through Phase-2 with demographic data
                        phase2_integration = integrate_phase2_analysis(ml_csv, age=age, gender=gender)
                        
                        # Debug: Check integration result structure
                        if not isinstance(phase2_integration, dict):
                            st.error("Phase-2 integration returned invalid format")
                        elif "phase2_summary" not in phase2_integration:
                            st.error("Phase-2 integration missing summary")
                        else:
                            summary = phase2_integration["phase2_summary"]
                            
                            if summary.get("available", False):
                                # Display key metrics
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Overall Status", summary.get("overall_status", "Unknown"))
                                with col2:
                                    st.metric("Risk Level", summary.get("risk_level", "Unknown"))
                                with col3:
                                    st.metric("AI Confidence", summary.get("ai_confidence", "Unknown"))
                                with col4:
                                    metrics = summary.get("metrics", {})
                                    st.metric("Patterns Found", metrics.get("patterns_detected", 0))
                                
                                # Display AI analysis
                                display_text = phase2_integration.get("phase2_display_text", "No analysis available")
                                st.markdown(display_text)
                                
                                # Show abnormal findings
                                abnormal_findings = summary.get("abnormal_findings", [])
                                if abnormal_findings:
                                    st.warning("**AI-Detected Abnormal Findings:**")
                                    for finding in abnormal_findings:
                                        status_emoji = "🔻" if finding.get("status") == "Low" else "🔺" if finding.get("status") == "High" else "⚠️"
                                        test_name = finding.get("test", "Unknown")
                                        value = finding.get("value", "Unknown")
                                        status = finding.get("status", "Unknown")
                                        reference = finding.get("reference", "Unknown")
                                        st.write(f"{status_emoji} **{test_name}**: {value} ({status}) - Ref: {reference}")
                                
                                # Show AI recommendations
                                recommendations = summary.get("recommendations", {})
                                lifestyle_recs = recommendations.get("lifestyle", [])
                                if lifestyle_recs:
                                    st.info("**AI Lifestyle Recommendations:**")
                                    for rec in lifestyle_recs:
                                        st.write(f"• {rec}")
                                
                                # Medical disclaimer
                                st.warning("⚠️ **Medical Disclaimer**: This AI analysis is for informational purposes only. Always consult qualified healthcare professionals for medical decisions.")
                                
                                # Download Phase-2 results
                                phase2_full = phase2_integration.get("phase2_full_result", {})
                                phase2_json = json.dumps(phase2_full, indent=2)
                                st.download_button(
                                    label="📥 Download Phase-2 AI Analysis (JSON)",
                                    data=phase2_json,
                                    file_name=f"phase2_analysis_{uploaded_file.name.split('.')[0]}.json",
                                    mime="application/json"
                                )
                            else:
                                message = summary.get('message', 'Phase-2 analysis not available')
                                status = summary.get('status', 'unknown')
                                st.warning(f"Phase-2 Analysis ({status}): {message}")
                                
                                # Show debug info if available
                                phase2_full = phase2_integration.get("phase2_full_result", {})
                                if "error_details" in phase2_full:
                                    with st.expander("Debug Information"):
                                        st.text(phase2_full["error_details"])
                            
                    except Exception as e:
                        st.error(f"Phase-2 Analysis Error: {str(e)}")
                        st.info("Falling back to Phase-1 analysis only")
                        
            else:
                st.warning("⚠️ Phase-2 AI Analysis requires Ollama with Mistral 7B model")
                st.info(f"**Setup Instructions:**\n1. Install Ollama: https://ollama.ai\n2. Run: `{phase2_req['installation_command']}`\n3. Restart this application")
                st.code(phase2_req['installation_command'])
            
            st.divider()
            
            # Final Comprehensive Report Section
            st.subheader("📋 Final Medical Report")
            
            # Generate comprehensive report with demographic data
            final_report = generate_final_report(
                uploaded_file.name,
                parsed_data,
                validated_data,
                interpretation,
                ml_csv,
                phase2_integration if 'phase2_integration' in locals() else None,
                age=age,
                gender=gender
            )
            
            # Display the final report
            st.markdown(final_report["report_html"], unsafe_allow_html=True)
            
            # Download options for final report
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="📄 Download PDF Report",
                    data=final_report["report_text"],
                    file_name=f"medical_report_{uploaded_file.name.split('.')[0]}.txt",
                    mime="text/plain"
                )
            
            with col2:
                st.download_button(
                    label="📊 Download Complete Analysis (JSON)",
                    data=final_report["complete_json"],
                    file_name=f"complete_analysis_{uploaded_file.name.split('.')[0]}.json",
                    mime="application/json"
                )
            
            with col3:
                if final_report.get("phase2_available"):
                    st.download_button(
                        label="🤖 Download AI Analysis (JSON)",
                        data=final_report["ai_analysis_json"],
                        file_name=f"ai_analysis_{uploaded_file.name.split('.')[0]}.json",
                        mime="application/json"
                    )
                else:
                    st.info("AI Analysis not available")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please upload a valid blood report.")
            
        # Q&A Assistant Section - Modern Chat Interface
        st.divider()
        st.subheader("💬 AI Medical Assistant")
        st.markdown("Chat with your AI assistant about your blood report analysis. All responses are based on your actual medical data.")
        
        # Initialize Q&A assistant if Phase-2 analysis is available
        if 'phase2_integration' in locals() and phase2_integration.get("phase2_summary", {}).get("available", False):
            # Import Q&A assistant
            from core.qa_assistant import create_qa_assistant
            
            # Create assistant with analysis data
            qa_assistant = create_qa_assistant(phase2_integration)
            
            # Create and render modern chat interface
            chat_interface = create_medical_chat_interface(
                qa_assistant, 
                session_key=f"medical_chat_{uploaded_file.name}"
            )
            
            # Render the complete chat interface
            chat_interface.render_complete_interface()
            
        else:
            # Fallback when AI is not available
            st.info("🤖 **AI Chat Assistant Unavailable**")
            st.markdown("""
            The AI chat assistant requires Phase-2 analysis with Ollama and Mistral 7B.
            
            **To enable AI chat:**
            1. Ensure Ollama is running (should auto-start)
            2. Verify Mistral model: `ollama list`
            3. Upload and analyze your blood report
            
            **Current Status:** Phase-1 analysis available, AI chat disabled
            """)
            
            # Show basic analysis data viewer
            with st.expander("📊 View Analysis Data (No AI Chat)"):
                if 'interpretation' in locals():
                    st.json(interpretation)
                else:
                    st.info("No analysis data available. Please upload a blood report first.")
        
        st.divider()
else:
    st.info("👆 Upload a report to begin.")
    st.markdown("""
    ### How to use:
    1. Click **Browse files**
    2. Select your blood report
    3. Wait for analysis
    4. Review results
    """)
