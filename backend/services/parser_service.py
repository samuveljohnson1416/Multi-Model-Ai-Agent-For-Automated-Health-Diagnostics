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
# Known CBC reference ranges — used to identify parameters even
# when OCR garbles the parameter name (common with phone photos).
# Format: (low, high) — exclusive match; maps to canonical name + unit.
# These ranges are population-level norms; the matcher tolerates ±1 unit.
# ──────────────────────────────────────────────────────────────
CBC_RANGE_FINGERPRINTS = [
    # (ref_low, ref_high, tolerance, canonical_name, unit)
    (3.80,  6.00,  0.10, "RBC",        "mill/cumm"),
    (11.5,  17.0,  0.20, "Hemoglobin", "g/dL"),
    (35.0,  52.0,  0.30, "PCV",        "%"),
    (76.0, 100.0,  0.50, "MCV",        "fL"),
    (27.0,  34.0,  0.20, "MCH",        "pg"),
    (32.0,  35.0,  0.10, "MCHC",       "g/dL"),
    (11.0,  16.0,  0.10, "RDW",        "%"),
    (37.0,  49.0,  0.20, "RDW-SD",     "fL"),   # RDW-SD shares a different range
    (7.5,   11.0,  0.10, "MPV",        "fL"),
    (0.15,   0.40, 0.01, "PCT",        "%"),
    (11.0,  22.0,  0.10, "PDW",        "fL"),
    (150.0, 400.0, 2.0,  "Platelet",   "/cumm"),
    (3.50,  10.0,  0.10, "WBC",        "/cumm"),
    (40.0,  73.0,  0.50, "Neutrophils", "%"),
    (15.0,  45.0,  0.50, "Lymphocytes", "%"),
    ( 4.0,  12.0,  0.10, "Monocytes",   "%"),
    ( 0.5,   7.0,  0.10, "Eosinophils", "%"),
    ( 0.0,   2.0,  0.05, "Basophils",   "%"),
]

# ──────────────────────────────────────────────────────────────
# Regex patterns for blood report parameters
# Each entry: (regex, canonical_name, default_unit)
# ──────────────────────────────────────────────────────────────

PARAMETER_PATTERNS = [
    # CBC Parameters
    (r"(?:Haemoglobin|Hemoglobin|HB|Hb|Hgb|HGB|HEMOGLOBIN|nos)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Hemoglobin", "g/dL"),
    (r"(?:RBC|Red Blood Cell|Total RBC Count|mec)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "RBC", "mill/cumm"),
    (r"(?:WBC|White Blood Cell|Total WBC Count|Total WBC)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "WBC", "/cumm"),
    (r"(?:Platelet|PLT|Platelets|Platelet Count|mr)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Platelet", "/cumm"),
    (r"(?:PCV|Hematocrit|HCT|Packed Cell Volume|ucr)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "PCV", "%"),
    (r"(?:MCV|Mean Corpuscular Volume)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "MCV", "fL"),
    (r"(?:MCH|Mean Corpuscular Hemoglobin|mcu)(?!C)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "MCH", "pg"),
    (r"(?:MCHC|Mean Corpuscular Hemoglobin Concentration|mene)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "MCHC", "g/dL"),
    (r"(?:RDW[-\s]?(?:CV)?|Red Cell Distribution Width|noe|noe-cy)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "RDW", "%"),
    (r"(?:MPV|Mean Platelet Volume)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "MPV", "fL"),
    (r"(?:PCT|Plateletcrit|ecr)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "PCT", "%"),
    (r"(?:PDW|Platelet Distribution Width)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "PDW", "fL"),
    (r"(?:P[-\s]?LCR|Platelet Large Cell Ratio)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "P-LCR", "%"),
    (r"(?:P[-\s]?LCC|Platelet Large Cell Count)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "P-LCC", "/cumm"),

    # Differential Count — full names and common abbreviations
    (r"(?:Neutrophil|Neutrophils|NEU|NEUT)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Neutrophils", "%"),
    (r"(?:Lymphocyte|Lymphocytes|LYM|LYMPH)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Lymphocytes", "%"),
    (r"(?:Eosinophil|Eosinophils|EOS|EOSINO)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Eosinophils", "%"),
    (r"(?:Monocyte|Monocytes|MON|MONO)\s*(?:\([^)]*\))?\s*[:=,]*\s*(\d+\.?\d*)", "Monocytes", "%"),
    (r"(?:Basophil|Basophils|BAS|BASO)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "Basophils", "%"),
    (r"(?:LIC|Large Immature Cells)\s*(?:\([^)]*\))?\s*[:=]?\s*(\d+\.?\d*)", "LIC", "%"),
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

# Map of known abbreviation → canonical parameter name
# Used by the markdown table parser when regex patterns don't match cell text.
ABBREVIATION_MAP = {
    # CBC
    "hb": "Hemoglobin", "hgb": "Hemoglobin", "hemoglobin": "Hemoglobin",
    "haemoglobin": "Hemoglobin", "nos": "Hemoglobin",
    "rbc": "RBC", "red blood cell": "RBC", "mec": "RBC",
    "wbc": "WBC", "white blood cell": "WBC",
    "plt": "Platelet", "platelet": "Platelet", "platelets": "Platelet",
    "platelet count": "Platelet", "mr": "Platelet",
    "pcv": "PCV", "hematocrit": "PCV", "hct": "PCV", "ucr": "PCV",
    "mcv": "MCV", "mch": "MCH", "mchc": "MCHC", "mene": "MCHC", "mcu": "MCH",
    "rdw": "RDW", "rdw-cv": "RDW", "rdw cv": "RDW",
    "mpv": "MPV", "pct": "PCT", "ecr": "PCT", "pdw": "PDW",
    "p-lcr": "P-LCR", "p lcr": "P-LCR", "plcr": "P-LCR",
    "p-lcc": "P-LCC", "p lcc": "P-LCC", "plcc": "P-LCC",
    # Differential
    "neutrophil": "Neutrophils", "neutrophils": "Neutrophils",
    "neu": "Neutrophils", "neut": "Neutrophils",
    "lymphocyte": "Lymphocytes", "lymphocytes": "Lymphocytes",
    "lym": "Lymphocytes", "lymph": "Lymphocytes",
    "eosinophil": "Eosinophils", "eosinophils": "Eosinophils",
    "eos": "Eosinophils",
    "monocyte": "Monocytes", "monocytes": "Monocytes",
    "mon": "Monocytes", "mono": "Monocytes",
    "basophil": "Basophils", "basophils": "Basophils",
    "bas": "Basophils", "baso": "Basophils",
    "lic": "LIC",
    "esr": "ESR",
    # Metabolic
    "glucose": "Glucose", "fbs": "Glucose", "blood sugar": "Glucose",
    "hba1c": "HbA1c", "a1c": "HbA1c",
    # Lipid
    "cholesterol": "Cholesterol", "total cholesterol": "Cholesterol",
    "hdl": "HDL", "ldl": "LDL",
    "triglycerides": "Triglycerides", "tg": "Triglycerides",
    "vldl": "VLDL",
    # Renal
    "creatinine": "Creatinine", "urea": "Urea",
    "bun": "BUN", "uric acid": "Uric_Acid",
    # Liver
    "bilirubin": "Bilirubin_Total", "total bilirubin": "Bilirubin_Total",
    "bilirubin total": "Bilirubin_Total",
    "bilirubin direct": "Bilirubin_Direct", "direct bilirubin": "Bilirubin_Direct",
    "alt": "ALT", "sgpt": "ALT",
    "ast": "AST", "sgot": "AST",
    "alp": "ALP", "ggt": "GGT",
    "total protein": "Total_Protein", "albumin": "Albumin",
    "globulin": "Globulin",
    # Electrolytes
    "sodium": "Sodium", "na": "Sodium",
    "potassium": "Potassium", "k": "Potassium",
    "chloride": "Chloride", "cl": "Chloride",
    "calcium": "Calcium", "ca": "Calcium",
    # Iron & Vitamins
    "iron": "Iron", "ferritin": "Ferritin",
    "vitamin b12": "Vitamin_B12", "b12": "Vitamin_B12",
    "vitamin d": "Vitamin_D",
    # Thyroid
    "tsh": "TSH", "t3": "T3", "t4": "T4",
    # Inflammatory
    "crp": "CRP", "c-reactive protein": "CRP",
}

# Sanity bounds per parameter (reject clearly wrong OCR reads)
SANITY_BOUNDS = {
    "Hemoglobin": (2.0, 25.0),
    "RBC": (1.0, 10.0),
    "WBC": (1.0, 100000),      # Allow e.g. 5.14 or 5140
    "Platelet": (10, 900000),  # Allow e.g. 182 or 182000
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
    "CRP": (0.0, 500.0),
}


# Differential rows often print "<abs count> <abs range> <percent> <percent range>",
# e.g. "NEU 2.63 1.60-7.00 51.1 40.0-73.0". The regex patterns grab the first number
# (the absolute count), which would be mistaken for a percentage.
_DIFFERENTIAL = {"Neutrophils", "Lymphocytes", "Monocytes", "Eosinophils", "Basophils"}
_NUM = r"\d+\.?\d*"
_RANGE = rf"{_NUM}\s*[-–]\s*{_NUM}"
_ABS_THEN_PERCENT = re.compile(
    rf"{_NUM}\s*[hHlL!|]?\s*{_RANGE}\s*[hHlL!|]?\s*({_NUM})\s*[hHlL!|]?\s*({_RANGE})?"
)


def _percent_column(window: str, value_start: int):
    """(percent value, its range or None) if the row is abs-then-percent, else None."""
    m = _ABS_THEN_PERCENT.match(window, value_start)
    if not m or float(m.group(1)) > 100:
        return None
    rng = re.sub(r"\s*[-–]\s*", " - ", m.group(2)) if m.group(2) else None
    return float(m.group(1)), rng


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
            Dict of parameter_name → {value, unit, reference_range?}
        """
        # Try JSON first
        params = self._try_parse_json(raw_text)
        if params:
            return params

        # Try markdown table extraction (NVIDIA Nemotron OCR output)
        if "|" in raw_text:
            md_params = self._parse_markdown_table(raw_text)
            if md_params:
                logger.info(
                    "Markdown table parser found %d params: %s",
                    len(md_params), list(md_params.keys()),
                )
                # Also run regex on cleaned text to catch anything the table parser missed
                cleaned = self._preprocess_text(raw_text)
                regex_params = self._parse_regex(cleaned)
                # Merge: table results take priority, regex fills gaps
                for name, data in regex_params.items():
                    if name not in md_params:
                        md_params[name] = data
                return md_params

        # Preprocess then regex extract
        cleaned = self._preprocess_text(raw_text)
        params = self._parse_regex(cleaned)
        
        # Fallback: if OCR garbled parameter names, match by known reference ranges
        range_params = self._parse_reference_ranges(cleaned)
        for name, data in range_params.items():
            if name not in params:
                params[name] = data
                
        return params

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

    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Strip markdown artifacts so the regex parser sees clean lines.

        Handles:
          - Literal escaped newlines ("\\n") from the old OCR join bug
          - Markdown table pipes  |  and separator rows  |---|---|
          - Markdown bold / italic  ** *
          - Markdown headers  ## #
          - Unicode superscripts that OCR sometimes returns
        """
        # Defence-in-depth: convert literal \n (two chars) to real newlines
        text = text.replace("\\n", "\n")

        # Drop markdown table separator rows (e.g. |---|---|---| or | :--- |)
        text = re.sub(r"^\|?[\s:]*-{2,}[\s:|\-]*$", "", text, flags=re.MULTILINE)

        # Replace pipe characters with spaces (markdown table cells → space-separated)
        text = text.replace("|", " ")

        # Strip markdown bold / italic markers
        text = text.replace("**", "")
        text = text.replace("*", "")

        # Strip markdown heading markers
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

        # Normalise whitespace: collapse multiple spaces to one
        text = re.sub(r" {2,}", " ", text)

        return text

    def _parse_markdown_table(self, text: str) -> Optional[Dict[str, dict]]:
        """Parse markdown tables produced by NVIDIA Nemotron OCR.

        Nemotron typically returns tables like:
            | RBC | 6.22 | h | 10⁶/μL | 3.80 - 6.00 |
            | HGB | 17.4 | h | g/dL   | 11.5 - 17.0 |

        Strategy: for each row, try to match the first cell against known
        parameter abbreviations, then extract the first numeric cell as the
        value.
        """
        parameters: Dict[str, dict] = {}
        lines = text.split("\n")

        for line in lines:
            # Only process lines that look like table rows
            if "|" not in line:
                continue

            # Skip separator rows  |---|---|---|
            if re.match(r"^\|?[\s:]*-{2,}[\s:|\-]*$", line.strip()):
                continue

            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) < 2:
                continue

            # Try to identify the parameter name from the first cell
            name_cell = cells[0].strip().lower()
            # Remove markdown bold/italic
            name_cell = name_cell.replace("**", "").replace("*", "").strip()

            canonical = ABBREVIATION_MAP.get(name_cell)
            if not canonical:
                # Try without hyphens / spaces for compound names like P-LCR
                canonical = ABBREVIATION_MAP.get(name_cell.replace("-", "").replace(" ", ""))
            if not canonical:
                continue

            # Already found this parameter
            if canonical in parameters:
                continue

            # Find the first numeric value in the remaining cells
            value = None
            unit = None
            ref_range = None
            for cell in cells[1:]:
                # Check if it looks like a reference range (N - N)
                range_match = re.search(r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", cell)
                if range_match:
                    ref_range = f"{range_match.group(1)} - {range_match.group(2)}"
                    continue
                # Check if it looks like a unit
                unit_match = re.match(
                    r"^(g/dL|g/L|mg/dL|mmol/L|mEq/L|U/L|%|fL|pg|/cumm|cells/[µu]L|"
                    r"mm/hr|ng/mL|pg/mL|mcg/dL|mIU/L|ng/dL|[µu]mol/L|mill/cumm|"
                    r"lakhs/[µu]L|10[³⁶⁹]/[µu]L|10\^?[369]/[µu]L)$",
                    cell.strip(), re.IGNORECASE,
                )
                if unit_match:
                    unit = unit_match.group(1)
                    continue
                num_match = re.fullmatch(r"[<>]?\s*(\d+\.?\d*)", cell.strip())
                if num_match and value is None:
                    value = float(num_match.group(1))

            # No numeric cell -> let the regex fallback in parse() fill this parameter
            if value is None:
                continue

            entry: dict = {"value": value, "unit": unit or "N/A"}
            if ref_range:
                entry["reference_range"] = ref_range

            parameters[canonical] = entry
            logger.debug(
                "[MD TABLE] ACCEPTED %s=%.4f %s (ref=%r)",
                canonical, value, entry["unit"], ref_range,
            )

        return parameters if parameters else None

    def _parse_regex(self, text: str) -> Dict[str, dict]:
        """Extract parameters from free text using regex patterns."""
        parameters = {}
        lines = text.split("\n")

        # ── [PARSING CHECKPOINT] Dump every line entering the parser ──
        logger.debug("[PARSING CHECKPOINT] Total lines to parse: %d", len(lines))
        for i, line in enumerate(lines, start=1):
            logger.debug("[PARSING CHECKPOINT] Input line %03d: %r", i, line)

        for line_num, line in enumerate(lines):
            # Create a 2-line window to handle parameters split across lines
            window = line
            if line_num + 1 < len(lines):
                window += " " + lines[line_num + 1]

            line_matched = False
            for pattern, param_name, default_unit in PARAMETER_PATTERNS:
                # Skip if we already found this parameter
                if param_name in parameters:
                    continue

                # Match against the 2-line window
                match = re.search(pattern, window, re.IGNORECASE)
                if match:
                    line_matched = True
                    try:
                        value = float(match.group(1))

                        # Differential row with an absolute-count column first: use the percent
                        percent = _percent_column(window, match.start(1)) if param_name in _DIFFERENTIAL else None
                        if percent:
                            value = percent[0]

                        # Sanity check
                        bounds = SANITY_BOUNDS.get(param_name)
                        if bounds and not (bounds[0] <= value <= bounds[1]):
                            logger.debug(
                                "[PARSING CHECKPOINT] Line %03d: SANITY REJECTED %r "
                                "-> %s=%.4f (bounds: %.2f-%.2f) from line: %r",
                                line_num, match.group(0), param_name, value,
                                bounds[0], bounds[1], window,
                            )
                            continue

                        # Try to extract unit from the window
                        unit = "%" if percent else (self._extract_unit(window, match.end()) or default_unit)

                        # Try to extract reference range from the window. For a percent
                        # column with no adjacent range, leave it empty so the built-in
                        # percent range is used rather than the absolute-count range.
                        # Only look at the parameter's own row: the 2-line window would otherwise
                        # hand it the previous/next row's range when its own row has none.
                        row_end = len(line) if match.start(1) < len(line) else len(window)
                        ref_range = percent[1] if percent else self._extract_reference_range(
                            window[match.end():row_end]
                        )

                        parameters[param_name] = {
                            "value": value,
                            "unit": unit,
                        }
                        if ref_range:
                            parameters[param_name]["reference_range"] = ref_range

                        logger.debug(
                            "[PARSING CHECKPOINT] Line %03d: ACCEPTED %s=%.4f %s "
                            "(ref_range=%r) from line: %r",
                            line_num, param_name, value, unit, ref_range, window,
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
        # Count units printed as a power of ten ("10^3/uL"): the numbers are scaled, so the
        # unit must be kept for the validator to convert (default units would be wrong).
        scaled = re.match(rf"[x×]?\s*10\s*[\^*]?\s*([36³⁶])\s*/\s*[µuμ]?\s*L", remaining, re.IGNORECASE)
        if scaled:
            return "×10³/µL" if scaled.group(1) in "3³" else "×10⁶/µL"
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

    def _parse_reference_ranges(self, text: str) -> Dict[str, dict]:
        """
        Extract parameters by looking for characteristic reference ranges.
        Useful when OCR garbles the parameter name (e.g. "RBC" -> "mec")
        but preserves the numbers.
        """
        parameters = {}
        lines = text.split("\n")

        for line in lines:
            # Look for a reference range pattern: num1 - num2
            ref_match = re.search(r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)", line)
            if not ref_match:
                continue

            ref_low = float(ref_match.group(1))
            ref_high = float(ref_match.group(2))

            # Match against known fingerprints
            matched_param = None
            matched_unit = None
            
            for fp_low, fp_high, tol, canonical, default_unit in CBC_RANGE_FINGERPRINTS:
                if abs(ref_low - fp_low) <= tol and abs(ref_high - fp_high) <= tol:
                    matched_param = canonical
                    matched_unit = default_unit
                    break

            if not matched_param:
                continue

            if matched_param in parameters:
                continue

            # Now find the actual value on this line
            # It's usually the first number that ISN'T part of the reference range
            # We strip the reference range out first
            line_no_ref = line[:ref_match.start()] + line[ref_match.end():]
            
            # Find all numbers
            num_matches = re.findall(r"(\d+\.?\d*)", line_no_ref)
            for num_str in num_matches:
                try:
                    val = float(num_str)
                    
                    # Sanity check
                    bounds = SANITY_BOUNDS.get(matched_param)
                    if bounds and not (bounds[0] <= val <= bounds[1]):
                        continue

                    # We found a valid value!
                    unit = self._extract_unit(line, 0) or matched_unit
                    parameters[matched_param] = {
                        "value": val,
                        "unit": unit,
                        "reference_range": f"{ref_low} - {ref_high}"
                    }
                    
                    logger.debug(
                        "[FINGERPRINT MATCH] OCR garbled name but found %s=%.4f (ref: %s-%s) from: %r",
                        matched_param, val, ref_low, ref_high, line
                    )
                    break # Found the value for this line
                except ValueError:
                    continue

        return parameters
