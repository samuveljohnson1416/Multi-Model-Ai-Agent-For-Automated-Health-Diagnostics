"""
Parser service — extracts blood parameters from OCR text.

Merges logic from src/core/parser.py and src/core/enhanced_blood_parser.py.
Handles both structured (JSON) and unstructured (OCR text) inputs.
"""

import re
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Regex patterns for blood report parameters
# Each entry: (regex, canonical_name, default_unit)
# ──────────────────────────────────────────────────────────────

PARAMETER_PATTERNS = [
    # CBC Parameters
    (r"(?:Haemoglobin|Hemoglobin|HB|Hb|Hgb|HGB|HEMOGLOBIN)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Hemoglobin", "g/dL"),
    (r"(?:RBC|Red Blood Cell|Total RBC Count)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "RBC", "mill/cumm"),
    (r"(?:WBC|White Blood Cell|Total WBC Count|Total WBC)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "WBC", "/cumm"),
    (r"(?:Platelet|PLT|Platelets|Platelet Count)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Platelet", "/cumm"),
    (r"(?:PCV|Hematocrit|HCT|Packed Cell Volume)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "PCV", "%"),
    (r"(?:MCV|Mean Corpuscular Volume)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "MCV", "fL"),
    (r"(?:MCH|Mean Corpuscular Hemoglobin)(?!C)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "MCH", "pg"),
    (r"(?:MCHC|Mean Corpuscular Hemoglobin Concentration)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "MCHC", "g/dL"),
    (r"(?:RDW|Red Cell Distribution Width)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "RDW", "%"),
    (r"(?:MPV|Mean Platelet Volume)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "MPV", "fL"),

    # Differential Count
    (r"(?:Neutrophil|Neutrophils)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Neutrophils", "%"),
    (r"(?:Lymphocyte|Lymphocytes)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Lymphocytes", "%"),
    (r"(?:Eosinophil|Eosinophils)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Eosinophils", "%"),
    (r"(?:Monocyte|Monocytes)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Monocytes", "%"),
    (r"(?:Basophil|Basophils)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Basophils", "%"),
    (r"(?:ESR|Erythrocyte Sedimentation Rate)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "ESR", "mm/hr"),

    # Metabolic Panel
    (r"(?:Glucose|Blood Sugar|Fasting Glucose|FBS)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Glucose", "mg/dL"),
    (r"(?:HbA1c|Glycated Hemoglobin|A1C)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "HbA1c", "%"),

    # Lipid Panel
    (r"(?:Total Cholesterol|Cholesterol|CHOL)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Cholesterol", "mg/dL"),
    (r"(?:HDL|HDL Cholesterol|HDL-C)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "HDL", "mg/dL"),
    (r"(?:LDL|LDL Cholesterol|LDL-C)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "LDL", "mg/dL"),
    (r"(?:Triglycerides|TG|Triglyceride)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Triglycerides", "mg/dL"),
    (r"(?:VLDL)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "VLDL", "mg/dL"),

    # Renal Panel
    (r"(?:Creatinine|CREAT|Serum Creatinine)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Creatinine", "mg/dL"),
    (r"(?:BUN|Blood Urea Nitrogen)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "BUN", "mg/dL"),
    (r"(?:Urea)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Urea", "mg/dL"),
    (r"(?:Uric Acid)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Uric_Acid", "mg/dL"),

    # Liver Panel
    (r"(?:Bilirubin Total|Total Bilirubin|Bilirubin)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Bilirubin_Total", "mg/dL"),
    (r"(?:Bilirubin Direct|Direct Bilirubin)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Bilirubin_Direct", "mg/dL"),
    (r"(?:ALT|SGPT|Alanine Aminotransferase)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "ALT", "U/L"),
    (r"(?:AST|SGOT|Aspartate Aminotransferase)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "AST", "U/L"),
    (r"(?:ALP|Alkaline Phosphatase)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "ALP", "U/L"),
    (r"(?:GGT|Gamma GT)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "GGT", "U/L"),
    (r"(?:Total Protein)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Total_Protein", "g/dL"),
    (r"(?:Albumin)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Albumin", "g/dL"),
    (r"(?:Globulin)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Globulin", "g/dL"),

    # Electrolytes
    (r"(?:Sodium|Na)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Sodium", "mEq/L"),
    (r"(?:Potassium|K)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Potassium", "mEq/L"),
    (r"(?:Chloride|Cl)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Chloride", "mEq/L"),
    (r"(?:Calcium|Ca)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Calcium", "mg/dL"),

    # Iron & Vitamins
    (r"(?:Iron|Serum Iron)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Iron", "mcg/dL"),
    (r"(?:Ferritin)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Ferritin", "ng/mL"),
    (r"(?:Vitamin B12|B12)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Vitamin_B12", "pg/mL"),
    (r"(?:Vitamin D|25-OH Vitamin D)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Vitamin_D", "ng/mL"),

    # Thyroid
    (r"(?:TSH|Thyroid Stimulating Hormone)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "TSH", "mIU/L"),
    (r"(?:T3|Triiodothyronine)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "T3", "ng/dL"),
    (r"(?:T4|Thyroxine)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "T4", "mcg/dL"),

    # Inflammatory Markers
    (r"(?:CRP|C-Reactive Protein)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "CRP", "mg/L"),
]

# Sanity bounds per parameter (reject clearly wrong OCR reads)
SANITY_BOUNDS = {
    "Hemoglobin": (2.0, 25.0),
    "RBC": (1.0, 10.0),
    "WBC": (500, 100000),
    "Platelet": (10000, 900000),
    "PCV": (10.0, 70.0),
    "MCV": (50.0, 150.0),
    "MCH": (15.0, 45.0),
    "MCHC": (25.0, 40.0),
    "RDW": (8.0, 30.0),
    "Glucose": (20, 700),
    "HbA1c": (3.0, 18.0),
    "Cholesterol": (50, 500),
    "Creatinine": (0.1, 20.0),
    "TSH": (0.01, 100.0),
}


class ParserService:
    """
    Parses blood report text into structured parameter data.
    Handles JSON input, CSV-converted text, and raw OCR text.
    """

    def parse(self, raw_text: str) -> Dict[str, dict]:
        """
        Parse raw text into blood parameters.

        Args:
            raw_text: OCR text, JSON string, or CSV-converted text

        Returns:
            Dict of parameter_name → {value, unit, reference_range?, raw_text?}
        """
        # Try JSON first
        params = self._try_parse_json(raw_text)
        if params:
            return params

        # Fall back to regex extraction
        return self._parse_regex(raw_text)

    def _try_parse_json(self, text: str) -> Optional[Dict[str, dict]]:
        """Try to parse text as JSON blood report data."""
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

        parameters = {}

        # Handle {"parameters": [{name, value, unit}, ...]}
        if isinstance(data, dict) and "parameters" in data:
            for param in data["parameters"]:
                name = param.get("name", "Unknown")
                try:
                    value = float(param.get("value", 0))
                    parameters[name] = {
                        "value": value,
                        "unit": param.get("unit", "N/A"),
                        "reference_range": param.get("reference_range", "N/A"),
                    }
                except (ValueError, TypeError):
                    continue
            return parameters if parameters else None

        # Handle {param_name: {value: x, unit: y}, ...}
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and "value" in value:
                    try:
                        parameters[key] = {
                            "value": float(value["value"]),
                            "unit": value.get("unit", "N/A"),
                            "reference_range": value.get("reference_range", "N/A"),
                        }
                    except (ValueError, TypeError):
                        continue
                elif isinstance(value, (int, float)):
                    parameters[key] = {"value": float(value), "unit": "N/A"}

            return parameters if parameters else None

        return None

    def _parse_regex(self, text: str) -> Dict[str, dict]:
        """Extract parameters from free text using regex patterns."""
        parameters = {}
        lines = text.split("\n")

        # ── [PARSING CHECKPOINT] Dump every line entering the parser ──
        logger.debug("[PARSING CHECKPOINT] Total lines to parse: %d", len(lines))
        for i, line in enumerate(lines, start=1):
            logger.debug("[PARSING CHECKPOINT] Input line %03d: %r", i, line)

        for line_num, line in enumerate(lines, start=1):
            line_matched = False
            for pattern, param_name, default_unit in PARAMETER_PATTERNS:
                # Skip if we already found this parameter
                if param_name in parameters:
                    continue

                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    line_matched = True
                    try:
                        value = float(match.group(1))

                        # Sanity check
                        bounds = SANITY_BOUNDS.get(param_name)
                        if bounds and not (bounds[0] <= value <= bounds[1]):
                            logger.debug(
                                "[PARSING CHECKPOINT] Line %03d: SANITY REJECTED %r "
                                "-> %s=%.4f (bounds: %.2f-%.2f) from line: %r",
                                line_num, match.group(0), param_name, value,
                                bounds[0], bounds[1], line,
                            )
                            continue

                        # Try to extract unit from the line
                        unit = self._extract_unit(line, match.end()) or default_unit

                        # Try to extract reference range from the line
                        ref_range = self._extract_reference_range(line)

                        parameters[param_name] = {
                            "value": value,
                            "unit": unit,
                        }
                        if ref_range:
                            parameters[param_name]["reference_range"] = ref_range

                        logger.debug(
                            "[PARSING CHECKPOINT] Line %03d: ACCEPTED %s=%.4f %s "
                            "(ref_range=%r) from line: %r",
                            line_num, param_name, value, unit, ref_range, line,
                        )

                    except ValueError:
                        continue

            if not line_matched and line.strip():
                logger.debug(
                    "[PARSING CHECKPOINT] Line %03d: NO PATTERN MATCH for line: %r",
                    line_num, line,
                )

        # ── [PARSING CHECKPOINT] Final result summary ──
        logger.debug(
            "[PARSING CHECKPOINT] Parsing complete. Found %d parameters: %s",
            len(parameters), list(parameters.keys()),
        )
        return parameters

    def _extract_unit(self, line: str, value_end: int) -> Optional[str]:
        """Try to extract unit from text after the value."""
        remaining = line[value_end:].strip()
        unit_pattern = r"^\s*(g/dL|g/L|mg/dL|mmol/L|mEq/L|U/L|%|fL|pg|/cumm|cells/µL|mm/hr|ng/mL|pg/mL|mcg/dL|mIU/L|ng/dL|µmol/L|mill/cumm|lakhs/µL)"
        match = re.search(unit_pattern, remaining, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_reference_range(self, line: str) -> Optional[str]:
        """Try to extract reference range from the line."""
        # Pattern: number - number (possibly with units)
        ref_pattern = r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)"
        matches = list(re.finditer(ref_pattern, line))
        # Usually the reference range is the last range on the line
        if matches:
            last = matches[-1]
            return f"{last.group(1)} - {last.group(2)}"
        return None
