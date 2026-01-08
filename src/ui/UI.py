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

# Multi-report system imports
from core.multi_report_manager import get_or_create_session, MultiReportManager
from core.multi_report_qa_assistant import create_multi_report_qa_assistant

# Enhanced AI Agent imports
from core.enhanced_ai_agent import create_enhanced_ai_agent


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

# Initialize session state for enhanced AI agent
if 'enhanced_ai_agent' not in st.session_state:
    st.session_state.enhanced_ai_agent = None
if 'ai_session_id' not in st.session_state:
    st.session_state.ai_session_id = None

# Initialize session state for multi-report management
if 'multi_report_session' not in st.session_state:
    st.session_state.multi_report_session = None
if 'current_reports' not in st.session_state:
    st.session_state.current_reports = {}
if 'comparison_available' not in st.session_state:
    st.session_state.comparison_available = False

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
st.markdown("AI-powered medical report analysis with enhanced intelligence, multi-report comparison, and goal-oriented assistance")

# Initialize Enhanced AI Agent
if not st.session_state.enhanced_ai_agent:
    st.session_state.enhanced_ai_agent = create_enhanced_ai_agent()
    st.session_state.ai_session_id = st.session_state.enhanced_ai_agent.start_user_session(
        session_type="analysis"
    )

# Show AI Agent status
agent_status = "🤖 Enhanced AI Agent Active" if st.session_state.enhanced_ai_agent else "⚠️ AI Agent Initializing"
st.success(agent_status)

# Show Ollama status
if ollama_setup["ready"]:
    st.success("🤖 AI Analysis Ready")
else:
    st.warning("⚠️ AI Analysis Limited")

# Multi-report session status
if st.session_state.multi_report_session:
    session_data = st.session_state.multi_report_session.get_all_reports()
    report_count = len(session_data['reports'])
    
    if report_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Session Reports", report_count)
        with col2:
            st.metric("🔄 Comparison", "Available" if st.session_state.comparison_available else "Single Report")
        with col3:
            if st.button("🗑️ Clear Session"):
                st.session_state.multi_report_session = None
                st.session_state.current_reports = {}
                st.session_state.comparison_available = False
                st.rerun()

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
            # Get or create multi-report session
            if not st.session_state.multi_report_session:
                st.session_state.multi_report_session = get_or_create_session()
            
            manager = st.session_state.multi_report_session
            
            # Extract raw text from file
            ingestion_result = extract_text_from_file(uploaded_file)
            
            # Parse ingestion result to get raw text
            try:
                result_data = json.loads(ingestion_result)
                
                # Handle different file types
                if "file_type" in result_data:
                    file_type = result_data["file_type"]
                    
                    if file_type == "CSV":
                        st.success(f"✅ {file_type} file processed")
                        st.info("CSV files are processed as-is. For medical analysis, please upload a blood report image or PDF.")
                        st.stop()
                
                # Get raw text for multi-report detection
                raw_text = result_data.get("raw_text", "")
                if not raw_text and "medical_parameters" in result_data:
                    # Reconstruct text from medical parameters for detection
                    params = result_data["medical_parameters"]
                    raw_text = f"Medical Report\n"
                    for param in params:
                        raw_text += f"{param['name']}: {param['value']} {param['unit']} (Ref: {param['reference_range']})\n"
                
            except json.JSONDecodeError:
                # Fallback for plain text
                raw_text = ingestion_result
            
            if not raw_text or len(raw_text.strip()) < 50:
                st.error("❌ No valid content detected in the uploaded file.")
                st.stop()
            
            # Process document through multi-report manager
            processing_result = manager.process_document(raw_text, uploaded_file.name)
            
            if processing_result['status'] == 'error':
                st.error(f"❌ {processing_result['message']}")
                st.stop()
            
            # Update session state
            st.session_state.current_reports = manager.analysis_results
            st.session_state.comparison_available = processing_result.get('comparison_available', False)
            
            # Display processing results
            st.success(f"✅ Document processed successfully!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Reports Detected", processing_result['report_count'])
            with col2:
                st.metric("✅ Valid Reports", processing_result['valid_reports'])
            with col3:
                st.metric("🔄 Comparison", "Available" if processing_result['comparison_available'] else "Not Available")
            
            st.divider()
            
            # Display individual report results
            valid_reports = [r for r in processing_result['reports'] if r['status'] == 'success']
            
            if not valid_reports:
                st.error("❌ No valid medical reports found in the document.")
                st.info("**Possible reasons:**")
                st.info("• Image quality too low for OCR")
                st.info("• Report format not supported") 
                st.info("• No tabular medical data found")
                st.stop()
            
            # Show results for each report
            for i, report_info in enumerate(valid_reports):
                report_id = report_info['report_id']
                analysis_data = manager.get_report_data(report_id)
                
                if not analysis_data:
                    continue
                
                # Create expandable section for each report
                with st.expander(f"📋 {report_id} - {report_info['parameters_count']} parameters", expanded=(i == 0)):
                    
                    # Extract data for display
                    validated_data = analysis_data.get('validated_data', {})
                    interpretation = analysis_data.get('interpretation', {})
                    phase2_result = analysis_data.get('phase2_result')
                    
                    # Extract demographics
                    age = None
                    gender = None
                    if phase2_result and 'phase2_full_result' in phase2_result:
                        demographics = phase2_result['phase2_full_result'].get('demographics', {})
                        age = demographics.get('age')
                        gender = demographics.get('gender')
                    
                    # Show demographics if found
                    if age is not None or gender is not None:
                        st.success("👤 **Demographics automatically extracted:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Age", f"{age} years" if age is not None else "Not found")
                        with col2:
                            st.metric("Gender", gender if gender is not None else "Not found")
                    
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
                    
                    # AI Analysis Section
                    if analysis_data.get('phase2_available', False) and phase2_result:
                        st.subheader("🤖 AI Analysis")
                        
                        if phase2_result.get("phase2_summary", {}).get("available", False):
                            summary_data = phase2_result["phase2_summary"]
                            
                            # Display key AI metrics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Overall Status", summary_data.get("overall_status", "Unknown"))
                            with col2:
                                st.metric("Risk Level", summary_data.get("risk_level", "Unknown"))
                            with col3:
                                st.metric("AI Confidence", summary_data.get("ai_confidence", "Unknown"))
                            
                            # Show AI recommendations if available
                            recommendations = summary_data.get("recommendations", {})
                            lifestyle_recs = recommendations.get("lifestyle", [])
                            if lifestyle_recs:
                                st.info("**AI Recommendations:**")
                                for rec in lifestyle_recs[:3]:  # Top 3
                                    st.write(f"• {rec}")
                        else:
                            st.warning("AI analysis not available for this report")
                    else:
                        st.info("🤖 **Enhanced AI analysis not available for this report**")
                    
                    # Generate and show clean text report
                    st.subheader("📋 Medical Report")
                    
                    # Generate the clean text report
                    clean_report = generate_clean_text_report(
                        uploaded_file.name,
                        validated_data,
                        interpretation,
                        phase2_result,
                        age=age,
                        gender=gender
                    )
                    
                    # Show compact summary first
                    st.markdown(f"""
**🩺 {report_id} Summary**

**📊 Quick Overview:**
- Total Tests: {total_params}
- Normal: {normal_count}
- Abnormal: {low_count + high_count}
                    """)
                    
                    # Add Read More expandable section
                    with st.expander(f"📄 Read More - Full {report_id} Report"):
                        st.text(clean_report)
                    
                    # Download options for individual report
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Generate text report for download
                        report_text = clean_report
                        
                        st.download_button(
                            label=f"📄 Download {report_id} Report",
                            data=report_text,
                            file_name=f"{report_id}_{uploaded_file.name.split('.')[0]}.txt",
                            mime="text/plain",
                            key=f"download_report_{report_id}"
                        )
                    
                    with col2:
                        ml_csv = analysis_data.get('ml_csv', '')
                        if ml_csv:
                            st.download_button(
                                label=f"📊 Download {report_id} CSV",
                                data=ml_csv,
                                file_name=f"{report_id}_{uploaded_file.name.split('.')[0]}.csv",
                                mime="text/csv",
                                key=f"download_csv_{report_id}"
                            )
            
            # Comparison Analysis Section (if multiple reports)
            if processing_result.get('comparison_available', False):
                st.divider()
                st.subheader("🔄 Comparative Analysis")
                
                comparison_data = manager.get_comparison_results()
                if comparison_data and comparison_data.get('status') == 'success':
                    
                    # Show comparison summary
                    summary = comparison_data.get('summary', {})
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Reports Compared", summary.get('total_reports', 0))
                    with col2:
                        st.metric("Parameters Compared", summary.get('parameters_compared', 0))
                    with col3:
                        st.metric("Improving", summary.get('improving_parameters', 0), delta="↗️")
                    with col4:
                        st.metric("Worsening", summary.get('worsening_parameters', 0), delta="↘️", delta_color="inverse")
                    
                    # Overall assessment
                    overall_assessment = summary.get('overall_assessment', 'stable')
                    if overall_assessment == 'improving':
                        st.success(f"📈 **Overall Trend: Improving**")
                    elif overall_assessment == 'declining':
                        st.error(f"📉 **Overall Trend: Declining**")
                    else:
                        st.info(f"📊 **Overall Trend: Stable**")
                    
                    # Key changes
                    key_changes = summary.get('key_changes', [])
                    if key_changes:
                        st.subheader("🔍 Key Changes")
                        for change in key_changes[:5]:
                            change_emoji = "📈" if change['change_type'] == 'increase' else "📉"
                            st.write(f"{change_emoji} **{change['parameter']}**: {change['percent_change']:+.1f}% change from {change['from_report']} to {change['to_report']}")
                    
                    # Expandable detailed comparison
                    with st.expander("📊 Detailed Parameter Comparisons"):
                        param_comparisons = comparison_data.get('parameter_comparisons', {})
                        
                        for param_name, comparison in param_comparisons.items():
                            st.write(f"**{param_name}**")
                            
                            values = comparison.get('values', [])
                            changes = comparison.get('changes', [])
                            trend = comparison.get('trend', 'stable')
                            
                            # Show values across reports
                            value_text = " → ".join([f"{v['value']} {v['unit']}" for v in values])
                            st.write(f"Values: {value_text}")
                            
                            # Show trend
                            trend_emoji = "📈" if trend == 'increasing' else "📉" if trend == 'decreasing' else "➡️"
                            st.write(f"Trend: {trend_emoji} {trend.title()}")
                            
                            if changes:
                                latest_change = changes[-1]
                                percent_change = latest_change.get('percent_change', 0)
                                st.write(f"Latest Change: {percent_change:+.1f}%")
                            
                            st.write("---")
                
                else:
                    st.info("🔄 **Comparison analysis not available**")
                    st.write("Comparison requires multiple valid reports with common parameters.")
            
            # Multi-Report Chat Interface Section with Enhanced AI
            st.divider()
            st.subheader("💬 Enhanced AI Medical Assistant")
            
            # Enhanced AI Agent Integration
            if st.session_state.enhanced_ai_agent:
                
                # Show AI capabilities
                with st.expander("🧠 AI Agent Capabilities"):
                    st.markdown("""
                    **Enhanced Intelligence Features:**
                    - 🎯 **Intent Recognition**: Understands your true goals beyond literal requests
                    - 🤔 **Smart Clarification**: Asks intelligent questions when requests are unclear
                    - 🔄 **Goal-Oriented Workflows**: Automatically plans multi-step actions to achieve your goals
                    - 🧠 **Context Memory**: Remembers conversation history and learns your preferences
                    - 📊 **Anticipatory Suggestions**: Proactively recommends relevant actions
                    
                    **Medical Analysis:**
                    - Multi-report processing and comparison
                    - Trend analysis and pattern recognition
                    - Personalized health recommendations
                    - Risk assessment and monitoring
                    """)
                
                # Enhanced Chat Interface
                if 'enhanced_chat_messages' not in st.session_state:
                    st.session_state.enhanced_chat_messages = []
                
                # Display chat messages
                for message in st.session_state.enhanced_chat_messages:
                    with st.chat_message(message["role"]):
                        if message["role"] == "assistant" and "response_data" in message:
                            # Enhanced response display
                            response_data = message["response_data"]
                            st.markdown(message["content"])
                            
                            # Show additional response elements
                            if response_data.get("type") == "clarification_request":
                                st.info("💡 **Clarifying Questions:**")
                                for i, q in enumerate(response_data.get("questions", [])[:3], 1):
                                    st.write(f"{i}. {q.get('question', '')}")
                            
                            elif response_data.get("type") == "context_request":
                                st.warning("📋 **Additional Information Needed:**")
                                for instruction in response_data.get("upload_instructions", []):
                                    st.write(f"• {instruction}")
                            
                            elif response_data.get("suggestions"):
                                st.success("💡 **Suggestions:**")
                                for suggestion in response_data["suggestions"][:3]:
                                    st.write(f"• {suggestion}")
                        else:
                            st.markdown(message["content"])
                
                # Enhanced Chat Input
                if prompt := st.chat_input("Ask me anything about your blood reports..."):
                    # Add user message to chat history
                    st.session_state.enhanced_chat_messages.append({"role": "user", "content": prompt})
                    
                    # Display user message
                    with st.chat_message("user"):
                        st.markdown(prompt)
                    
                    # Process with Enhanced AI Agent
                    with st.chat_message("assistant"):
                        with st.spinner("🧠 Enhanced AI processing your request..."):
                            
                            # Prepare additional context
                            additional_context = {
                                'ui_state': 'streamlit_interface',
                                'reports_uploaded': len(st.session_state.current_reports) > 0,
                                'comparison_available': st.session_state.comparison_available,
                                'session_type': 'interactive_analysis'
                            }
                            
                            # Process message with Enhanced AI Agent
                            response = st.session_state.enhanced_ai_agent.process_user_message(
                                prompt, additional_context
                            )
                            
                            # Display response based on type
                            response_type = response.get('type', 'general')
                            response_message = response.get('message', 'I apologize, but I encountered an issue processing your request.')
                            
                            # Display main response
                            st.markdown(response_message)
                            
                            # Handle different response types
                            if response_type == 'clarification_request':
                                st.info("💭 **I need some clarification to help you better:**")
                                questions = response.get('questions', [])
                                for i, q in enumerate(questions[:3], 1):
                                    st.write(f"**{i}.** {q.get('question', '')}")
                                    if q.get('suggested_answers'):
                                        st.write(f"   *Suggestions: {', '.join(q['suggested_answers'][:3])}*")
                            
                            elif response_type == 'context_request':
                                st.warning("📋 **To provide the best help, I need:**")
                                if response.get('upload_instructions'):
                                    for instruction in response['upload_instructions']:
                                        st.write(f"• {instruction}")
                                
                                if response.get('next_steps'):
                                    st.info("**Next Steps:**")
                                    for step in response['next_steps']:
                                        st.write(f"• {step}")
                            
                            elif response_type == 'workflow_complete':
                                st.success("✅ **Task Completed Successfully!**")
                                if response.get('next_actions'):
                                    st.info("**What you can do next:**")
                                    for action in response['next_actions']:
                                        st.write(f"• {action}")
                            
                            elif response_type == 'error':
                                st.error("⚠️ **I encountered an issue, but I'm here to help!**")
                                if response.get('suggestions'):
                                    st.info("**Try these alternatives:**")
                                    for suggestion in response['suggestions']:
                                        st.write(f"• {suggestion}")
                            
                            # Show additional capabilities or suggestions
                            if response.get('additional_actions'):
                                with st.expander("🔍 More things you can try"):
                                    for action in response['additional_actions']:
                                        st.write(f"• {action}")
                            
                            # Show workflow status if available
                            if response.get('workflow_id'):
                                with st.expander("⚙️ Processing Details"):
                                    workflow_status = response.get('workflow_status', {})
                                    st.write(f"**Workflow:** {workflow_status.get('goal_description', 'Processing request')}")
                                    st.write(f"**Status:** {workflow_status.get('status', 'unknown').title()}")
                    
                    # Add assistant response to chat history
                    st.session_state.enhanced_chat_messages.append({
                        "role": "assistant", 
                        "content": response_message,
                        "response_data": response
                    })
                
                # Enhanced Chat Controls
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🗑️ Clear Chat"):
                        st.session_state.enhanced_chat_messages = []
                        # Reset AI agent session
                        st.session_state.enhanced_ai_agent.end_session()
                        st.session_state.ai_session_id = st.session_state.enhanced_ai_agent.start_user_session()
                        st.rerun()
                
                with col2:
                    if st.button("📊 Agent Status"):
                        if st.session_state.ai_session_id:
                            st.info(f"**Session ID:** {st.session_state.ai_session_id[:8]}...")
                            st.info(f"**Messages:** {len(st.session_state.enhanced_chat_messages)}")
                            st.info("**Status:** Active and learning from your interactions")
                
                with col3:
                    if st.button("💡 Quick Help"):
                        help_message = """
                        **Quick Start Guide:**
                        • Upload blood reports for analysis
                        • Ask: "Analyze my report" or "What are my abnormal values?"
                        • Compare: "How do my reports compare?" or "Show me trends"
                        • Get advice: "What should I do about my cholesterol?"
                        • Be natural - I understand context and can clarify unclear requests!
                        """
                        st.info(help_message)
            
            else:
                st.error("🤖 **Enhanced AI Agent not available**")
                st.markdown("The enhanced AI features require proper initialization. Please refresh the page.")
            
            # Legacy Q&A Section (fallback)
            if not st.session_state.enhanced_ai_agent:
                st.divider()
                st.subheader("💬 Basic Q&A Assistant (Fallback)")
                
                # Check if we have any reports with Phase-2 analysis
                has_enhanced_analysis = any(
                    manager.get_report_data(report_id).get('phase2_available', False) 
                    for report_id in st.session_state.current_reports.keys()
                )
                
                if has_enhanced_analysis:
                    # Create multi-report Q&A assistant
                    qa_assistant = create_multi_report_qa_assistant(
                        st.session_state.current_reports,
                        manager.get_comparison_results()
                    )
                    
                    # Show session info
                    session_info = qa_assistant.get_session_summary()
                    st.info(f"🤖 **Multi-Report AI Chat Active** - {session_info['reports_loaded']} reports loaded, comparison {'available' if session_info['comparison_available'] else 'not available'}")
                    
                    # Available topics for multi-report
                    topics = qa_assistant.get_available_topics()
                    with st.expander("💡 Available Topics"):
                        for topic in topics:
                            st.write(f"• {topic}")
                    
                    # Chat interface
                    if 'multi_chat_messages' not in st.session_state:
                        st.session_state.multi_chat_messages = []
                    
                    # Display chat messages
                    for message in st.session_state.multi_chat_messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                    
                    # Chat input
                    if prompt := st.chat_input("Ask about your blood reports..."):
                        # Add user message to chat history
                        st.session_state.multi_chat_messages.append({"role": "user", "content": prompt})
                        
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        
                        # Generate AI response
                        with st.chat_message("assistant"):
                            with st.spinner("🤖 Analyzing your question..."):
                                response = qa_assistant.answer_question(prompt)
                            st.markdown(response)
                        
                        # Add assistant response to chat history
                        st.session_state.multi_chat_messages.append({"role": "assistant", "content": response})
                    
                    # Chat controls
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Clear Basic Chat"):
                            st.session_state.multi_chat_messages = []
                            qa_assistant.clear_session()
                            st.rerun()
                    
                    with col2:
                        if st.button("📊 Basic Session Stats"):
                            stats = qa_assistant.get_session_summary()
                            st.json(stats)
                
                else:
                    st.info("🤖 **AI Chat requires enhanced analysis**")
                    st.markdown("Upload blood reports and ensure AI analysis is available to enable chat functionality.")
            
        except Exception as e:
            st.error(f"❌ Processing Error: {str(e)}")
            
            # Add debug information
            with st.expander("🔍 Debug Information"):
                st.write("**Error Details:**")
                st.code(str(e))
                
                if 'processing_result' in locals():
                    st.write("**Processing Result:**")
                    st.json(processing_result)
                
                if st.session_state.multi_report_session:
                    session_data = st.session_state.multi_report_session.get_all_reports()
                    st.write("**Session Data:**")
                    st.write(f"Reports: {len(session_data.get('reports', {}))}")
                    st.write(f"Analysis Results: {len(session_data.get('analysis_results', {}))}")
            
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
    2. **Automatic detection** of multiple reports within single documents
    3. **Individual analysis** of each report with complete data isolation
    4. **Comparative analysis** across multiple reports with trend detection
    5. **AI chat** with session-based memory for multi-report conversations
    
    ### Multi-Report Features:
    - **Boundary Detection**: Automatically separates multiple reports in single PDFs
    - **Data Isolation**: Each report analyzed independently to prevent data mixing
    - **Trend Analysis**: Compare parameters across reports to identify improvements or concerns
    - **Session Memory**: AI assistant remembers context across multiple questions
    - **Comparative Chat**: Ask questions like "compare my reports" or "show trends"
    """)
    
    # Show example questions for multi-report scenarios
    with st.expander("💡 Example Multi-Report Questions"):
        st.markdown("""
        **Individual Report Questions:**
        - "What are the abnormal values in Report_1?"
        - "Explain my latest cholesterol levels"
        
        **Comparison Questions:**
        - "Compare my hemoglobin levels across all reports"
        - "What trends do you see in my glucose levels?"
        - "Has my overall health improved?"
        
        **Trend Analysis:**
        - "Which parameters are getting worse?"
        - "Show me the biggest changes between reports"
        - "What should I focus on based on the trends?"
        """)