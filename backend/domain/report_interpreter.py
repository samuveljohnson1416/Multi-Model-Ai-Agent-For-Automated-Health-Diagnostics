"""
Report interpreter — analyzes validated parameters and generates clinical summary.

Replaces the minimal interpreter.py (48 lines) with a more complete version
that computes severity, groups abnormalities, and produces a structured summary.
Pure domain logic — no I/O.
"""

from typing import Dict, List, Any, Optional
from ..models.blood_parameter import BloodParameter, ParameterStatus


def compute_deviation(value: float, ref_min: float, ref_max: float) -> tuple[float, str]:
    """
    Compute how far a value deviates from its reference range.

    Returns:
        (deviation_percent, severity) where severity is Mild/Moderate/Severe.
    """
    if ref_min <= value <= ref_max:
        return 0.0, "Normal"

    if value < ref_min and ref_min > 0:
        deviation = ((ref_min - value) / ref_min) * 100
    elif value > ref_max and ref_max > 0:
        deviation = ((value - ref_max) / ref_max) * 100
    else:
        deviation = 0.0

    deviation = round(deviation, 1)

    if deviation < 10:
        severity = "Mild"
    elif deviation < 25:
        severity = "Moderate"
    else:
        severity = "Severe"

    return deviation, severity


def interpret_parameters(
    parameters: List[BloodParameter],
) -> Dict[str, Any]:
    """
    Analyze a list of validated blood parameters and produce a clinical summary.

    Args:
        parameters: List of BloodParameter objects with status already set.

    Returns:
        Dict with:
          - summary: {total, normal, low, high, critical}
          - abnormal_parameters: List of abnormal BloodParameter objects
          - severity_breakdown: {Mild: n, Moderate: n, Severe: n}
          - recommendations: List of recommendation strings
    """
    normal_count = 0
    low_count = 0
    high_count = 0
    critical_count = 0
    abnormal: List[BloodParameter] = []
    severity_counts = {"Mild": 0, "Moderate": 0, "Severe": 0}

    for param in parameters:
        if param.status == ParameterStatus.NORMAL:
            normal_count += 1
        elif param.status == ParameterStatus.LOW:
            low_count += 1
            abnormal.append(param)
            if param.severity:
                severity_counts[param.severity] = severity_counts.get(param.severity, 0) + 1
        elif param.status == ParameterStatus.HIGH:
            high_count += 1
            abnormal.append(param)
            if param.severity:
                severity_counts[param.severity] = severity_counts.get(param.severity, 0) + 1
        elif param.status == ParameterStatus.CRITICAL:
            critical_count += 1
            abnormal.append(param)
            severity_counts["Severe"] = severity_counts.get("Severe", 0) + 1

    total = len(parameters)
    abnormal_count = low_count + high_count + critical_count

    # Generate recommendations
    recommendations = _generate_recommendations(
        abnormal, abnormal_count, total, critical_count
    )

    return {
        "summary": {
            "total_parameters": total,
            "normal": normal_count,
            "low": low_count,
            "high": high_count,
            "critical": critical_count,
            "abnormal_count": abnormal_count,
            "normal_percentage": round(
                (normal_count / total * 100) if total > 0 else 0, 1
            ),
        },
        "abnormal_parameters": abnormal,
        "severity_breakdown": severity_counts,
        "recommendations": recommendations,
    }


def _generate_recommendations(
    abnormal: List[BloodParameter],
    abnormal_count: int,
    total: int,
    critical_count: int,
) -> List[str]:
    """Generate basic clinical recommendations from parameter analysis."""
    recommendations = []

    if abnormal_count == 0:
        recommendations.append(
            "✅ All parameters are within normal ranges. Continue maintaining a healthy lifestyle."
        )
        return recommendations

    recommendations.append(
        f"Found {abnormal_count} abnormal parameter(s) out of {total} tested."
    )

    if critical_count > 0:
        recommendations.append(
            "⚠️ Critical values detected. Seek immediate medical attention."
        )

    # Group by type of concern
    low_params = [p for p in abnormal if p.status == ParameterStatus.LOW]
    high_params = [p for p in abnormal if p.status == ParameterStatus.HIGH]

    if low_params:
        names = ", ".join(p.name for p in low_params[:5])
        recommendations.append(f"Low values: {names}. Discuss with your healthcare provider.")

    if high_params:
        names = ", ".join(p.name for p in high_params[:5])
        recommendations.append(f"High values: {names}. Discuss with your healthcare provider.")

    recommendations.append(
        "Schedule a follow-up consultation with your healthcare provider for personalized advice."
    )

    return recommendations
