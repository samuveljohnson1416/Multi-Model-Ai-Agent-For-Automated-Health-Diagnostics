import json
import pandas as pd
import io
from typing import Dict, Any, Optional
from .phase2_orchestrator import process_csv_with_phase2
from .csv_schema_adapter import adapt_csv_for_phase2, safe_percentage


class Phase2Integration:
    """Integration layer between existing system and Phase-2 LLM analysis with safety guarantees"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.phase2_enabled = self._check_ollama_availability()
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is running and Mistral model is available"""
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any("mistral" in model.get("name", "") for model in models)
            return False
        except Exception:
            return False
    
    def process_with_phase2(self, csv_content: str) -> Dict[str, Any]:
        """Process CSV through Phase-2 with proper schema validation and safety guarantees"""
        
        # Step 1: Check Phase-2 availability (NEVER assume it's available)
        if not self.phase2_enabled:
            return {
                "phase2_status": "unavailable",
                "message": "Phase-2 requires Ollama with Mistral model. Please install: 'ollama pull mistral:instruct'",
                "fallback_used": True,
                "schema_info": None
            }
        
        # Step 2: Validate input (NEVER assume CSV is valid)
        if not csv_content or csv_content.strip() == "":
            return {
                "phase2_status": "no_data",
                "message": "No CSV data available for Phase-2 analysis",
                "fallback_used": True,
                "schema_info": None
            }
        
        # Step 3: Schema validation and adaptation (CRITICAL SAFETY STEP)
        # NEVER assume CSV column names - always validate and adapt
        try:
            adaptation_result = adapt_csv_for_phase2(csv_content)
            
            if not adaptation_result["success"]:
                return {
                    "phase2_status": "schema_validation_failed",
                    "message": f"CSV schema validation failed: {adaptation_result['error']}",
                    "schema_info": adaptation_result.get("schema_info"),
                    "schema_summary": adaptation_result.get("schema_summary", "No schema summary available"),
                    "fallback_used": True,
                    "error_details": adaptation_result["error"]
                }
            
            # Use adapted CSV for Phase-2 processing
            adapted_csv = adaptation_result["adapted_csv"]
            schema_info = adaptation_result["schema_info"]
            
        except Exception as e:
            return {
                "phase2_status": "adaptation_error",
                "message": f"CSV adaptation failed: {str(e)}",
                "error_details": str(e),
                "fallback_used": True,
                "schema_info": None
            }
        
        # Step 4: Process through Phase-2 (ONLY after successful schema validation)
        # LLM invocation occurs ONLY AFTER schema validation succeeds
        try:
            # Use the new orchestrator that extracts demographics from CSV
            phase2_result = process_csv_with_phase2(adapted_csv, self.ollama_url)
            
            # Add integration metadata with safe numeric formatting
            data_quality_score = schema_info.get("data_quality", {}).get("data_quality_score", 0)
            
            phase2_result["phase2_status"] = "completed"
            phase2_result["integration_info"] = {
                "csv_rows_processed": schema_info.get("row_count", 0),
                "valid_rows": schema_info.get("valid_rows", 0),
                "data_quality_score": round(data_quality_score, 3),
                "ollama_url": self.ollama_url,
                "model_used": "mistral:instruct",
                "schema_adaptation": "successful",
                "milestone2_enabled": True,
                "demographic_extraction": "from_csv_only",  # Updated to reflect new approach
                "medical_context_rules": "strict_csv_only"  # No user input for demographics
            }
            phase2_result["schema_info"] = schema_info
            
            return phase2_result
            
        except Exception as e:
            return {
                "phase2_status": "processing_error",
                "message": f"Phase-2 LLM processing failed: {str(e)}",
                "error_details": str(e),
                "schema_info": schema_info,
                "fallback_used": True
            }
    
    def get_phase2_summary(self, phase2_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from Phase-2 analysis for UI display with safe formatting"""
        
        if phase2_result.get("phase2_status") != "completed":
            return {
                "available": False,
                "status": phase2_result.get("phase2_status", "unknown"),
                "message": phase2_result.get("message", "Phase-2 analysis not available")
            }
        
        try:
            synthesis = phase2_result.get("synthesis", {})
            param_interp = phase2_result.get("parameter_interpretation", {})
            risk_assess = phase2_result.get("pattern_risk_assessment", {})
            recommendations = phase2_result.get("recommendations", {})
            
            # Extract key metrics with safe defaults
            summary = synthesis.get("summary", {})
            abnormal_params = synthesis.get("abnormal_parameters", [])
            
            # Safe numeric formatting
            total_tests = summary.get("total_tests", 0)
            abnormal_count = summary.get("abnormal_count", 0)
            patterns_detected = summary.get("patterns_detected", 0)
            
            # Extract Milestone-2 specific data
            milestone2_compliance = phase2_result.get("milestone2_compliance", {})
            milestone2_enhancements = synthesis.get("milestone2_enhancements", {})
            
            # Format for UI display with Milestone-2 enhancements
            return {
                "available": True,
                "overall_status": synthesis.get("overall_status", "Unknown"),
                "risk_level": synthesis.get("risk_level", "Unknown"),
                "metrics": {
                    "total_tests": int(total_tests) if isinstance(total_tests, (int, float)) else 0,
                    "abnormal_count": int(abnormal_count) if isinstance(abnormal_count, (int, float)) else 0,
                    "patterns_detected": int(patterns_detected) if isinstance(patterns_detected, (int, float)) else 0,
                    "context_available": summary.get("context_available", False)
                },
                "abnormal_findings": [
                    {
                        "test": param.get("test_name", "Unknown"),
                        "value": param.get("value", "Unknown"),
                        "status": param.get("classification", "Unknown"),
                        "reference": param.get("reference_range", "Unknown")
                    }
                    for param in abnormal_params[:5] if isinstance(param, dict)  # Limit to top 5, ensure dict
                ],
                "key_concerns": synthesis.get("key_concerns", [])[:3] if isinstance(synthesis.get("key_concerns"), list) else [],  # Top 3
                "milestone2_features": {
                    "patterns_detected": milestone2_enhancements.get("patterns_detected", []),
                    "pattern_risk_level": milestone2_enhancements.get("pattern_risk_level", "Low"),
                    "context_notes": milestone2_enhancements.get("context_notes", []),
                    "total_patterns": milestone2_enhancements.get("total_patterns", 0)
                },
                "recommendations": {
                    "lifestyle": recommendations.get("lifestyle_recommendations", [])[:3] if isinstance(recommendations.get("lifestyle_recommendations"), list) else [],
                    "follow_up": recommendations.get("follow_up_guidance", ""),
                    "consultation_required": bool(recommendations.get("healthcare_consultation"))
                },
                "ai_confidence": self._calculate_confidence(phase2_result),
                "processing_info": {
                    "model": "Mistral Instruct",
                    "processing_time": "Local LLM",
                    "data_source": "CSV-only (no hallucination)",
                    "milestone2_compliant": milestone2_compliance.get("integration_status") == "MILESTONE-2_COMPLIANT"
                }
            }
            
        except Exception as e:
            return {
                "available": False,
                "status": "parsing_error",
                "message": f"Failed to parse Phase-2 results: {str(e)}"
            }
    
    def _calculate_confidence(self, phase2_result: Dict[str, Any]) -> str:
        """Calculate overall confidence in Phase-2 analysis with safe numeric handling"""
        try:
            param_interp = phase2_result.get("parameter_interpretation", {})
            interpretations = param_interp.get("interpretations", [])
            
            if not interpretations or not isinstance(interpretations, list):
                return "Low"
            
            # Count successful interpretations with safe handling
            successful = 0
            total = len(interpretations)
            
            for interp in interpretations:
                if isinstance(interp, dict):
                    classification = interp.get("classification", "Unknown")
                    if classification not in ["Unknown", "Missing"]:
                        successful += 1
            
            if total == 0:
                return "Low"
            
            success_rate = safe_percentage(successful, total, 1) / 100.0
            
            if success_rate >= 0.8:
                return "High"
            elif success_rate >= 0.6:
                return "Medium"
            else:
                return "Low"
                
        except Exception:
            return "Unknown"
    
    def format_for_display(self, phase2_summary: Dict[str, Any]) -> str:
        """Format Phase-2 summary with Milestone-2 enhancements for text display with safe string formatting"""
        
        if not phase2_summary.get("available"):
            return f"Phase-2 Analysis: {phase2_summary.get('message', 'Not available')}"
        
        try:
            status = phase2_summary.get("overall_status", "Unknown")
            risk = phase2_summary.get("risk_level", "Unknown")
            metrics = phase2_summary.get("metrics", {})
            milestone2_features = phase2_summary.get("milestone2_features", {})
            
            # Safe numeric extraction
            total_tests = metrics.get("total_tests", 0)
            abnormal_count = metrics.get("abnormal_count", 0)
            patterns_detected = metrics.get("patterns_detected", 0)
            
            display_text = f"""**🤖 Phase-2 AI Analysis (Mistral) - Milestone-2 Compliant**

**Overall Status:** {status}
**Risk Level:** {risk}
**Tests Analyzed:** {total_tests} | **Abnormal:** {abnormal_count} | **Patterns:** {patterns_detected}

**🔍 Milestone-2 Pattern Recognition:**"""
            
            # Add detected patterns
            patterns = milestone2_features.get("patterns_detected", [])
            if isinstance(patterns, list) and patterns:
                display_text += f"\n• **Patterns Detected:** {len(patterns)}"
                for pattern in patterns[:3]:  # Top 3 patterns
                    if pattern:
                        display_text += f"\n  - {str(pattern)}"
                
                pattern_risk = milestone2_features.get("pattern_risk_level", "Low")
                display_text += f"\n• **Pattern Risk Level:** {pattern_risk}"
            else:
                display_text += f"\n• No significant patterns detected across parameter combinations"
            
            # Add contextual analysis if available
            context_notes = milestone2_features.get("context_notes", [])
            if isinstance(context_notes, list) and context_notes:
                display_text += f"\n\n**👤 Contextual Analysis (Model-3):**"
                for note in context_notes[:2]:  # Top 2 context notes
                    if note:
                        display_text += f"\n• {str(note)}"
            elif metrics.get("context_available", False):
                display_text += f"\n\n**👤 Contextual Analysis:** Available with demographic data"
            
            display_text += f"\n\n**🔬 Key Findings:**"
            
            # Add abnormal findings with safe access
            abnormal_findings = phase2_summary.get("abnormal_findings", [])
            if isinstance(abnormal_findings, list):
                for finding in abnormal_findings:
                    if isinstance(finding, dict):
                        test_name = finding.get("test", "Unknown")
                        value = finding.get("value", "Unknown")
                        status_val = finding.get("status", "Unknown")
                        display_text += f"\n• **{test_name}**: {value} ({status_val})"
            
            # Add concerns with safe access
            concerns = phase2_summary.get("key_concerns", [])
            if isinstance(concerns, list) and concerns:
                display_text += f"\n\n**⚠️ Areas of Concern:** {', '.join(str(c) for c in concerns[:3])}"
            
            # Add top recommendations with safe access
            recs = phase2_summary.get("recommendations", {}).get("lifestyle", [])
            if isinstance(recs, list) and recs:
                display_text += f"\n\n**💡 AI Recommendations:**"
                for rec in recs[:2]:  # Top 2
                    if rec:  # Ensure not empty
                        display_text += f"\n• {str(rec)}"
            
            # Add compliance info
            processing_info = phase2_summary.get("processing_info", {})
            milestone2_compliant = processing_info.get("milestone2_compliant", False)
            ai_confidence = phase2_summary.get("ai_confidence", "Unknown")
            
            display_text += f"\n\n**✅ Compliance:** {'Milestone-2 Compliant' if milestone2_compliant else 'Legacy Mode'}"
            display_text += f" | **AI Confidence:** {ai_confidence}"
            
            return display_text
            
        except Exception as e:
            return f"Phase-2 Analysis: Error formatting results - {str(e)}"


def integrate_phase2_analysis(csv_content: str, ollama_url: str = "http://localhost:11434", 
                             age: Optional[int] = None, gender: Optional[str] = None) -> Dict[str, Any]:
    """Main integration function for Phase-2 analysis with Milestone-2 support and safety guarantees
    
    Note: age and gender parameters are kept for backward compatibility but are ignored.
    Demographics are now extracted from CSV data only, following medical context analysis rules.
    """
    integration = Phase2Integration(ollama_url)
    
    # Process through Phase-2 with full error handling (demographics extracted from CSV)
    phase2_result = integration.process_with_phase2(csv_content)
    
    # Get summary for UI with safe formatting
    phase2_summary = integration.get_phase2_summary(phase2_result)
    
    # Format for display with safe string handling
    display_text = integration.format_for_display(phase2_summary)
    
    return {
        "phase2_full_result": phase2_result,
        "phase2_summary": phase2_summary,
        "phase2_display_text": display_text,
        "integration_status": "milestone2_completed",
        "medical_context_approach": "csv_demographics_only",
        "backward_compatibility_note": "age/gender parameters ignored - demographics extracted from CSV only"
    }


def check_phase2_requirements() -> Dict[str, Any]:
    """Check if Phase-2 requirements are met with safe error handling"""
    try:
        integration = Phase2Integration()
        
        return {
            "ollama_available": integration.phase2_enabled,
            "required_model": "mistral:instruct",
            "installation_command": "ollama pull mistral:instruct",
            "status": "ready" if integration.phase2_enabled else "setup_required"
        }
    except Exception as e:
        return {
            "ollama_available": False,
            "required_model": "mistral:instruct",
            "installation_command": "ollama pull mistral:instruct",
            "status": "error",
            "error": str(e)
        }