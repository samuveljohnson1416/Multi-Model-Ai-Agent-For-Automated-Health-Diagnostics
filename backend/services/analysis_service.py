"""
Analysis Service
================
Orchestrates the Multi-Model AI analysis pipeline.

Extracted from src/ui/UI.py (perform_multi_model_analysis + perform_contextual_analysis).
All medical decisions remain rule-based via core.medical_logic.

Models:
  Model 1 – Parameter classification     (core.medical_logic)
  Model 2 – Pattern recognition           (core.medical_logic)
  Model 3 – Risk score computation        (core.medical_logic)
  Model 4 – Contextual analysis           (inline, age/gender/history/lifestyle)
  Phase-2  – LLM explanations             (phase2.phase2_integration_safe)

⚠️  No medical decisions are made in this file.
    All deterministic reasoning is delegated to core.medical_logic.
"""

import logging
import re
from typing import Optional

from core.interpreter import (
    consolidate_multi_model_results,
    calculate_severity_metrics,
    generate_deterministic_recommendations,
)
from core.medical_logic import MedicalLogic

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_analysis(
    validated_data: dict,
    phase1_csv: Optional[str] = None,
    user_context: Optional[dict] = None,
    run_phase2: bool = True,
    run_contextual: bool = True,
) -> dict:
    """
    Run the full multi-model analysis pipeline.

    Args:
        validated_data:  Parameter dict from core.validator (keys = param names,
                         values = {value, unit, status, reference_range}).
        phase1_csv:      CSV string from phase1 extraction (optional).
        user_context:    Dict with age, gender, medical_history, lifestyle (optional).
        run_phase2:      Whether to attempt Phase-2 LLM analysis.
        run_contextual:  Whether to run contextual (Model-4) analysis.

    Returns:
        Flat dict compatible with AnalysisResponse schema.
    """
    if not validated_data:
        return _empty_result("No validated data provided.")

    # ── Models 1, 2, 3 ───────────────────────────────────────────────────
    model1 = _run_model1(validated_data)
    model2 = _run_model2(validated_data)
    model3 = _run_model3(validated_data)

    # ── Consolidate ───────────────────────────────────────────────────────
    try:
        analysis = consolidate_multi_model_results(model1, model2, model3)
    except Exception as exc:
        logger.exception("Result consolidation failed")
        analysis = {**model1, **model2, **model3}

    # ── Recommendations ───────────────────────────────────────────────────
    try:
        analysis["recommendations"] = generate_deterministic_recommendations(analysis)
    except Exception as exc:
        logger.exception("Recommendation generation failed")
        analysis.setdefault("recommendations", [])

    # ── Phase-2 LLM analysis (optional) ──────────────────────────────────
    analysis["phase2_result"] = None
    if run_phase2 and phase1_csv:
        analysis["phase2_result"] = _run_phase2(phase1_csv)

    # ── Contextual analysis – Model 4 (optional) ─────────────────────────
    analysis["contextual_analysis"] = None
    if run_contextual and user_context:
        analysis["contextual_analysis"] = _run_contextual(
            validated_data, user_context
        )

    analysis["success"] = True
    analysis["error"] = None
    analysis["decision_method"] = "RULE-BASED (medical_logic)"
    return analysis


# ---------------------------------------------------------------------------
# Model 1 – Parameter classification
# ---------------------------------------------------------------------------

def _run_model1(validated_data: dict) -> dict:
    """Classify each parameter and count normal/abnormal."""
    result: dict = {
        "total_parameters": len(validated_data),
        "classifications": {},
        "abnormal_parameters": 0,
        "normal_parameters": 0,
        "severity_analysis": {},
        "decision_method": "RULE-BASED (medical_logic)",
    }

    abnormal = 0
    normal = 0

    for param_name, param_info in validated_data.items():
        status = param_info.get("status", "UNKNOWN")
        if status in ("LOW", "HIGH"):
            abnormal += 1
        elif status == "NORMAL":
            normal += 1

        result["classifications"][param_name] = {
            "value": param_info.get("value"),
            "status": status,
            "reference_range": param_info.get("reference_range", ""),
        }

    result["abnormal_parameters"] = abnormal
    result["normal_parameters"] = normal

    try:
        result["severity_analysis"] = calculate_severity_metrics(validated_data)
    except Exception:
        pass

    return result


# ---------------------------------------------------------------------------
# Model 2 – Pattern recognition
# ---------------------------------------------------------------------------

def _run_model2(validated_data: dict) -> dict:
    """Detect clinical patterns across parameter combinations."""
    medical_logic = MedicalLogic()
    parameters = _build_param_floats(validated_data)

    patterns: list = []
    try:
        patterns = medical_logic.get_all_detected_patterns(parameters)
    except Exception as exc:
        logger.exception("Pattern detection failed")

    return {
        "patterns_detected": patterns,
        "pattern_count": len(patterns),
        "pattern_names": [p.get("pattern", "Unknown") for p in patterns],
        "decision_method": "RULE-BASED (medical_logic)",
    }


# ---------------------------------------------------------------------------
# Model 3 – Risk score computation
# ---------------------------------------------------------------------------

def _run_model3(validated_data: dict) -> dict:
    """Compute risk scores for anaemia, infection, bleeding, CVD, renal."""
    medical_logic = MedicalLogic()
    parameters = _build_param_floats(validated_data)

    overall: dict = {}
    try:
        overall = medical_logic.assess_overall_health_status(parameters)
    except Exception:
        pass

    def safe_risk(method_name: str) -> dict:
        try:
            return getattr(medical_logic, method_name)(parameters) or {}
        except Exception:
            return {}

    return {
        "overall_risk_level": overall.get("overall_risk_level", "Unknown"),
        "risk_score": overall.get("risk_score", 0.0),
        "patterns_detected": overall.get("patterns_detected", []),
        "requires_attention": overall.get("requires_attention", False),
        "recommendation": overall.get("recommendation", ""),
        "anemia_risk": safe_risk("calculate_anemia_risk_score"),
        "infection_risk": safe_risk("calculate_infection_risk_score"),
        "bleeding_risk": safe_risk("calculate_bleeding_risk_score"),
        "cardiovascular_risk": safe_risk("calculate_cardiovascular_risk_score"),
        "renal_risk": safe_risk("calculate_renal_risk_score"),
        "decision_method": "RULE-BASED (medical_logic)",
    }


# ---------------------------------------------------------------------------
# Phase-2 – LLM insights (non-blocking, always optional)
# ---------------------------------------------------------------------------

def _run_phase2(phase1_csv: str) -> Optional[dict]:
    try:
        from phase2.phase2_integration_safe import integrate_phase2_analysis

        result = integrate_phase2_analysis(phase1_csv)
        return result
    except ImportError:
        logger.warning("Phase-2 module not available")
        return {"phase2_status": "unavailable", "fallback_used": True}
    except Exception as exc:
        logger.exception("Phase-2 analysis failed")
        return {"phase2_status": "error", "error": str(exc), "fallback_used": True}


# ---------------------------------------------------------------------------
# Model 4 – Contextual analysis (age / gender / history / lifestyle)
# ---------------------------------------------------------------------------

def _run_contextual(validated_data: dict, user_context: dict) -> dict:
    """
    Adjust risk assessments based on patient demographics and lifestyle.
    Ported faithfully from src/ui/UI.py:perform_contextual_analysis().
    """
    age = user_context.get("age")
    gender = user_context.get("gender")
    medical_history = user_context.get("medical_history", [])
    lifestyle = user_context.get("lifestyle", {})

    analysis: dict = {
        "context_summary": {
            "age": age if age else "Not provided",
            "gender": gender if gender else "Not provided",
            "conditions": medical_history if medical_history else ["None reported"],
            "lifestyle": lifestyle if lifestyle else {"status": "Not provided"},
        },
        "adjusted_risks": {},
        "personalized_insights": [],
        "lifestyle_impact": [],
        "age_gender_considerations": [],
        "recommendations": [],
    }

    # ── helpers ────────────────────────────────────────────────────────────
    def get_value(param: str) -> Optional[float]:
        for key, info in validated_data.items():
            if param.lower() in key.lower():
                try:
                    return float(info.get("value", 0))
                except Exception:
                    return None
        return None

    def get_status(param: str) -> str:
        for key, info in validated_data.items():
            if param.lower() in key.lower():
                return info.get("status", "UNKNOWN")
        return "UNKNOWN"

    hb = get_value("hemoglobin")
    hb_status = get_status("hemoglobin")
    glucose = get_value("glucose")
    cholesterol = get_value("cholesterol")

    # ── Age-based insights ────────────────────────────────────────────────
    age_risk_modifier = 1.0
    age_insights: list = []

    if age:
        if age < 18:
            age_insights += [
                "Pediatric patient – reference ranges may differ from adult values",
                "Growth and development factors should be considered",
            ]
        elif age < 40:
            age_insights.append(
                "Young adult – baseline values important for future comparison"
            )
        elif age < 60:
            age_insights.append(
                "Middle-aged – increased cardiovascular screening recommended"
            )
            age_risk_modifier = 1.2
            if cholesterol and cholesterol > 180:
                age_insights.append(
                    "⚠️ Cholesterol monitoring important at this age"
                )
        else:
            age_insights += [
                "Senior patient – age-related changes in blood values expected",
                "More frequent monitoring recommended",
            ]
            age_risk_modifier = 1.4
            if hb and hb < 13:
                age_insights.append(
                    "⚠️ Anaemia more common in elderly – investigate cause"
                )

    analysis["age_gender_considerations"].extend(age_insights)

    # ── Gender-based insights ─────────────────────────────────────────────
    gender_insights: list = []
    if gender:
        if gender.lower() == "female":
            gender_insights.append("Female reference ranges applied")
            if hb:
                if hb < 12:
                    gender_insights.append(
                        "⚠️ Haemoglobin below female normal range (12-16 g/dL)"
                    )
                elif 12 <= hb <= 16:
                    gender_insights.append(
                        "✅ Haemoglobin within female normal range"
                    )
            if age and 45 <= age <= 55:
                gender_insights += [
                    "Perimenopausal age – hormonal changes may affect blood values",
                    "Iron deficiency more common during this period",
                ]
        elif gender.lower() == "male":
            gender_insights.append("Male reference ranges applied")
            if hb:
                if hb < 14:
                    gender_insights.append(
                        "⚠️ Haemoglobin below male normal range (14-18 g/dL)"
                    )
                elif 14 <= hb <= 18:
                    gender_insights.append(
                        "✅ Haemoglobin within male normal range"
                    )
            if age and age >= 50:
                gender_insights.append(
                    "PSA screening recommended for males over 50"
                )

    analysis["age_gender_considerations"].extend(gender_insights)

    # ── Medical history ───────────────────────────────────────────────────
    history_insights: list = []
    history_risk_modifier = 1.0

    def _add_rec(category, priority, finding, risk, reasoning, actions):
        analysis["recommendations"].append(
            {
                "category": category,
                "priority": priority,
                "traceability": {
                    "finding": finding,
                    "risk": risk,
                    "reasoning": reasoning,
                },
                "actions": actions,
            }
        )

    if "Diabetes" in medical_history:
        history_insights.append("🩺 Diabetes History: Glucose monitoring critical")
        history_risk_modifier += 0.3
        gf = f"Glucose: {glucose} mg/dL" if glucose else "Glucose level in report"
        if glucose and glucose > 126:
            history_insights.append(
                "⚠️ Fasting glucose elevated – diabetes control needs attention"
            )
        elif glucose and glucose > 100:
            history_insights.append(
                "⚠️ Pre-diabetic range – lifestyle modifications important"
            )
        _add_rec(
            "Diabetes Management", "High",
            f"Medical History: Diabetes + {gf}",
            "Elevated metabolic risk due to diabetes history",
            "Because you have diabetes history → blood sugar control is critical → regular monitoring prevents complications",
            ["Regular HbA1c monitoring every 3 months", "Maintain blood sugar diary", "Follow diabetic diet plan"],
        )

    if "Hypertension" in medical_history:
        history_insights.append(
            "🩺 Hypertension History: Cardiovascular risk elevated"
        )
        history_risk_modifier += 0.2
        cf = f"Cholesterol: {cholesterol} mg/dL" if cholesterol else "Cholesterol in report"
        if cholesterol and cholesterol > 200:
            history_insights.append(
                "⚠️ High cholesterol + hypertension = increased heart disease risk"
            )
        _add_rec(
            "Blood Pressure Management", "High",
            f"Medical History: Hypertension + {cf}",
            "Elevated cardiovascular risk due to hypertension",
            "Because you have hypertension → blood vessels under strain → sodium reduction and weight management reduce heart attack/stroke risk",
            ["Reduce sodium intake", "Regular BP monitoring", "Maintain healthy weight"],
        )

    if "Heart Disease" in medical_history:
        history_insights.append(
            "🩺 Heart Disease History: Cardiac markers important"
        )
        history_risk_modifier += 0.4
        _add_rec(
            "Cardiac Care", "High",
            "Medical History: Heart Disease",
            "High cardiovascular risk due to existing heart condition",
            "Because you have heart disease history → cardiac function compromised → regular monitoring and activity modification prevent cardiac events",
            ["Regular cardiac checkups", "Monitor cholesterol and triglycerides", "Avoid strenuous activity without clearance"],
        )

    if "Anemia" in medical_history:
        history_insights.append(
            "🩺 Anaemia History: Haemoglobin monitoring essential"
        )
        hb_finding = f"Current Hb: {hb} g/dL ({hb_status})" if hb else "Haemoglobin in report"
        if hb_status == "LOW":
            history_insights.append(
                "⚠️ Current low Hb confirms ongoing anaemia – treatment needed"
            )
        _add_rec(
            "Anaemia Management", "Medium",
            f"Medical History: Anaemia + {hb_finding}",
            "Ongoing anaemia risk based on history",
            "Because you have anaemia history → prone to low haemoglobin → iron-rich diet and supplements maintain healthy blood levels",
            ["Iron-rich diet", "Consider iron supplements", "Identify and treat underlying cause"],
        )

    if "Thyroid Disorder" in medical_history:
        history_insights.append("🩺 Thyroid History: TSH monitoring recommended")
        _add_rec(
            "Thyroid Management", "Medium",
            "Medical History: Thyroid Disorder",
            "Metabolic imbalance risk due to thyroid condition",
            "Because you have thyroid disorder → metabolism affected → regular TSH monitoring ensures proper medication dosing",
            ["Regular TSH testing", "Medication compliance", "Watch for fatigue/weight changes"],
        )

    if "Kidney Disease" in medical_history:
        history_insights.append(
            "🩺 Kidney Disease History: Creatinine and eGFR critical"
        )
        history_risk_modifier += 0.3
        _add_rec(
            "Kidney Care", "High",
            "Medical History: Kidney Disease",
            "Renal function decline risk",
            "Because you have kidney disease → filtration capacity reduced → monitoring creatinine/BUN and limiting protein prevents further damage",
            ["Monitor creatinine and BUN", "Limit protein intake as advised", "Stay hydrated"],
        )

    if "Liver Disease" in medical_history:
        history_insights.append(
            "🩺 Liver Disease History: Liver function tests important"
        )
        _add_rec(
            "Liver Care", "High",
            "Medical History: Liver Disease",
            "Hepatic function compromise risk",
            "Because you have liver disease → detoxification impaired → avoiding alcohol and monitoring enzymes prevents further liver damage",
            ["Avoid alcohol completely", "Monitor liver enzymes", "Hepatitis screening if not done"],
        )

    analysis["personalized_insights"].extend(history_insights)

    # ── Lifestyle impact ──────────────────────────────────────────────────
    lifestyle_insights: list = []
    lifestyle_risk_modifier = 1.0

    smoker = lifestyle.get("smoker", False)
    alcohol = lifestyle.get("alcohol", "None")
    exercise = lifestyle.get("exercise", "Moderate")
    diet = lifestyle.get("diet", "Balanced")

    if smoker:
        lifestyle_insights += [
            "🚬 Smoker: Increased cardiovascular and respiratory risk",
            "Smoking affects oxygen-carrying capacity of blood",
        ]
        lifestyle_risk_modifier += 0.3
        if hb_status == "HIGH":
            lifestyle_insights.append(
                "⚠️ Elevated Hb may be compensatory response to smoking"
            )
        _add_rec(
            "Smoking Cessation", "High",
            "Lifestyle: Active Smoker",
            "Elevated cardiovascular, respiratory, and cancer risk",
            "Because you smoke → blood oxygen reduced, vessels damaged → quitting dramatically reduces heart attack and lung disease risk",
            ["Consider smoking cessation programme", "Nicotine replacement therapy", "Lung function screening"],
        )

    if alcohol == "Heavy":
        lifestyle_insights += [
            "🍺 Heavy Alcohol: Liver and blood cell production affected",
            "Alcohol can cause macrocytic anaemia and liver damage",
        ]
        lifestyle_risk_modifier += 0.25
        _add_rec(
            "Alcohol Reduction", "High",
            "Lifestyle: Heavy Alcohol Consumption",
            "Liver damage and blood cell production impairment",
            "Because you consume heavy alcohol → liver stressed, bone marrow affected → reducing intake prevents cirrhosis and anaemia",
            ["Reduce alcohol intake", "Liver function monitoring", "Consider counselling"],
        )
    elif alcohol == "Moderate":
        lifestyle_insights.append(
            "🍺 Moderate Alcohol: Monitor liver function periodically"
        )

    if exercise == "Sedentary":
        lifestyle_insights.append("🪑 Sedentary Lifestyle: Increased metabolic risk")
        lifestyle_risk_modifier += 0.15
        _add_rec(
            "Physical Activity", "Medium",
            "Lifestyle: Sedentary (Low Physical Activity)",
            "Increased metabolic syndrome, obesity, and cardiovascular risk",
            "Because you have sedentary lifestyle → metabolism slows → regular exercise improves heart health and blood sugar control",
            ["Start with 15-20 min daily walks", "Gradually increase activity", "Aim for 150 min/week moderate exercise"],
        )
    elif exercise == "Active":
        lifestyle_insights.append("🏃 Active Lifestyle: Good for cardiovascular health")
        lifestyle_risk_modifier -= 0.1

    if diet == "High Fat/Sugar":
        lifestyle_insights.append("🍔 High Fat/Sugar Diet: Metabolic syndrome risk")
        lifestyle_risk_modifier += 0.2
        diet_findings = "Lifestyle: High Fat/Sugar Diet"
        if glucose and glucose > 100:
            lifestyle_insights.append("⚠️ Diet contributing to elevated glucose")
            diet_findings += f" + Glucose: {glucose} mg/dL"
        if cholesterol and cholesterol > 200:
            lifestyle_insights.append("⚠️ Diet contributing to elevated cholesterol")
            diet_findings += f" + Cholesterol: {cholesterol} mg/dL"
        _add_rec(
            "Dietary Changes", "High",
            diet_findings,
            "Elevated risk of diabetes, heart disease, and obesity",
            "Because your diet is high in fat/sugar → blood sugar spikes, cholesterol rises → switching to whole foods reduces risk",
            ["Reduce processed foods", "Increase fibre intake", "Choose whole grains over refined"],
        )
    elif diet == "Vegetarian":
        lifestyle_insights.append("🥗 Vegetarian Diet: Monitor B12 and iron levels")
        if hb_status == "LOW":
            lifestyle_insights.append(
                "⚠️ Low Hb may be related to vegetarian diet – check B12/iron"
            )
            _add_rec(
                "Vegetarian Nutrition", "Medium",
                f"Lifestyle: Vegetarian Diet + Low Haemoglobin ({hb} g/dL)",
                "Iron and B12 deficiency risk common in vegetarians",
                "Because you follow vegetarian diet + have low Hb → plant iron less absorbable, B12 lacking → fortified foods and supplements prevent deficiency",
                ["Include fortified cereals and plant milks", "Consider B12 supplements", "Pair iron-rich foods with Vitamin C"],
            )

    analysis["lifestyle_impact"] = lifestyle_insights

    # ── Adjusted risk scores ──────────────────────────────────────────────
    total_modifier = age_risk_modifier * history_risk_modifier * lifestyle_risk_modifier

    base_anemia = 60 if hb_status == "LOW" else 10
    base_cardiac = 50 if (cholesterol and cholesterol > 200) else 10
    base_metabolic = 50 if (glucose and glucose > 100) else 10

    analysis["adjusted_risks"] = {
        "anemia_risk": {
            "base": base_anemia,
            "adjusted": min(100, int(base_anemia * total_modifier)),
            "modifier": round(total_modifier, 2),
            "level": (
                "High" if min(100, int(base_anemia * total_modifier)) > 60
                else "Moderate" if min(100, int(base_anemia * total_modifier)) > 30
                else "Low"
            ),
        },
        "cardiac_risk": {
            "base": base_cardiac,
            "adjusted": min(100, int(base_cardiac * total_modifier)),
            "modifier": round(total_modifier, 2),
            "level": (
                "High" if min(100, int(base_cardiac * total_modifier)) > 60
                else "Moderate" if min(100, int(base_cardiac * total_modifier)) > 30
                else "Low"
            ),
        },
        "metabolic_risk": {
            "base": base_metabolic,
            "adjusted": min(100, int(base_metabolic * total_modifier)),
            "modifier": round(total_modifier, 2),
            "level": (
                "High" if min(100, int(base_metabolic * total_modifier)) > 60
                else "Moderate" if min(100, int(base_metabolic * total_modifier)) > 30
                else "Low"
            ),
        },
        "overall_modifier": round(total_modifier, 2),
    }

    return analysis


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_param_floats(validated_data: dict) -> dict:
    """Build {param_name_lower: float_value} for medical_logic methods."""
    params: dict = {}
    for name, info in validated_data.items():
        try:
            params[name.lower()] = float(info.get("value", 0))
        except (ValueError, TypeError):
            continue
    return params


def _empty_result(error_msg: str) -> dict:
    return {
        "total_parameters": 0,
        "classifications": {},
        "abnormal_parameters": 0,
        "normal_parameters": 0,
        "patterns_detected": [],
        "pattern_count": 0,
        "recommendations": [],
        "phase2_result": None,
        "contextual_analysis": None,
        "success": False,
        "error": error_msg,
        "decision_method": "RULE-BASED",
    }