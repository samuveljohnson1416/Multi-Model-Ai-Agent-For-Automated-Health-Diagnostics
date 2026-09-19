"""
Layouts seen in real lab reports (sample reports from public lab templates). Each case is a
line, or a few lines, of extracted text that used to be misread, dropped, or given the wrong
scale. No network.
"""
import json

from backend.services.parser_service import ParserService
from backend.services.validator_service import ValidatorService


def analyze(text: str, **kw) -> dict:
    """Parse and validate text; returns {name: BloodParameter}."""
    raw = ParserService().parse(text)
    return {p.name: p for p in ValidatorService().validate(raw, **kw)}


def test_watermark_line_between_name_and_value():
    # "Drlogy.com" is a stamp printed over the row; it used to hide the value
    p = analyze("Total WBC count\nDrlogy.com\n25000 High 4000 - 11000 cumm")["WBC"]
    assert p.value == 25000 and p.status.value in ("HIGH", "CRITICAL")


def test_flag_glued_to_value_and_cmm_unit():
    params = analyze("WBC Count H10570 /cmm 4000 - 10000\nRBC Count 4.79 million/cmm 4.5 - 5.5")
    assert params["WBC"].value == 10570 and params["WBC"].status.value == "HIGH"
    assert params["RBC"].value == 4.79 and params["RBC"].status.value == "NORMAL"


def test_lakhs_are_converted_not_flagged_critical():
    # 3.5 lakhs/cumm = 350,000, which is normal; it used to be read as a count of 3.5
    p = analyze("PLATELET COUNT 3.5 lakhs/cumm 1.5 - 4.1")["Platelet"]
    assert p.value == 350000 and p.status.value == "NORMAL"


def test_leukocyte_name_and_thousands_separator():
    p = analyze("TOTAL LEUKOCYTE COUNT 5,100 cumm 4,800 - 10,800")["WBC"]
    assert p.value == 5100 and p.status.value == "NORMAL"


def test_flag_letter_between_name_and_value():
    p = analyze("MEAN CELL HAEMOGLOBIN CON, MCHC H 35.7 % 31.5 - 34.5")["MCHC"]
    assert p.value == 35.7 and p.status.value == "HIGH"


def test_below_detection_value_is_kept():
    p = analyze("Vitamin B12 L < 148 pg/mL 187 - 833")["Vitamin_B12"]
    assert p.value == 148 and p.status.value == "LOW" and p.unit == "pg/mL"


def test_sample_qualifier_after_name():
    assert analyze("Creatinine, Serum 0.83 mg/dL 0.66 - 1.25")["Creatinine"].value == 0.83


def test_printed_range_in_another_unit_than_the_builtin_one():
    # T3 1.01 ng/mL with printed range 0.58-1.59 is normal; the built-in range is per dL
    p = analyze("T3 - Triiodothyronine 1.01 ng/mL 0.58 - 1.59")["T3"]
    assert p.status.value == "NORMAL" and (p.reference_min, p.reference_max) == (0.58, 1.59)


def test_bracketed_abbreviation_and_annotation_letter():
    params = analyze(
        "Mean Cell Volume (MCV) 109.6 H fL 80-100\n"
        "Hemoglobin (HB/Hgb)) M 6.5 L** g/dL 14.0-18.0\n"
        "White Blood Cell (WBC) 6.9 K/mcL 4.8-10.8"
    )
    assert params["MCV"].value == 109.6 and params["MCV"].status.value == "HIGH"
    assert params["Hemoglobin"].value == 6.5
    assert params["WBC"].value == 6900
    assert "Chloride" not in params  # "cL" inside "mcL" is not a chloride result


def test_json_with_a_results_envelope():
    doc = {
        "patient_info": {"age": 28},
        "test_results": {
            "hemoglobin": {"value": 12.5, "unit": "g/dL", "reference_range": "13.0-17.0"},
            "fasting_glucose": {"value": 96, "unit": "mg/dL", "reference_range": "70-99"},
        },
    }
    params = analyze(json.dumps(doc))
    assert params["Hemoglobin"].status.value == "LOW"
    assert params["Glucose"].status.value == "NORMAL"


def test_k_suffix_in_a_printed_range():
    p = analyze("Platelet Count 280000 cumm 150k-410k")["Platelet"]
    assert (p.reference_min, p.reference_max) == (150000, 410000) and p.unit == "/cumm"
