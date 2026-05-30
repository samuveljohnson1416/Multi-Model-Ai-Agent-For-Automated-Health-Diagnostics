"""
Interpretation Module - Unified Interface for Medical Result Analysis
Consolidates all deterministic medical logic from phase2_orchestrator, medical_logic, and UI analysis.
All decisions are RULE-BASED and auditable (deterministic: true).
"""

from typing import Dict, List, Any, Optional
from enum import Enum


class InterpretationStatus(Enum):
    """Status classifications"""
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"
    BORDERLINE = "Borderline"
    MISSING = "Missing"
    UNKNOWN = "Unknown"


class RiskSeverity(Enum):
    """Risk severity levels"""
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    SEVERE = "Severe"


def interpret_results(validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy interface: Interpret results from validated parameter data.
    Aggregates LOW/NORMAL/HIGH classifications and generates summary.
    
    Args:
        validated_data: Dict mapping parameter names to status/value/reference info
        
    Returns:
        Dict with summary, abnormal parameters, and recommendations
    """
    interpretation = {
        "summary": {},
        "abnormal_parameters": [],
        "recommendations": [],
        "decision_method": "RULE-BASED"
    }
    
    low_count = 0
    high_count = 0
    normal_count = 0
    
    for param_name, param_info in validated_data.items():
        status = param_info.get("status")
        
        if status == "LOW":
            low_count += 1
            interpretation["abnormal_parameters"].append({
                "parameter": param_name,
                "value": param_info.get("value"),
                "status": "LOW",
                "reference": param_info.get("reference_range", "N/A")
            })
        elif status == "HIGH":
            high_count += 1
            interpretation["abnormal_parameters"].append({
                "parameter": param_name,
                "value": param_info.get("value"),
                "status": "HIGH",
                "reference": param_info.get("reference_range", "N/A")
            })
        elif status == "NORMAL":
            normal_count += 1
    
    interpretation["summary"] = {
        "total_parameters": len(validated_data),
        "normal": normal_count,
        "low": low_count,
        "high": high_count
    }
    
    if low_count == 0 and high_count == 0:
        interpretation["recommendations"].append("All parameters are normal.")
    else:
        interpretation["recommendations"].append(f"Found {low_count + high_count} abnormal parameter(s).")
        interpretation["recommendations"].append("Consult a doctor for detailed analysis.")
    
    return interpretation


def consolidate_multi_model_results(model1_result: Dict, model2_result: Dict, 
                                   model3_result: Dict) -> Dict[str, Any]:
    """
    Consolidate results from all three deterministic models into unified analysis.
    
    Model 1: Parameter interpretation (LOW/NORMAL/HIGH classification)
    Model 2: Pattern recognition & risk detection  
    Model 3: Risk score computation
    
    Args:
        model1_result: Parameter classification results (from medical_logic)
        model2_result: Pattern/risk detection results (from medical_logic or advanced_pattern_analysis)
        model3_result: Risk scoring results (from medical_logic or advanced_risk_calculator)
        
    Returns:
        Consolidated analysis with all findings, severity assessment, and recommendations
    """
    consolidated = {
        "parameter_analysis": model1_result,
        "pattern_analysis": model2_result,
        "risk_assessment": model3_result,
        "overall_summary": {},
        "findings": [],
        "recommendations": [],
        "decision_method": "RULE-BASED (deterministic)"
    }
    
    # Extract counts
    total_params = model1_result.get("summary", {}).get("total_parameters", 0)
    abnormal_count = (
        model1_result.get("summary", {}).get("low", 0) +
        model1_result.get("summary", {}).get("high", 0)
    )
    
    # Extract patterns
    patterns = model2_result.get("patterns_detected", []) if model2_result else []
    pattern_count = len(patterns) if isinstance(patterns, list) else 0
    
    # Extract risk assessment
    risk_level = model3_result.get("risk_level", "Unknown") if model3_result else "Unknown"
    risk_score = model3_result.get("risk_score", 0.0) if model3_result else 0.0
    
    # Build overall summary
    consolidated["overall_summary"] = {
        "total_parameters_analyzed": total_params,
        "abnormal_parameters": abnormal_count,
        "normal_percentage": round((total_params - abnormal_count) / total_params * 100, 1) if total_params > 0 else 0,
        "patterns_detected": pattern_count,
        "overall_risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "requires_attention": abnormal_count > 0 or pattern_count > 0 or risk_score >= 0.4
    }
    
    # Generate findings
    if abnormal_count > 0:
        consolidated["findings"].append(f"{abnormal_count} abnormal parameter(s) detected out of {total_params}")
    
    if pattern_count > 0:
        pattern_names = [p.get("pattern", "Unknown") for p in patterns if isinstance(p, dict)]
        consolidated["findings"].append(f"Clinical patterns detected: {', '.join(pattern_names)}")
    
    if risk_score >= 0.7:
        consolidated["findings"].append("HIGH RISK STATUS - Immediate medical consultation recommended")
    elif risk_score >= 0.4:
        consolidated["findings"].append("MODERATE RISK STATUS - Follow-up consultation recommended")
    else:
        consolidated["findings"].append("LOW RISK STATUS - Continue regular monitoring")
    
    # Generate recommendations
    if abnormal_count > 0 and pattern_count > 0:
        consolidated["recommendations"].append("Multiple abnormal findings with detected patterns - urgent medical evaluation needed")
    elif abnormal_count > 5:
        consolidated["recommendations"].append("Multiple abnormalities detected - comprehensive medical evaluation recommended")
    elif abnormal_count > 0:
        consolidated["recommendations"].append("Some abnormalities detected - follow-up testing may be needed")
    
    if risk_score >= 0.7:
        consolidated["recommendations"].append("Seek immediate consultation with qualified healthcare professional")
    elif risk_score >= 0.4:
        consolidated["recommendations"].append("Schedule appointment with healthcare provider for detailed evaluation")
    else:
        consolidated["recommendations"].append("Continue routine health monitoring")
    
    return consolidated


def calculate_severity_metrics(parameters: Dict[str, Dict]) -> Dict[str, Any]:
    """
    Calculate severity metrics for each abnormal parameter.
    
    Args:
        parameters: Dict mapping parameter names to their status/value/reference info
        
    Returns:
        Dict with severity analysis for each abnormal parameter
    """
    severity_analysis = {
        "total_abnormal": 0,
        "severe_abnormalities": [],
        "moderate_abnormalities": [],
        "mild_abnormalities": [],
        "severity_distribution": {}
    }
    
    for param_name, param_info in parameters.items():
        status = param_info.get("status")
        
        if status not in ["LOW", "HIGH"]:
            continue
        
        severity_analysis["total_abnormal"] += 1
        
        try:
            value = float(param_info.get("value", 0))
            ref_range = str(param_info.get("reference_range", ""))
            
            # Parse reference range
            deviation = 0.0
            if "-" in ref_range:
                parts = ref_range.replace("(", "").replace(")", "").split("-")
                try:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    mid_val = (min_val + max_val) / 2
                    
                    if status == "LOW":
                        deviation = abs((value - min_val) / min_val) * 100 if min_val != 0 else 0
                    else:
                        deviation = abs((value - max_val) / max_val) * 100 if max_val != 0 else 0
                except (ValueError, ZeroDivisionError):
                    deviation = 0.0
            
            # Classify severity
            if deviation >= 25:
                severity = RiskSeverity.SEVERE.value
                severity_analysis["severe_abnormalities"].append({
                    "parameter": param_name,
                    "status": status,
                    "value": value,
                    "deviation_percent": round(deviation, 1)
                })
            elif deviation >= 10:
                severity = RiskSeverity.MODERATE.value
                severity_analysis["moderate_abnormalities"].append({
                    "parameter": param_name,
                    "status": status,
                    "value": value,
                    "deviation_percent": round(deviation, 1)
                })
            else:
                severity = RiskSeverity.LOW.value
                severity_analysis["mild_abnormalities"].append({
                    "parameter": param_name,
                    "status": status,
                    "value": value,
                    "deviation_percent": round(deviation, 1)
                })
            
        except (ValueError, TypeError):
            severity = RiskSeverity.UNKNOWN.value
    
    severity_analysis["severity_distribution"] = {
        "severe": len(severity_analysis["severe_abnormalities"]),
        "moderate": len(severity_analysis["moderate_abnormalities"]),
        "mild": len(severity_analysis["mild_abnormalities"])
    }
    
    return severity_analysis


def generate_deterministic_recommendations(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate recommendations based on RULE-BASED analysis (NO LLM).
    All recommendations are derived from deterministic rules, not generative AI.
    
    Args:
        analysis: Dict containing parameter analysis, patterns, and risk assessment
        
    Returns:
        List of recommendation dicts with category, priority, reasoning, and actions
    """
    recommendations = []
    
    summary = analysis.get("overall_summary", {})
    abnormal_count = summary.get("abnormal_parameters", 0)
    pattern_count = summary.get("patterns_detected", 0)
    risk_level = summary.get("overall_risk_level", "Low")
    
    # Rule 1: High abnormality count
    if abnormal_count >= 5:
        recommendations.append({
            "category": "Comprehensive Evaluation",
            "priority": "HIGH",
            "rule": "multiple_abnormalities_rule",
            "reasoning": f"Multiple abnormal parameters ({abnormal_count}) detected → increased health risk",
            "actions": [
                "Seek comprehensive medical evaluation",
                "Request complete diagnostic workup",
                "Schedule specialist consultation if indicated by results"
            ]
        })
    elif abnormal_count >= 3:
        recommendations.append({
            "category": "Follow-up Testing",
            "priority": "MEDIUM",
            "rule": "moderate_abnormalities_rule",
            "reasoning": f"Multiple abnormalities ({abnormal_count}) detected → follow-up needed",
            "actions": [
                "Schedule follow-up appointment with physician",
                "Repeat tests to confirm findings",
                "Discuss treatment options with healthcare provider"
            ]
        })
    
    # Rule 2: Pattern detection
    if pattern_count > 0:
        patterns = analysis.get("pattern_analysis", {}).get("patterns_detected", [])
        if isinstance(patterns, list) and len(patterns) > 0:
            recommendations.append({
                "category": "Pattern-Based Intervention",
                "priority": "HIGH",
                "rule": "pattern_detection_rule",
                "reasoning": f"Clinical patterns detected ({pattern_count}) → specific interventions indicated",
                "actions": [
                    "Consult specialist based on detected patterns",
                    "Initiate targeted diagnostic investigations",
                    "Begin appropriate management protocol"
                ]
            })
    
    # Rule 3: Risk level
    if risk_level == "High":
        recommendations.append({
            "category": "Urgent Medical Attention",
            "priority": "URGENT",
            "rule": "high_risk_rule",
            "reasoning": "High risk status → immediate medical evaluation required",
            "actions": [
                "Seek immediate medical consultation",
                "Do not delay - high-risk findings present",
                "Bring all test results to appointment"
            ]
        })
    elif risk_level == "Moderate":
        recommendations.append({
            "category": "Timely Consultation",
            "priority": "MEDIUM",
            "rule": "moderate_risk_rule",
            "reasoning": "Moderate risk status → professional medical review needed",
            "actions": [
                "Schedule appointment with healthcare provider",
                "Prepare detailed symptom history",
                "Bring all test reports and previous medical records"
            ]
        })
    else:
        recommendations.append({
            "category": "Routine Monitoring",
            "priority": "LOW",
            "rule": "low_risk_rule",
            "reasoning": "Low risk status → continue regular health monitoring",
            "actions": [
                "Maintain regular health check-ups",
                "Continue healthy lifestyle practices",
                "Retest as recommended by physician"
            ]
        })
    
    return recommendations
