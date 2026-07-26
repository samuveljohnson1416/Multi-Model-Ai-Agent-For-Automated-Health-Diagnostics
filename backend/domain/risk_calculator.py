"""
Risk calculator — Framingham CVD risk, lipid ratios, and metabolic syndrome.

Ported from src/core/advanced_risk_calculator.py.
Pure domain logic — no I/O, no API calls.
"""

import math
from typing import Dict, Optional, List, Any


# ──────────────────────────────────────────────────────────────
# Framingham Risk Score Tables
# ──────────────────────────────────────────────────────────────

_MALE_AGE_POINTS = {
    (20, 34): -9, (35, 39): -4, (40, 44): 0, (45, 49): 3,
    (50, 54): 6, (55, 59): 8, (60, 64): 10, (65, 69): 11,
    (70, 74): 12, (75, 79): 13,
}

_FEMALE_AGE_POINTS = {
    (20, 34): -7, (35, 39): -3, (40, 44): 0, (45, 49): 3,
    (50, 54): 6, (55, 59): 8, (60, 64): 10, (65, 69): 12,
    (70, 74): 14, (75, 79): 16,
}

_MALE_TC_POINTS = {
    (20, 39): {(0, 159): 0, (160, 199): 4, (200, 239): 7, (240, 279): 9, (280, 999): 11},
    (40, 49): {(0, 159): 0, (160, 199): 3, (200, 239): 5, (240, 279): 6, (280, 999): 8},
    (50, 59): {(0, 159): 0, (160, 199): 2, (200, 239): 3, (240, 279): 4, (280, 999): 5},
    (60, 69): {(0, 159): 0, (160, 199): 1, (200, 239): 1, (240, 279): 2, (280, 999): 3},
    (70, 79): {(0, 159): 0, (160, 199): 0, (200, 239): 0, (240, 279): 1, (280, 999): 1},
}

_FEMALE_TC_POINTS = {
    (20, 39): {(0, 159): 0, (160, 199): 4, (200, 239): 8, (240, 279): 11, (280, 999): 13},
    (40, 49): {(0, 159): 0, (160, 199): 3, (200, 239): 6, (240, 279): 8, (280, 999): 10},
    (50, 59): {(0, 159): 0, (160, 199): 2, (200, 239): 4, (240, 279): 5, (280, 999): 7},
    (60, 69): {(0, 159): 0, (160, 199): 1, (200, 239): 2, (240, 279): 3, (280, 999): 4},
    (70, 79): {(0, 159): 0, (160, 199): 1, (200, 239): 1, (240, 279): 2, (280, 999): 2},
}

_HDL_POINTS = {(60, 999): -1, (50, 59): 0, (40, 49): 1, (0, 39): 2}

_MALE_SMOKING_POINTS = {(20, 39): 8, (40, 49): 5, (50, 59): 3, (60, 69): 1, (70, 79): 1}
_FEMALE_SMOKING_POINTS = {(20, 39): 9, (40, 49): 7, (50, 59): 4, (60, 69): 2, (70, 79): 1}

# 10-year risk by total points (male)
_MALE_RISK_PERCENT = {
    0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 4,
    9: 5, 10: 6, 11: 8, 12: 10, 13: 12, 14: 16, 15: 20, 16: 25,
}

# 10-year risk by total points (female)
_FEMALE_RISK_PERCENT = {
    9: 1, 10: 1, 11: 1, 12: 1, 13: 2, 14: 2, 15: 3, 16: 4,
    17: 5, 18: 6, 19: 8, 20: 11, 21: 14, 22: 17, 23: 22, 24: 27,
}


# ──────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────


def _lookup_range(table: dict, value: float) -> int:
    """Look up a value in a range-keyed table."""
    for (low, high), points in table.items():
        if low <= value <= high:
            return points
    return 0


def _lookup_tc_points(age: int, tc: float, is_male: bool) -> int:
    """Look up total cholesterol points by age group."""
    table = _MALE_TC_POINTS if is_male else _FEMALE_TC_POINTS
    for (age_low, age_high), tc_table in table.items():
        if age_low <= age <= age_high:
            return _lookup_range(tc_table, tc)
    return 0


def _lookup_smoking_points(age: int, is_male: bool) -> int:
    """Look up smoking points by age group."""
    table = _MALE_SMOKING_POINTS if is_male else _FEMALE_SMOKING_POINTS
    for (low, high), points in table.items():
        if low <= age <= high:
            return points
    return 0


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def calculate_framingham_risk(
    age: int,
    gender: str,
    total_cholesterol: Optional[float] = None,
    hdl: Optional[float] = None,
    is_smoker: bool = False,
) -> Dict[str, Any]:
    """
    Calculate 10-year cardiovascular disease risk using Framingham Risk Score.

    Args:
        age: Patient age (20-79)
        gender: "male" or "female"
        total_cholesterol: Total cholesterol in mg/dL
        hdl: HDL cholesterol in mg/dL
        is_smoker: Smoking status

    Returns:
        Dict with: total_points, risk_percent, risk_category
    """
    if age < 20 or age > 79:
        return {"error": "Age must be between 20 and 79 for Framingham risk"}

    is_male = gender.lower() == "male"

    # Age points
    age_table = _MALE_AGE_POINTS if is_male else _FEMALE_AGE_POINTS
    total_points = _lookup_range(age_table, age)

    # Total cholesterol points
    if total_cholesterol is not None:
        total_points += _lookup_tc_points(age, total_cholesterol, is_male)

    # HDL points
    if hdl is not None:
        total_points += _lookup_range(_HDL_POINTS, hdl)

    # Smoking points
    if is_smoker:
        total_points += _lookup_smoking_points(age, is_male)

    # Look up 10-year risk
    risk_table = _MALE_RISK_PERCENT if is_male else _FEMALE_RISK_PERCENT
    risk_percent = risk_table.get(total_points, 30 if total_points > 16 else 1)

    # Risk category
    if risk_percent < 10:
        category = "low"
    elif risk_percent < 20:
        category = "moderate"
    else:
        category = "high"

    return {
        "total_points": total_points,
        "risk_percent": risk_percent,
        "risk_category": category,
        "description": f"{risk_percent}% risk of cardiovascular event in 10 years",
    }


def calculate_lipid_ratios(
    total_cholesterol: Optional[float] = None,
    hdl: Optional[float] = None,
    ldl: Optional[float] = None,
    triglycerides: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Calculate clinical lipid ratios.

    Returns:
        Dict with computed ratios and their risk categories.
    """
    ratios = {}

    if total_cholesterol and hdl and hdl > 0:
        tc_hdl_ratio = round(total_cholesterol / hdl, 2)
        ratios["tc_hdl_ratio"] = {
            "value": tc_hdl_ratio,
            "optimal": "< 5.0",
            "status": "optimal" if tc_hdl_ratio < 5.0 else "elevated",
        }

    if ldl and hdl and hdl > 0:
        ldl_hdl_ratio = round(ldl / hdl, 2)
        ratios["ldl_hdl_ratio"] = {
            "value": ldl_hdl_ratio,
            "optimal": "< 3.5",
            "status": "optimal" if ldl_hdl_ratio < 3.5 else "elevated",
        }

    if triglycerides and hdl and hdl > 0:
        tg_hdl_ratio = round(triglycerides / hdl, 2)
        ratios["tg_hdl_ratio"] = {
            "value": tg_hdl_ratio,
            "optimal": "< 2.0",
            "status": "optimal" if tg_hdl_ratio < 2.0 else "elevated",
        }

    # Non-HDL cholesterol
    if total_cholesterol and hdl:
        non_hdl = round(total_cholesterol - hdl, 1)
        ratios["non_hdl_cholesterol"] = {
            "value": non_hdl,
            "optimal": "< 130 mg/dL",
            "status": "optimal" if non_hdl < 130 else "elevated",
        }

    return ratios


def calculate_basic_risk(
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Calculate basic health risk score from abnormal parameter counts.

    Args:
        parameters: Dict of parameter_name → {status, value, ...}

    Returns:
        Dict with risk_score (0-1), risk_level, risk_factors
    """
    risk_factors = []
    risk_score = 0.0

    for name, data in parameters.items():
        status = data.get("status", "UNKNOWN")
        if status == "HIGH":
            risk_score += 0.15
            risk_factors.append({"parameter": name, "status": status, "severity": "high"})
        elif status == "LOW":
            risk_score += 0.10
            risk_factors.append({"parameter": name, "status": status, "severity": "medium"})
        elif status == "CRITICAL":
            risk_score += 0.25
            risk_factors.append({"parameter": name, "status": status, "severity": "critical"})

    risk_score = min(risk_score, 1.0)

    if risk_score < 0.2:
        risk_level = "low"
    elif risk_score < 0.5:
        risk_level = "medium"
    elif risk_score < 0.8:
        risk_level = "high"
    else:
        risk_level = "critical"

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
    }
