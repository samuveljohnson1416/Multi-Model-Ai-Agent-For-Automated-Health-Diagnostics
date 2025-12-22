import streamlit as st
import pandas as pd
import io
import json
from ocr_engine import extract_text_from_file
from parser import parse_blood_report
from validator import validate_parameters
from interpreter import interpret_results
from csv_converter import json_to_ml_csv
from phase2_integration import integrate_phase2_analysis, check_phase2_requirements

st.set_page_config(page_title="Blood Report Analyzer", layout="wide")

st.title("Blood Report Analyzer – Milestone 1")
st.markdown("Analyzes blood test reports and provides interpretations.")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your medical report",
    type=["pdf", "png", "jpg", "jpeg", "json", "csv"],
    help="Supported: PDF, PNG, JPG, JPEG, JSON, CSV"
)

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
                        # Process through Phase-2
                        phase2_integration = integrate_phase2_analysis(ml_csv)
                        
                        if phase2_integration["phase2_summary"]["available"]:
                            summary = phase2_integration["phase2_summary"]
                            
                            # Display key metrics
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Overall Status", summary["overall_status"])
                            with col2:
                                st.metric("Risk Level", summary["risk_level"])
                            with col3:
                                st.metric("AI Confidence", summary["ai_confidence"])
                            with col4:
                                st.metric("Patterns Found", summary["metrics"]["patterns_detected"])
                            
                            # Display AI analysis
                            st.markdown(phase2_integration["phase2_display_text"])
                            
                            # Show abnormal findings
                            if summary["abnormal_findings"]:
                                st.warning("**AI-Detected Abnormal Findings:**")
                                for finding in summary["abnormal_findings"]:
                                    status_emoji = "🔻" if finding["status"] == "Low" else "🔺" if finding["status"] == "High" else "⚠️"
                                    st.write(f"{status_emoji} **{finding['test']}**: {finding['value']} ({finding['status']}) - Ref: {finding['reference']}")
                            
                            # Show AI recommendations
                            if summary["recommendations"]["lifestyle"]:
                                st.info("**AI Lifestyle Recommendations:**")
                                for rec in summary["recommendations"]["lifestyle"]:
                                    st.write(f"• {rec}")
                            
                            # Medical disclaimer
                            st.warning("⚠️ **Medical Disclaimer**: This AI analysis is for informational purposes only. Always consult qualified healthcare professionals for medical decisions.")
                            
                            # Download Phase-2 results
                            phase2_json = json.dumps(phase2_integration["phase2_full_result"], indent=2)
                            st.download_button(
                                label="📥 Download Phase-2 AI Analysis (JSON)",
                                data=phase2_json,
                                file_name=f"phase2_analysis_{uploaded_file.name.split('.')[0]}.json",
                                mime="application/json"
                            )
                            
                        else:
                            st.warning(f"Phase-2 Analysis: {summary['message']}")
                            
                    except Exception as e:
                        st.error(f"Phase-2 Analysis Error: {str(e)}")
                        st.info("Falling back to Phase-1 analysis only")
                        
            else:
                st.warning("⚠️ Phase-2 AI Analysis requires Ollama with Mistral 7B model")
                st.info(f"**Setup Instructions:**\n1. Install Ollama: https://ollama.ai\n2. Run: `{phase2_req['installation_command']}`\n3. Restart this application")
                st.code(phase2_req['installation_command'])
            
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
