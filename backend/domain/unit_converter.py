"""
Unit conversion system for blood parameters.

Ported from src/core/unit_converter.py.
Pure domain logic — no I/O, no API calls.
"""

from typing import Optional, Tuple

# ──────────────────────────────────────────────────────────────
# Standard units for each parameter
# ──────────────────────────────────────────────────────────────

STANDARD_UNITS = {
    "Hemoglobin": "g/dL",
    "RBC": "mill/cumm",
    "WBC": "/cumm",
    "Platelet": "/cumm",
    "PCV": "%",
    "MCV": "fL",
    "MCH": "pg",
    "MCHC": "g/dL",
    "RDW": "%",
    "MPV": "fL",
    "ESR": "mm/hr",
    "Glucose": "mg/dL",
    "HbA1c": "%",
    "Cholesterol": "mg/dL",
    "HDL": "mg/dL",
    "LDL": "mg/dL",
    "Triglycerides": "mg/dL",
    "VLDL": "mg/dL",
    "Creatinine": "mg/dL",
    "BUN": "mg/dL",
    "Urea": "mg/dL",
    "Uric_Acid": "mg/dL",
    "Sodium": "mEq/L",
    "Potassium": "mEq/L",
    "Chloride": "mEq/L",
    "Calcium": "mg/dL",
    "Iron": "mcg/dL",
    "Ferritin": "ng/mL",
    "Vitamin_B12": "pg/mL",
    "Vitamin_D": "ng/mL",
    "TSH": "mIU/L",
    "T3": "ng/dL",
    "T4": "mcg/dL",
    "Bilirubin_Total": "mg/dL",
    "Bilirubin_Direct": "mg/dL",
    "ALT": "U/L",
    "AST": "U/L",
    "ALP": "U/L",
    "GGT": "U/L",
    "Total_Protein": "g/dL",
    "Albumin": "g/dL",
    "Globulin": "g/dL",
    "CRP": "mg/L",
}

# ──────────────────────────────────────────────────────────────
# Conversion factors: (from_unit, to_unit) → multiplier
# value_in_to_unit = value_in_from_unit * factor
# ──────────────────────────────────────────────────────────────

CONVERSIONS: dict[tuple[str, str], float] = {
    # Hemoglobin
    ("g/dL", "g/L"): 10.0,
    ("g/L", "g/dL"): 0.1,
    ("g/dL", "mmol/L"): 0.6206,
    ("mmol/L", "g/dL"): 1.611,
    # Glucose
    ("mg/dL", "mmol/L"): 0.0555,
    ("mmol/L", "mg/dL"): 18.018,
    # Cholesterol (total, HDL, LDL)
    ("mg/dL", "mmol/L_chol"): 0.02586,
    ("mmol/L_chol", "mg/dL"): 38.67,
    # Triglycerides
    ("mg/dL", "mmol/L_tg"): 0.01129,
    ("mmol/L_tg", "mg/dL"): 88.57,
    # Creatinine
    ("mg/dL", "µmol/L"): 88.4,
    ("µmol/L", "mg/dL"): 0.01131,
    # Urea / BUN
    ("mg/dL", "mmol/L_urea"): 0.1665,
    ("mmol/L_urea", "mg/dL"): 6.006,
    # Calcium
    ("mg/dL", "mmol/L_ca"): 0.2495,
    ("mmol/L_ca", "mg/dL"): 4.008,
    # WBC
    ("/cumm", "×10³/µL"): 0.001,
    ("×10³/µL", "/cumm"): 1000,
    ("/cumm", "cells/µL"): 1.0,
    ("cells/µL", "/cumm"): 1.0,
    # Platelet
    ("/cumm", "×10³/µL_plt"): 0.001,
    ("×10³/µL_plt", "/cumm"): 1000,
    ("/cumm", "lakhs/µL"): 0.00001,
    ("lakhs/µL", "/cumm"): 100000,
    # RBC
    ("mill/cumm", "×10⁶/µL"): 1.0,
    ("×10⁶/µL", "mill/cumm"): 1.0,
    ("mill/cumm", "million/µL"): 1.0,
    ("million/µL", "mill/cumm"): 1.0,
    # Iron
    ("mcg/dL", "µmol/L_fe"): 0.1791,
    ("µmol/L_fe", "mcg/dL"): 5.583,
    # Bilirubin
    ("mg/dL", "µmol/L_bili"): 17.1,
    ("µmol/L_bili", "mg/dL"): 0.05848,
    # TSH
    ("mIU/L", "µIU/mL"): 1.0,
    ("µIU/mL", "mIU/L"): 1.0,
}


# ──────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────


def get_standard_unit(parameter_name: str) -> Optional[str]:
    """Get the standard unit for a parameter."""
    return STANDARD_UNITS.get(parameter_name)


def convert_unit(
    value: float,
    from_unit: str,
    to_unit: str,
) -> Optional[float]:
    """
    Convert a value between units.

    Returns:
        Converted value, or None if conversion is not supported.
    """
    # Same unit — no conversion needed
    from_clean = from_unit.strip().lower()
    to_clean = to_unit.strip().lower()

    if from_clean == to_clean:
        return value

    # Look up conversion factor
    factor = CONVERSIONS.get((from_unit, to_unit))
    if factor is not None:
        return round(value * factor, 4)

    # Try reverse conversion
    reverse_factor = CONVERSIONS.get((to_unit, from_unit))
    if reverse_factor is not None and reverse_factor != 0:
        return round(value / reverse_factor, 4)

    return None


def convert_to_standard(
    parameter_name: str,
    value: float,
    current_unit: str,
) -> Tuple[float, str]:
    """
    Convert a parameter value to its standard unit.

    Returns:
        Tuple of (converted_value, standard_unit).
        If conversion is not possible, returns the original value and unit.
    """
    standard_unit = get_standard_unit(parameter_name)
    if standard_unit is None:
        return value, current_unit

    if current_unit.strip() == standard_unit:
        return value, standard_unit

    converted = convert_unit(value, current_unit, standard_unit)
    if converted is not None:
        return converted, standard_unit

    return value, current_unit
