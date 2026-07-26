"""
Dynamic Reference Ranges — age/gender-adjusted blood parameter ranges.

Ported from src/core/dynamic_reference_ranges.py.
Pure domain logic — no I/O, no API calls.
"""

from typing import Dict, Optional, Any


# ──────────────────────────────────────────────────────────────
# Age/gender-adjusted reference ranges (clinical data)
# ──────────────────────────────────────────────────────────────

DYNAMIC_RANGES: Dict[str, Any] = {
    "Hemoglobin": {
        "male": {
            "child_0_12": {"min": 11.5, "max": 15.5, "unit": "g/dL"},
            "teen_13_17": {"min": 13.0, "max": 16.0, "unit": "g/dL"},
            "adult_18_49": {"min": 14.0, "max": 18.0, "unit": "g/dL"},
            "adult_50_64": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
            "senior_65_plus": {"min": 12.5, "max": 17.0, "unit": "g/dL"},
        },
        "female": {
            "child_0_12": {"min": 11.5, "max": 15.5, "unit": "g/dL"},
            "teen_13_17": {"min": 12.0, "max": 16.0, "unit": "g/dL"},
            "adult_18_49": {"min": 12.0, "max": 16.0, "unit": "g/dL"},
            "adult_50_64": {"min": 11.5, "max": 15.5, "unit": "g/dL"},
            "senior_65_plus": {"min": 11.0, "max": 15.0, "unit": "g/dL"},
        },
        "default": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
    },
    "RBC": {
        "male": {
            "child_0_12": {"min": 4.0, "max": 5.5, "unit": "mill/cumm"},
            "teen_13_17": {"min": 4.5, "max": 5.5, "unit": "mill/cumm"},
            "adult_18_49": {"min": 4.7, "max": 6.1, "unit": "mill/cumm"},
            "adult_50_64": {"min": 4.5, "max": 5.9, "unit": "mill/cumm"},
            "senior_65_plus": {"min": 4.2, "max": 5.7, "unit": "mill/cumm"},
        },
        "female": {
            "child_0_12": {"min": 4.0, "max": 5.5, "unit": "mill/cumm"},
            "teen_13_17": {"min": 4.0, "max": 5.0, "unit": "mill/cumm"},
            "adult_18_49": {"min": 4.2, "max": 5.4, "unit": "mill/cumm"},
            "adult_50_64": {"min": 4.0, "max": 5.2, "unit": "mill/cumm"},
            "senior_65_plus": {"min": 3.8, "max": 5.0, "unit": "mill/cumm"},
        },
        "default": {"min": 4.5, "max": 5.5, "unit": "mill/cumm"},
    },
    "WBC": {
        "child_0_12": {"min": 5000, "max": 15000, "unit": "/cumm"},
        "teen_13_17": {"min": 4500, "max": 13000, "unit": "/cumm"},
        "adult_18_64": {"min": 4000, "max": 11000, "unit": "/cumm"},
        "senior_65_plus": {"min": 3500, "max": 10500, "unit": "/cumm"},
        "default": {"min": 4000, "max": 11000, "unit": "/cumm"},
    },
    "Platelet": {
        "child_0_12": {"min": 150000, "max": 450000, "unit": "/cumm"},
        "teen_13_17": {"min": 150000, "max": 400000, "unit": "/cumm"},
        "adult_18_64": {"min": 150000, "max": 400000, "unit": "/cumm"},
        "senior_65_plus": {"min": 140000, "max": 380000, "unit": "/cumm"},
        "default": {"min": 150000, "max": 400000, "unit": "/cumm"},
    },
    "MCV": {"default": {"min": 80.0, "max": 100.0, "unit": "fL"}},
    "MCH": {"default": {"min": 27.0, "max": 33.0, "unit": "pg"}},
    "MCHC": {"default": {"min": 32.0, "max": 36.0, "unit": "g/dL"}},
    "RDW": {"default": {"min": 11.5, "max": 14.5, "unit": "%"}},
    "PCV": {
        "male": {"default": {"min": 40.0, "max": 54.0, "unit": "%"}},
        "female": {"default": {"min": 36.0, "max": 48.0, "unit": "%"}},
        "default": {"min": 36.0, "max": 54.0, "unit": "%"},
    },
    "Neutrophils": {"default": {"min": 40.0, "max": 70.0, "unit": "%"}},
    "Lymphocytes": {"default": {"min": 20.0, "max": 40.0, "unit": "%"}},
    "Eosinophils": {"default": {"min": 1.0, "max": 6.0, "unit": "%"}},
    "Monocytes": {"default": {"min": 2.0, "max": 10.0, "unit": "%"}},
    "Basophils": {"default": {"min": 0.0, "max": 2.0, "unit": "%"}},
    "ESR": {
        "male": {
            "adult_18_49": {"min": 0, "max": 15, "unit": "mm/hr"},
            "adult_50_64": {"min": 0, "max": 20, "unit": "mm/hr"},
            "senior_65_plus": {"min": 0, "max": 30, "unit": "mm/hr"},
            "default": {"min": 0, "max": 15, "unit": "mm/hr"},
        },
        "female": {
            "adult_18_49": {"min": 0, "max": 20, "unit": "mm/hr"},
            "adult_50_64": {"min": 0, "max": 30, "unit": "mm/hr"},
            "senior_65_plus": {"min": 0, "max": 40, "unit": "mm/hr"},
            "default": {"min": 0, "max": 20, "unit": "mm/hr"},
        },
        "default": {"min": 0, "max": 20, "unit": "mm/hr"},
    },
    "Glucose": {"default": {"min": 70, "max": 100, "unit": "mg/dL"}},
    "HbA1c": {"default": {"min": 4.0, "max": 5.6, "unit": "%"}},
    "Cholesterol": {"default": {"min": 0, "max": 200, "unit": "mg/dL"}},
    "HDL": {
        "male": {"default": {"min": 40, "max": 60, "unit": "mg/dL"}},
        "female": {"default": {"min": 50, "max": 60, "unit": "mg/dL"}},
        "default": {"min": 40, "max": 60, "unit": "mg/dL"},
    },
    "LDL": {"default": {"min": 0, "max": 100, "unit": "mg/dL"}},
    "Triglycerides": {"default": {"min": 0, "max": 150, "unit": "mg/dL"}},
    "VLDL": {"default": {"min": 2, "max": 30, "unit": "mg/dL"}},
    "Creatinine": {
        "male": {"default": {"min": 0.7, "max": 1.3, "unit": "mg/dL"}},
        "female": {"default": {"min": 0.6, "max": 1.1, "unit": "mg/dL"}},
        "default": {"min": 0.6, "max": 1.3, "unit": "mg/dL"},
    },
    "BUN": {"default": {"min": 7, "max": 20, "unit": "mg/dL"}},
    "Urea": {"default": {"min": 15, "max": 45, "unit": "mg/dL"}},
    "Uric_Acid": {
        "male": {"default": {"min": 3.4, "max": 7.0, "unit": "mg/dL"}},
        "female": {"default": {"min": 2.4, "max": 6.0, "unit": "mg/dL"}},
        "default": {"min": 2.4, "max": 7.0, "unit": "mg/dL"},
    },
    "Sodium": {"default": {"min": 136, "max": 145, "unit": "mEq/L"}},
    "Potassium": {"default": {"min": 3.5, "max": 5.0, "unit": "mEq/L"}},
    "Chloride": {"default": {"min": 98, "max": 106, "unit": "mEq/L"}},
    "Calcium": {"default": {"min": 8.5, "max": 10.5, "unit": "mg/dL"}},
    "Iron": {
        "male": {"default": {"min": 65, "max": 175, "unit": "mcg/dL"}},
        "female": {"default": {"min": 50, "max": 170, "unit": "mcg/dL"}},
        "default": {"min": 50, "max": 175, "unit": "mcg/dL"},
    },
    "Ferritin": {
        "male": {"default": {"min": 20, "max": 500, "unit": "ng/mL"}},
        "female": {"default": {"min": 20, "max": 200, "unit": "ng/mL"}},
        "default": {"min": 20, "max": 500, "unit": "ng/mL"},
    },
    "Vitamin_B12": {"default": {"min": 200, "max": 900, "unit": "pg/mL"}},
    "Vitamin_D": {"default": {"min": 30, "max": 100, "unit": "ng/mL"}},
    "TSH": {"default": {"min": 0.4, "max": 4.0, "unit": "mIU/L"}},
    "T3": {"default": {"min": 80, "max": 200, "unit": "ng/dL"}},
    "T4": {"default": {"min": 5.0, "max": 12.0, "unit": "mcg/dL"}},
    "Bilirubin_Total": {"default": {"min": 0.1, "max": 1.2, "unit": "mg/dL"}},
    "Bilirubin_Direct": {"default": {"min": 0.0, "max": 0.3, "unit": "mg/dL"}},
    "ALT": {"default": {"min": 7, "max": 56, "unit": "U/L"}},
    "AST": {"default": {"min": 10, "max": 40, "unit": "U/L"}},
    "ALP": {"default": {"min": 44, "max": 147, "unit": "U/L"}},
    "GGT": {
        "male": {"default": {"min": 0, "max": 65, "unit": "U/L"}},
        "female": {"default": {"min": 0, "max": 45, "unit": "U/L"}},
        "default": {"min": 0, "max": 65, "unit": "U/L"},
    },
    "Total_Protein": {"default": {"min": 6.0, "max": 8.3, "unit": "g/dL"}},
    "Albumin": {"default": {"min": 3.5, "max": 5.5, "unit": "g/dL"}},
    "Globulin": {"default": {"min": 2.0, "max": 3.5, "unit": "g/dL"}},
    "CRP": {"default": {"min": 0, "max": 3.0, "unit": "mg/L"}},
    "MPV": {"default": {"min": 7.5, "max": 11.5, "unit": "fL"}},
}

# ──────────────────────────────────────────────────────────────
# Name normalization (handles OCR variations)
# ──────────────────────────────────────────────────────────────

PARAMETER_ALIASES: Dict[str, str] = {
    "hemoglobin": "Hemoglobin", "hb": "Hemoglobin", "hgb": "Hemoglobin",
    "rbc": "RBC", "red blood cells": "RBC", "total rbc count": "RBC",
    "wbc": "WBC", "white blood cells": "WBC", "total wbc count": "WBC",
    "platelet": "Platelet", "plt": "Platelet", "platelets": "Platelet",
    "pcv": "PCV", "hematocrit": "PCV", "hct": "PCV",
    "mcv": "MCV", "mean corpuscular volume": "MCV",
    "mch": "MCH", "mean corpuscular hemoglobin": "MCH",
    "mchc": "MCHC",
    "rdw": "RDW", "red cell distribution width": "RDW",
    "mpv": "MPV", "mean platelet volume": "MPV",
    "neutrophils": "Neutrophils", "neutrophil": "Neutrophils",
    "lymphocytes": "Lymphocytes", "lymphocyte": "Lymphocytes",
    "eosinophils": "Eosinophils", "eosinophil": "Eosinophils",
    "monocytes": "Monocytes", "monocyte": "Monocytes",
    "basophils": "Basophils", "basophil": "Basophils",
    "esr": "ESR", "erythrocyte sedimentation rate": "ESR",
    "glucose": "Glucose", "blood sugar": "Glucose", "fasting glucose": "Glucose",
    "hba1c": "HbA1c", "glycated hemoglobin": "HbA1c",
    "cholesterol": "Cholesterol", "total cholesterol": "Cholesterol",
    "hdl": "HDL", "hdl cholesterol": "HDL",
    "ldl": "LDL", "ldl cholesterol": "LDL",
    "triglycerides": "Triglycerides", "tg": "Triglycerides",
    "vldl": "VLDL",
    "creatinine": "Creatinine", "serum creatinine": "Creatinine",
    "bun": "BUN", "blood urea nitrogen": "BUN",
    "urea": "Urea",
    "uric acid": "Uric_Acid", "uric_acid": "Uric_Acid",
    "sodium": "Sodium", "na": "Sodium",
    "potassium": "Potassium", "k": "Potassium",
    "chloride": "Chloride", "cl": "Chloride",
    "calcium": "Calcium", "ca": "Calcium",
    "iron": "Iron", "serum iron": "Iron",
    "ferritin": "Ferritin",
    "vitamin b12": "Vitamin_B12", "vitamin_b12": "Vitamin_B12", "b12": "Vitamin_B12",
    "vitamin d": "Vitamin_D", "vitamin_d": "Vitamin_D", "25-oh vitamin d": "Vitamin_D",
    "tsh": "TSH", "thyroid stimulating hormone": "TSH",
    "t3": "T3", "triiodothyronine": "T3",
    "t4": "T4", "thyroxine": "T4",
    "bilirubin": "Bilirubin_Total", "bilirubin total": "Bilirubin_Total",
    "bilirubin direct": "Bilirubin_Direct",
    "alt": "ALT", "sgpt": "ALT",
    "ast": "AST", "sgot": "AST",
    "alp": "ALP", "alkaline phosphatase": "ALP",
    "ggt": "GGT", "gamma gt": "GGT",
    "total protein": "Total_Protein", "total_protein": "Total_Protein",
    "albumin": "Albumin",
    "globulin": "Globulin",
    "crp": "CRP", "c-reactive protein": "CRP",
}


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def normalize_parameter_name(raw_name: str) -> str:
    """Normalize a raw parameter name to its canonical form."""
    key = raw_name.strip().lower()
    return PARAMETER_ALIASES.get(key, raw_name.strip())


def _get_age_group(age: int) -> str:
    """Map age to age group key."""
    if age <= 12:
        return "child_0_12"
    elif age <= 17:
        return "teen_13_17"
    elif age <= 49:
        return "adult_18_49"
    elif age <= 64:
        return "adult_50_64"
    else:
        return "senior_65_plus"


def get_reference_range(
    parameter_name: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get the reference range for a parameter, adjusted for age and gender.

    Returns:
        Dict with keys: min, max, unit — or None if parameter is unknown.
    """
    canonical = normalize_parameter_name(parameter_name)
    ranges = DYNAMIC_RANGES.get(canonical)

    if ranges is None:
        return None

    # Try gender-specific ranges first
    if gender and gender.lower() in ranges:
        gender_ranges = ranges[gender.lower()]

        # Try age-specific within gender
        if age is not None:
            age_group = _get_age_group(age)
            if age_group in gender_ranges:
                return gender_ranges[age_group]

            # Try broader age keys (e.g., adult_18_64 without the 49 split)
            for key, val in gender_ranges.items():
                if key != "default" and isinstance(val, dict) and "min" in val:
                    # Check if this is a matching broader age range
                    pass

        # Fall back to gender default
        if "default" in gender_ranges:
            return gender_ranges["default"]

    # Try age-only ranges (parameters without gender split like WBC)
    if age is not None:
        age_group = _get_age_group(age)
        if age_group in ranges:
            return ranges[age_group]

        # Try broader keys
        broader_map = {
            "adult_18_49": "adult_18_64",
            "adult_50_64": "adult_18_64",
        }
        broader = broader_map.get(age_group)
        if broader and broader in ranges:
            return ranges[broader]

    # Fall back to default
    if "default" in ranges:
        return ranges["default"]

    return None


def get_all_parameter_names() -> list[str]:
    """Get all known canonical parameter names."""
    return list(DYNAMIC_RANGES.keys())
