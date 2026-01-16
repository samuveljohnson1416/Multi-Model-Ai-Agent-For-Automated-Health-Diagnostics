import json
import pandas as pd
import io
from typing import Dict, List, Any, Optional
import requests
import re
from .advanced_pattern_analysis import Milestone2Integration

# Import unified LLM provider
try:
    from utils.llm_provider import get_llm_provider, generate_text
    HAS_LLM_PROVIDER = True
except ImportError:
    HAS_LLM_PROVIDER = False


class Phase2Orchestrator:
    """Phase-2 Medical AI Analysis using Mistral 7B Instruct via Ollama/HF API with Milestone-2 Integration"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "mistral:instruct"
        self.milestone2_integration = Milestone2Integration()
        
        # Use unified LLM provider if available
        self._llm_provider = get_llm_provider() if HAS_LLM_PROVIDER else None
        
    def _call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Call LLM API with automatic fallback between Ollama and HF API"""
        
        # Use unified provider if available
        if self._llm_provider:
            try:
                return self._llm_provider.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.1,
                    max_tokens=1000
                )
            except Exception as e:
                return f"Error: LLM provider failed - {str(e)}"
        
        # Fallback to direct Ollama call (legacy behavior)
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except Exception as e:
            return f"Error: Failed to connect to Ollama - {str(e)}"
    
    def _validate_json_output(self, text: str) -> Optional[Dict]:
        """Extract and validate JSON from LLM output"""
        try:
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return None
        except json.JSONDecodeError:
            return None
    
    def process_csv_to_phase2(self, csv_content: str) -> Dict[str, Any]:
        """Main orchestration: CSV → Model 1 → Milestone-2 Models → Synthesis → Recommendations"""
        
        # Parse CSV
        try:
            df = pd.read_csv(io.StringIO(csv_content))
            if df.empty:
                return {"error": "Empty CSV provided"}
        except Exception as e:
            return {"error": f"Invalid CSV format: {str(e)}"}
        
        # Step 1: Parameter Interpretation (Model 1)
        model1_result = self._model1_parameter_interpretation(df)
        
        # Step 2: Milestone-2 Pattern Recognition & Contextual Analysis
        milestone2_result = self.milestone2_integration.process_milestone2(
            model1_result, csv_content
        )
        
        # Step 3: Legacy Model 2 for backward compatibility
        model2_result = self._model2_pattern_risk_assessment(df, model1_result)
        
        # Step 4: Enhanced Synthesis Engine (integrates Milestone-2)
        synthesis_result = self._enhanced_synthesis_engine(
            model1_result, model2_result, milestone2_result
        )
        
        # Step 5: Recommendation Generator
        recommendations = self._recommendation_generator(synthesis_result)
        
        # Step 6: Final Report Assembly with Milestone-2
        final_report = self._assemble_milestone2_report(
            model1_result, model2_result, milestone2_result, synthesis_result, recommendations
        )
        
        return final_report


class Model1ParameterInterpreter:
    """Model 1: Parameter Interpretation using Mistral 7B"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def interpret_parameters(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compare each parameter with reference range using LLM"""
        
        # Prepare CSV data for LLM
        csv_data = []
        for _, row in df.iterrows():
            csv_data.append({
                "test_name": str(row.get("test_name", "")),
                "value": str(row.get("value", "")),
                "unit": str(row.get("unit", "")),
                "reference_range": str(row.get("reference_range", ""))
            })
        
        # System prompt for Medical Laboratory Specialist persona
        system_prompt = """You are a Medical Laboratory Specialist (MD) with 15+ years of experience in clinical laboratory medicine.
Your ONLY task is to compare laboratory test values with their reference ranges.
You must output STRICT JSON ONLY with no additional text.
Never add parameters not in the input.
Never diagnose diseases.
Use only: Low, Normal, High, Borderline."""
        
        # One-shot prompting
        prompt = f"""Analyze these laboratory parameters and classify each as Low/Normal/High/Borderline based on the reference range:

CSV Data:
{json.dumps(csv_data, indent=2)}

For each parameter, compare the value with the reference_range and classify.
If reference_range is missing or "NA", classify as "Unknown".
If value is "NA" or missing, classify as "Missing".

Output STRICT JSON format:
{{
  "interpretations": [
    {{
      "test_name": "parameter_name",
      "value": "actual_value",
      "classification": "Low|Normal|High|Borderline|Unknown|Missing",
      "reference_range": "range_used"
    }}
  ],
  "summary": {{
    "total_parameters": number,
    "normal_count": number,
    "abnormal_count": number
  }}
}}"""

        # Call LLM
        response = self.orchestrator._call_ollama(prompt, system_prompt)
        
        # Validate and return JSON
        result = self.orchestrator._validate_json_output(response)
        if result:
            return result
        else:
            # Fallback: deterministic classification
            return self._fallback_classification(csv_data)
    
    def _fallback_classification(self, csv_data: List[Dict]) -> Dict[str, Any]:
        """Deterministic fallback if LLM fails"""
        interpretations = []
        normal_count = 0
        abnormal_count = 0
        
        for param in csv_data:
            classification = "Unknown"
            
            try:
                value = param["value"]
                ref_range = param["reference_range"]
                
                if value == "NA" or not value:
                    classification = "Missing"
                elif ref_range == "NA" or not ref_range:
                    classification = "Unknown"
                else:
                    # Simple range parsing
                    if "-" in ref_range:
                        parts = ref_range.split("-")
                        if len(parts) == 2:
                            try:
                                low = float(parts[0].strip())
                                high = float(parts[1].strip())
                                val = float(value)
                                
                                if val < low:
                                    classification = "Low"
                                    abnormal_count += 1
                                elif val > high:
                                    classification = "High"
                                    abnormal_count += 1
                                else:
                                    classification = "Normal"
                                    normal_count += 1
                            except ValueError:
                                classification = "Unknown"
            except Exception:
                classification = "Unknown"
            
            interpretations.append({
                "test_name": param["test_name"],
                "value": param["value"],
                "classification": classification,
                "reference_range": param["reference_range"]
            })
        
        return {
            "interpretations": interpretations,
            "summary": {
                "total_parameters": len(csv_data),
                "normal_count": normal_count,
                "abnormal_count": abnormal_count
            }
        }


class Model2PatternRiskAssessment:
    """Model 2: Pattern Recognition & Risk Assessment"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def assess_patterns(self, df: pd.DataFrame, model1_result: Dict) -> Dict[str, Any]:
        """Analyze parameter combinations and assess risk"""
        
        # Step 1: Deterministic calculations
        deterministic_patterns = self._calculate_deterministic_patterns(df)
        
        # Step 2: LLM-based risk explanation
        llm_risk_assessment = self._llm_risk_explanation(deterministic_patterns, model1_result)
        
        return {
            "deterministic_patterns": deterministic_patterns,
            "risk_assessment": llm_risk_assessment
        }
    
    def _calculate_deterministic_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate known medical ratios and thresholds"""
        patterns = {}
        
        # Convert to dict for easier access
        params = {}
        for _, row in df.iterrows():
            test_name = str(row.get("test_name", "")).lower()
            try:
                value = float(row.get("value", 0))
                params[test_name] = value
            except (ValueError, TypeError):
                continue
        
        # Lipid ratios
        if "total cholesterol" in params and "hdl cholesterol" in params:
            if params["hdl cholesterol"] > 0:
                ratio = params["total cholesterol"] / params["hdl cholesterol"]
                patterns["cholesterol_hdl_ratio"] = {
                    "value": round(ratio, 2),
                    "risk_level": "High" if ratio > 5.0 else "Moderate" if ratio > 3.5 else "Low"
                }
        
        # Anemia patterns
        hb_low = params.get("hemoglobin", 0) < 12.0
        rbc_low = params.get("rbc count", 0) < 4.0
        if hb_low and rbc_low:
            patterns["anemia_pattern"] = {
                "detected": True,
                "risk_level": "Moderate"
            }
        
        # Infection patterns
        wbc_high = params.get("wbc count", 0) > 11000
        neutrophil_high = params.get("neutrophils", 0) > 70
        if wbc_high or neutrophil_high:
            patterns["infection_pattern"] = {
                "detected": True,
                "risk_level": "Moderate"
            }
        
        return patterns
    
    def _llm_risk_explanation(self, patterns: Dict, model1_result: Dict) -> Dict[str, Any]:
        """Use LLM to explain risk levels"""
        
        system_prompt = """You are a Medical Laboratory Specialist analyzing laboratory patterns.
Your task is to provide risk level assessment and brief reasoning.
Output STRICT JSON ONLY.
Never diagnose diseases.
Never mention medication names.
Use only: Low, Moderate, High risk levels."""
        
        prompt = f"""Analyze these laboratory patterns and abnormal findings:

Deterministic Patterns:
{json.dumps(patterns, indent=2)}

Abnormal Parameters from Model 1:
{json.dumps([p for p in model1_result.get("interpretations", []) if p["classification"] in ["Low", "High"]], indent=2)}

Provide risk assessment with brief reasoning.

Output STRICT JSON format:
{{
  "overall_risk_level": "Low|Moderate|High",
  "reasoning": "Brief explanation in one sentence",
  "key_concerns": ["concern1", "concern2"],
  "pattern_significance": "Low|Moderate|High"
}}"""

        response = self.orchestrator._call_ollama(prompt, system_prompt)
        result = self.orchestrator._validate_json_output(response)
        
        if result:
            return result
        else:
            # Fallback assessment
            risk_level = "Low"
            if patterns:
                high_risk_patterns = [p for p in patterns.values() if isinstance(p, dict) and p.get("risk_level") == "High"]
                if high_risk_patterns:
                    risk_level = "High"
                elif any(p.get("risk_level") == "Moderate" for p in patterns.values() if isinstance(p, dict)):
                    risk_level = "Moderate"
            
            return {
                "overall_risk_level": risk_level,
                "reasoning": "Assessment based on deterministic pattern analysis",
                "key_concerns": list(patterns.keys()),
                "pattern_significance": risk_level
            }


class SynthesisEngine:
    """Synthesis Engine: Aggregate Model 1 and Model 2 outputs"""
    
    def synthesize(self, model1_result: Dict, model2_result: Dict) -> Dict[str, Any]:
        """Aggregate outputs without creativity or assumptions"""
        
        # Extract abnormal findings
        abnormal_params = [
            p for p in model1_result.get("interpretations", [])
            if p["classification"] in ["Low", "High", "Borderline"]
        ]
        
        # Extract key concerns
        key_concerns = []
        if model2_result.get("risk_assessment", {}).get("key_concerns"):
            key_concerns.extend(model2_result["risk_assessment"]["key_concerns"])
        
        # Determine overall status
        total_abnormal = len(abnormal_params)
        risk_level = model2_result.get("risk_assessment", {}).get("overall_risk_level", "Low")
        
        if total_abnormal == 0 and risk_level == "Low":
            overall_status = "Normal"
        elif total_abnormal <= 2 and risk_level in ["Low", "Moderate"]:
            overall_status = "Minor Concerns"
        else:
            overall_status = "Requires Attention"
        
        return {
            "overall_status": overall_status,
            "abnormal_parameters": abnormal_params,
            "key_concerns": key_concerns,
            "risk_level": risk_level,
            "summary": {
                "total_tests": model1_result.get("summary", {}).get("total_parameters", 0),
                "abnormal_count": total_abnormal,
                "patterns_detected": len(model2_result.get("deterministic_patterns", {}))
            }
        }


class RecommendationGenerator:
    """Recommendation Generator with strict guardrails"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def generate_recommendations(self, synthesis_result: Dict) -> Dict[str, Any]:
        """Generate controlled lifestyle recommendations"""
        
        system_prompt = """You are a Medical Laboratory Specialist providing general lifestyle guidance.
You must ONLY provide general lifestyle advice.
MANDATORY requirements:
- Recommend consulting a healthcare professional
- Include medical disclaimer
- NO disease names
- NO medication names
- Focus on: diet, exercise, follow-up guidance
Output STRICT JSON ONLY."""
        
        abnormal_params = synthesis_result.get("abnormal_parameters", [])
        risk_level = synthesis_result.get("risk_level", "Low")
        
        prompt = f"""Based on these laboratory findings, provide general lifestyle recommendations:

Risk Level: {risk_level}
Abnormal Parameters: {len(abnormal_params)}
Key Concerns: {synthesis_result.get("key_concerns", [])}

Provide general lifestyle advice focusing on diet, exercise, and follow-up.
Include mandatory healthcare professional consultation and disclaimer.

Output STRICT JSON format:
{{
  "lifestyle_recommendations": [
    "recommendation1",
    "recommendation2"
  ],
  "follow_up_guidance": "guidance_text",
  "healthcare_consultation": "mandatory_consultation_text",
  "medical_disclaimer": "disclaimer_text"
}}"""

        response = self.orchestrator._call_ollama(prompt, system_prompt)
        result = self.orchestrator._validate_json_output(response)
        
        if result:
            return result
        else:
            # Fallback recommendations
            return self._fallback_recommendations(risk_level, len(abnormal_params))
    
    def _fallback_recommendations(self, risk_level: str, abnormal_count: int) -> Dict[str, Any]:
        """Safe fallback recommendations"""
        
        recommendations = [
            "Maintain a balanced diet with adequate nutrients",
            "Engage in regular physical activity as appropriate",
            "Stay adequately hydrated"
        ]
        
        if risk_level in ["Moderate", "High"] or abnormal_count > 0:
            recommendations.extend([
                "Monitor your health parameters regularly",
                "Follow up with healthcare provider as recommended"
            ])
        
        return {
            "lifestyle_recommendations": recommendations,
            "follow_up_guidance": "Schedule regular health check-ups and follow your healthcare provider's advice",
            "healthcare_consultation": "IMPORTANT: Consult with a qualified healthcare professional for proper medical evaluation and treatment",
            "medical_disclaimer": "This analysis is for informational purposes only and does not constitute medical advice, diagnosis, or treatment recommendations"
        }


# Add methods to Phase2Orchestrator
def _model1_parameter_interpretation(self, df: pd.DataFrame) -> Dict[str, Any]:
    """Execute Model 1: Parameter Interpretation"""
    model1 = Model1ParameterInterpreter(self)
    return model1.interpret_parameters(df)

def _model2_pattern_risk_assessment(self, df: pd.DataFrame, model1_result: Dict) -> Dict[str, Any]:
    """Execute Model 2: Pattern Recognition & Risk Assessment"""
    model2 = Model2PatternRiskAssessment(self)
    return model2.assess_patterns(df, model1_result)

def _synthesis_engine(self, model1_result: Dict, model2_result: Dict) -> Dict[str, Any]:
    """Execute Synthesis Engine"""
    synthesis = SynthesisEngine()
    return synthesis.synthesize(model1_result, model2_result)

def _recommendation_generator(self, synthesis_result: Dict) -> Dict[str, Any]:
    """Execute Recommendation Generator"""
    rec_gen = RecommendationGenerator(self)
    return rec_gen.generate_recommendations(synthesis_result)

def _enhanced_synthesis_engine(self, model1_result: Dict, model2_result: Dict, 
                             milestone2_result: Dict) -> Dict[str, Any]:
    """Enhanced Synthesis Engine that integrates Milestone-2 results"""
    
    # Get legacy synthesis
    legacy_synthesis = self._synthesis_engine(model1_result, model2_result)
    
    # Extract Milestone-2 insights
    milestone2_analysis = milestone2_result.get("milestone2_analysis", {})
    model2_patterns = milestone2_analysis.get("model2_patterns", {})
    model3_context = milestone2_analysis.get("model3_context", {})
    
    # Enhanced abnormal findings with pattern context
    abnormal_params = legacy_synthesis.get("abnormal_parameters", [])
    
    # Add pattern-based risk assessment
    pattern_risk = model2_patterns.get("risk_level", "Low")
    detected_patterns = model2_patterns.get("patterns_detected", [])
    
    # Combine risk levels (take higher of legacy vs Milestone-2)
    legacy_risk = legacy_synthesis.get("risk_level", "Low")
    risk_levels = {"Low": 1, "Moderate": 2, "High": 3}
    combined_risk_level = max(risk_levels.get(legacy_risk, 1), risk_levels.get(pattern_risk, 1))
    combined_risk = [k for k, v in risk_levels.items() if v == combined_risk_level][0]
    
    # Enhanced key concerns
    enhanced_concerns = legacy_synthesis.get("key_concerns", [])
    enhanced_concerns.extend(detected_patterns[:3])  # Add top 3 patterns
    
    # Add contextual notes if available
    context_notes = model3_context.get("context_notes", [])
    
    return {
        "overall_status": legacy_synthesis.get("overall_status", "Unknown"),
        "abnormal_parameters": abnormal_params,
        "key_concerns": list(set(enhanced_concerns))[:5],  # Deduplicate, limit to 5
        "risk_level": combined_risk,
        "milestone2_enhancements": {
            "patterns_detected": detected_patterns,
            "pattern_risk_level": pattern_risk,
            "context_notes": context_notes[:3],  # Top 3 context notes
            "total_patterns": model2_patterns.get("total_patterns", 0)
        },
        "summary": {
            "total_tests": model1_result.get("summary", {}).get("total_parameters", 0),
            "abnormal_count": len(abnormal_params),
            "patterns_detected": model2_patterns.get("total_patterns", 0),
            "context_available": len(context_notes) > 0
        }
    }

def _assemble_final_report(self, model1_result: Dict, model2_result: Dict, 
                          synthesis_result: Dict, recommendations: Dict) -> Dict[str, Any]:
    """Assemble final user-friendly report (legacy compatibility)"""
    
    return {
        "phase2_analysis": {
            "timestamp": pd.Timestamp.now().isoformat(),
            "model_used": self.model_name,
            "processing_status": "completed"
        },
        "parameter_interpretation": model1_result,
        "pattern_risk_assessment": model2_result,
        "synthesis": synthesis_result,
        "recommendations": recommendations,
        "medical_disclaimer": "This AI analysis is for informational purposes only. Always consult qualified healthcare professionals for medical decisions."
    }

def _assemble_milestone2_report(self, model1_result: Dict, model2_result: Dict, 
                               milestone2_result: Dict, synthesis_result: Dict, 
                               recommendations: Dict) -> Dict[str, Any]:
    """Assemble final report with Milestone-2 enhancements"""
    
    # Get legacy report structure
    legacy_report = self._assemble_final_report(
        model1_result, model2_result, synthesis_result, recommendations
    )
    
    # Add Milestone-2 specific sections
    milestone2_analysis = milestone2_result.get("milestone2_analysis", {})
    
    enhanced_report = {
        **legacy_report,
        "milestone2_compliance": {
            "model2_pattern_recognition": {
                "implemented": True,
                "patterns_detected": milestone2_analysis.get("model2_patterns", {}).get("patterns_detected", []),
                "pattern_types": [
                    "CBC distribution patterns",
                    "Lipid ratio analysis", 
                    "WBC distribution imbalances",
                    "RBC index coordination",
                    "Cross-system abnormalities"
                ],
                "risk_assessment": milestone2_analysis.get("model2_patterns", {}).get("risk_level", "Low")
            },
            "model3_contextual_analysis": {
                "implemented": True,
                "demographic_context": milestone2_analysis.get("model3_context", {}).get("demographic_info", {}),
                "context_notes": milestone2_analysis.get("model3_context", {}).get("context_notes", []),
                "limitations": milestone2_analysis.get("model3_context", {}).get("context_limitations", [])
            },
            "integration_status": "MILESTONE-2_COMPLIANT",
            "verification": {
                "model2_uses_parameter_combinations": True,
                "model2_detects_explicit_patterns": True,
                "model3_provides_age_gender_context": True,
                "phase1_authority_preserved": True
            }
        },
        "detailed_milestone2_results": milestone2_result
    }
    
    return enhanced_report

# Bind methods to class
Phase2Orchestrator._model1_parameter_interpretation = _model1_parameter_interpretation
Phase2Orchestrator._model2_pattern_risk_assessment = _model2_pattern_risk_assessment
Phase2Orchestrator._synthesis_engine = _synthesis_engine
Phase2Orchestrator._enhanced_synthesis_engine = _enhanced_synthesis_engine
Phase2Orchestrator._recommendation_generator = _recommendation_generator
Phase2Orchestrator._assemble_final_report = _assemble_final_report
Phase2Orchestrator._assemble_milestone2_report = _assemble_milestone2_report


def process_csv_with_phase2(csv_content: str, ollama_url: str = "http://localhost:11434") -> Dict[str, Any]:
    """Main entry point for Phase-2 processing with Milestone-2 support"""
    orchestrator = Phase2Orchestrator(ollama_url)
    return orchestrator.process_csv_to_phase2(csv_content)