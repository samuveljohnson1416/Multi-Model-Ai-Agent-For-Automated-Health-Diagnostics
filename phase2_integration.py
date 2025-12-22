import json
import pandas as pd
import io
from typing import Dict, Any, Optional
from phase2_orchestrator import process_csv_with_phase2
from csv_schema_adapter import adapt_csv_for_phase2, safe_percentage


class Phase2Integration:
    """Integration layer between existing system and Phase-2 LLM analysis"""
    
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
        """Process CSV through Phase-2 if available, otherwise return status"""
        
        if not self.phase2_enabled:
            return {
                "phase2_status": "unavailable",
                "message": "Phase-2 requires Ollama with Mistral 7B model. Please install: 'ollama pull mistral:7b-instruct'",
                "fallback_used": True
            }
        
        if not csv_content or csv_content.strip() == "":
            return {
                "phase2_status": "no_data",
                "message": "No CSV data available for Phase-2 analysis",
                "fallback_used": True
            }
        
        try:
            # Validate CSV format
            df = pd.read_csv(io.StringIO(csv_content))
            if df.empty:
                return {
                    "phase2_status": "empty_csv",
                    "message": "CSV contains no data for analysis",
                    "fallback_used": True
                }
            
            # Check required columns (flexible naming)
            required_cols = ["value", "unit", "reference_range"]
            test_name_col = None
            
            # Check for test name column (flexible naming)
            if "test_name" in df.columns:
                test_name_col = "test_name"
            elif "name" in df.columns:
                test_name_col = "name"
            else:
                return {
                    "phase2_status": "invalid_format",
                    "message": "CSV missing test name column (expected 'test_name' or 'name')",
                    "fallback_used": True
                }
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "phase2_status": "invalid_format",
                    "message": f"CSV missing required columns: {missing_cols}",
                    "fallback_used": True
                }
            
            # Standardize column names for Phase-2 processing
            if test_name_col == "name":
                df = df.rename(columns={"name": "test_name"})
            
            # Process through Phase-2
            phase2_result = process_csv_with_phase2(csv_content, self.ollama_url)
            
            # Add integration metadata
            phase2_result["phase2_status"] = "completed"
            phase2_result["integration_info"] = {
                "csv_rows_processed": len(df),
                "ollama_url": self.ollama_url,
                "model_used": "mistral:7b-instruct"
            }
            
            return phase2_result
            
        except Exception as e:
            return {
                "phase2_status": "error",
                "message": f"Phase-2 processing failed: {str(e)}",
                "error_details": str(e),
                "fallback_used": True
            }
    
    def get_phase2_summary(self, phase2_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from Phase-2 analysis for UI display"""
        
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
            
            # Extract key metrics
            summary = synthesis.get("summary", {})
            abnormal_params = synthesis.get("abnormal_parameters", [])
            
            # Format for UI display
            return {
                "available": True,
                "overall_status": synthesis.get("overall_status", "Unknown"),
                "risk_level": synthesis.get("risk_level", "Unknown"),
                "metrics": {
                    "total_tests": summary.get("total_tests", 0),
                    "abnormal_count": summary.get("abnormal_count", 0),
                    "patterns_detected": summary.get("patterns_detected", 0)
                },
                "abnormal_findings": [
                    {
                        "test": param["test_name"],
                        "value": param["value"],
                        "status": param["classification"],
                        "reference": param["reference_range"]
                    }
                    for param in abnormal_params[:5]  # Limit to top 5
                ],
                "key_concerns": synthesis.get("key_concerns", [])[:3],  # Top 3
                "recommendations": {
                    "lifestyle": recommendations.get("lifestyle_recommendations", [])[:3],
                    "follow_up": recommendations.get("follow_up_guidance", ""),
                    "consultation_required": bool(recommendations.get("healthcare_consultation"))
                },
                "ai_confidence": self._calculate_confidence(phase2_result),
                "processing_info": {
                    "model": "Mistral 7B Instruct",
                    "processing_time": "Local LLM",
                    "data_source": "CSV-only (no hallucination)"
                }
            }
            
        except Exception as e:
            return {
                "available": False,
                "status": "parsing_error",
                "message": f"Failed to parse Phase-2 results: {str(e)}"
            }
    
    def _calculate_confidence(self, phase2_result: Dict[str, Any]) -> str:
        """Calculate overall confidence in Phase-2 analysis"""
        try:
            param_interp = phase2_result.get("parameter_interpretation", {})
            interpretations = param_interp.get("interpretations", [])
            
            if not interpretations:
                return "Low"
            
            # Count successful interpretations
            successful = len([p for p in interpretations if p.get("classification") not in ["Unknown", "Missing"]])
            total = len(interpretations)
            
            if total == 0:
                return "Low"
            
            success_rate = successful / total
            
            if success_rate >= 0.8:
                return "High"
            elif success_rate >= 0.6:
                return "Medium"
            else:
                return "Low"
                
        except Exception:
            return "Unknown"
    
    def format_for_display(self, phase2_summary: Dict[str, Any]) -> str:
        """Format Phase-2 summary for text display"""
        
        if not phase2_summary.get("available"):
            return f"Phase-2 Analysis: {phase2_summary.get('message', 'Not available')}"
        
        try:
            status = phase2_summary["overall_status"]
            risk = phase2_summary["risk_level"]
            metrics = phase2_summary["metrics"]
            
            display_text = f"""**Phase-2 AI Analysis (Mistral 7B)**
            
**Overall Status:** {status}
**Risk Level:** {risk}
**Tests Analyzed:** {metrics['total_tests']} | **Abnormal:** {metrics['abnormal_count']} | **Patterns:** {metrics['patterns_detected']}

**Key Findings:**"""
            
            # Add abnormal findings
            for finding in phase2_summary.get("abnormal_findings", []):
                display_text += f"\n• **{finding['test']}**: {finding['value']} ({finding['status']})"
            
            # Add concerns
            concerns = phase2_summary.get("key_concerns", [])
            if concerns:
                display_text += f"\n\n**Areas of Concern:** {', '.join(concerns)}"
            
            # Add top recommendations
            recs = phase2_summary.get("recommendations", {}).get("lifestyle", [])
            if recs:
                display_text += f"\n\n**AI Recommendations:**"
                for rec in recs[:2]:  # Top 2
                    display_text += f"\n• {rec}"
            
            display_text += f"\n\n**AI Confidence:** {phase2_summary['ai_confidence']}"
            
            return display_text
            
        except Exception as e:
            return f"Phase-2 Analysis: Error formatting results - {str(e)}"


def integrate_phase2_analysis(csv_content: str, ollama_url: str = "http://localhost:11434") -> Dict[str, Any]:
    """Main integration function for Phase-2 analysis"""
    integration = Phase2Integration(ollama_url)
    
    # Process through Phase-2
    phase2_result = integration.process_with_phase2(csv_content)
    
    # Get summary for UI
    phase2_summary = integration.get_phase2_summary(phase2_result)
    
    # Format for display
    display_text = integration.format_for_display(phase2_summary)
    
    return {
        "phase2_full_result": phase2_result,
        "phase2_summary": phase2_summary,
        "phase2_display_text": display_text,
        "integration_status": "completed"
    }


def check_phase2_requirements() -> Dict[str, Any]:
    """Check if Phase-2 requirements are met"""
    integration = Phase2Integration()
    
    return {
        "ollama_available": integration.phase2_enabled,
        "required_model": "mistral:instruct",
        "installation_command": "ollama pull mistral:instruct",
        "status": "ready" if integration.phase2_enabled else "setup_required"
    }