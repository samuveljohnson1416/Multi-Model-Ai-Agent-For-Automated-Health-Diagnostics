"""
Test suite for the v3 backend.
Uses pytest. Tests are organized by layer:
  1. Domain (pure functions, no I/O)
  2. Services (parser, validator)
  3. LLM provider layer + agent framework (v3.0, no network)
  4. API (FastAPI endpoints via TestClient)
"""

# pyrefly: ignore [missing-import]
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

# ── Domain Tests ──────────────────────────────────────────────


class TestReferenceRanges:
    """Tests for backend.domain.reference_ranges"""

    def test_normalize_known_alias(self):
        from backend.domain.reference_ranges import normalize_parameter_name
        assert normalize_parameter_name("hb") == "Hemoglobin"
        assert normalize_parameter_name("HB") == "Hemoglobin"
        assert normalize_parameter_name("hemoglobin") == "Hemoglobin"

    def test_normalize_unknown_preserves_original(self):
        from backend.domain.reference_ranges import normalize_parameter_name
        assert normalize_parameter_name("SomeUnknownParam") == "SomeUnknownParam"

    def test_normalize_wbc_aliases(self):
        from backend.domain.reference_ranges import normalize_parameter_name
        assert normalize_parameter_name("wbc") == "WBC"
        assert normalize_parameter_name("white blood cells") == "WBC"
        assert normalize_parameter_name("total wbc count") == "WBC"

    def test_get_default_range(self):
        from backend.domain.reference_ranges import get_reference_range
        ref = get_reference_range("Hemoglobin")
        assert ref is not None
        assert "min" in ref
        assert "max" in ref
        assert ref["min"] == 12.0
        assert ref["max"] == 17.0

    def test_get_gender_adjusted_range(self):
        from backend.domain.reference_ranges import get_reference_range
        male_ref = get_reference_range("Hemoglobin", age=30, gender="male")
        female_ref = get_reference_range("Hemoglobin", age=30, gender="female")
        assert male_ref is not None
        assert female_ref is not None
        assert male_ref["min"] > female_ref["min"]  # Males have higher Hb range

    def test_get_age_adjusted_range(self):
        from backend.domain.reference_ranges import get_reference_range
        child_ref = get_reference_range("WBC", age=5)
        adult_ref = get_reference_range("WBC", age=30)
        assert child_ref is not None
        assert adult_ref is not None
        assert child_ref["max"] > adult_ref["max"]  # Children have higher WBC ceiling

    def test_unknown_parameter_returns_none(self):
        from backend.domain.reference_ranges import get_reference_range
        assert get_reference_range("NonExistentParameter") is None

    def test_get_all_parameter_names(self):
        from backend.domain.reference_ranges import get_all_parameter_names
        names = get_all_parameter_names()
        assert len(names) > 30
        assert "Hemoglobin" in names
        assert "Glucose" in names


class TestUnitConverter:
    """Tests for backend.domain.unit_converter"""

    def test_same_unit_no_conversion(self):
        from backend.domain.unit_converter import convert_unit
        assert convert_unit(14.0, "g/dL", "g/dL") == 14.0

    def test_hemoglobin_gdl_to_gl(self):
        from backend.domain.unit_converter import convert_unit
        result = convert_unit(14.0, "g/dL", "g/L")
        assert result is not None
        assert abs(result - 140.0) < 0.1

    def test_glucose_mgdl_to_mmol(self):
        from backend.domain.unit_converter import convert_unit
        result = convert_unit(100.0, "mg/dL", "mmol/L")
        assert result is not None
        assert abs(result - 5.55) < 0.1

    def test_unsupported_conversion_returns_none(self):
        from backend.domain.unit_converter import convert_unit
        assert convert_unit(10, "bushels", "parsecs") is None

    def test_convert_to_standard(self):
        from backend.domain.unit_converter import convert_to_standard
        value, unit = convert_to_standard("Hemoglobin", 140.0, "g/L")
        assert unit == "g/dL"
        assert abs(value - 14.0) < 0.1

    def test_get_standard_unit(self):
        from backend.domain.unit_converter import get_standard_unit
        assert get_standard_unit("Hemoglobin") == "g/dL"
        assert get_standard_unit("Glucose") == "mg/dL"
        assert get_standard_unit("NonExistent") is None


class TestRiskCalculator:
    """Tests for backend.domain.risk_calculator"""

    def test_framingham_male_low_risk(self):
        from backend.domain.risk_calculator import calculate_framingham_risk
        result = calculate_framingham_risk(
            age=35, gender="male",
            total_cholesterol=180, hdl=55, is_smoker=False
        )
        assert "risk_percent" in result
        assert result["risk_category"] == "low"

    def test_framingham_high_risk(self):
        from backend.domain.risk_calculator import calculate_framingham_risk
        result = calculate_framingham_risk(
            age=65, gender="male",
            total_cholesterol=280, hdl=30, is_smoker=True
        )
        assert result["risk_percent"] > 10

    def test_framingham_age_out_of_range(self):
        from backend.domain.risk_calculator import calculate_framingham_risk
        result = calculate_framingham_risk(age=15, gender="male")
        assert "error" in result

    def test_lipid_ratios(self):
        from backend.domain.risk_calculator import calculate_lipid_ratios
        result = calculate_lipid_ratios(
            total_cholesterol=200, hdl=50, ldl=120, triglycerides=150
        )
        assert "tc_hdl_ratio" in result
        assert result["tc_hdl_ratio"]["value"] == 4.0

    def test_basic_risk_all_normal(self):
        from backend.domain.risk_calculator import calculate_basic_risk
        params = {"Hemoglobin": {"status": "NORMAL", "value": 14.0}}
        result = calculate_basic_risk(params)
        assert result["risk_level"] == "low"
        assert result["risk_score"] == 0.0

    def test_basic_risk_with_abnormal(self):
        from backend.domain.risk_calculator import calculate_basic_risk
        params = {
            "Hemoglobin": {"status": "LOW", "value": 10.0},
            "WBC": {"status": "HIGH", "value": 15000},
        }
        result = calculate_basic_risk(params)
        assert result["risk_score"] > 0
        assert len(result["risk_factors"]) == 2


class TestReportInterpreter:
    """Tests for backend.domain.report_interpreter"""

    def test_compute_deviation_within_range(self):
        from backend.domain.report_interpreter import compute_deviation
        dev, severity = compute_deviation(14.0, 12.0, 17.0)
        assert dev == 0.0
        assert severity == "Normal"

    def test_compute_deviation_low(self):
        from backend.domain.report_interpreter import compute_deviation
        dev, severity = compute_deviation(10.0, 12.0, 17.0)
        assert dev > 0
        assert severity in ("Mild", "Moderate", "Severe")

    def test_interpret_all_normal(self):
        from backend.domain.report_interpreter import interpret_parameters
        from backend.models.blood_parameter import BloodParameter, ParameterStatus
        params = [
            BloodParameter(name="Hemoglobin", value=14.0, unit="g/dL", status=ParameterStatus.NORMAL),
            BloodParameter(name="RBC", value=5.0, unit="mill/cumm", status=ParameterStatus.NORMAL),
        ]
        result = interpret_parameters(params)
        assert result["summary"]["normal"] == 2
        assert result["summary"]["abnormal_count"] == 0
        assert len(result["abnormal_parameters"]) == 0

    def test_interpret_with_abnormal(self):
        from backend.domain.report_interpreter import interpret_parameters
        from backend.models.blood_parameter import BloodParameter, ParameterStatus
        params = [
            BloodParameter(name="Hemoglobin", value=10.0, unit="g/dL", status=ParameterStatus.LOW, severity="Moderate"),
            BloodParameter(name="WBC", value=5000, unit="/cumm", status=ParameterStatus.NORMAL),
        ]
        result = interpret_parameters(params)
        assert result["summary"]["low"] == 1
        assert result["summary"]["normal"] == 1
        assert len(result["abnormal_parameters"]) == 1


# ── Service Tests ─────────────────────────────────────────────


class TestParserService:
    """Tests for backend.services.parser_service"""

    def test_parse_json_parameters(self):
        from backend.services.parser_service import ParserService
        parser = ParserService()
        json_input = json.dumps({
            "parameters": [
                {"name": "Hemoglobin", "value": 14.5, "unit": "g/dL"},
                {"name": "RBC", "value": 5.2, "unit": "mill/cumm"},
            ]
        })
        result = parser.parse(json_input)
        assert "Hemoglobin" in result
        assert result["Hemoglobin"]["value"] == 14.5

    def test_parse_json_flat_dict(self):
        from backend.services.parser_service import ParserService
        parser = ParserService()
        json_input = json.dumps({
            "Hemoglobin": {"value": 14.0, "unit": "g/dL"},
            "RBC": {"value": 5.0, "unit": "mill/cumm"},
        })
        result = parser.parse(json_input)
        assert len(result) == 2

    def test_parse_ocr_text(self):
        from backend.services.parser_service import ParserService
        parser = ParserService()
        ocr_text = """
        Complete Blood Count Report
        Hemoglobin: 14.5 g/dL
        RBC: 5.2 mill/cumm
        WBC: 7500 /cumm
        Platelet: 250000 /cumm
        """
        result = parser.parse(ocr_text)
        assert "Hemoglobin" in result
        assert result["Hemoglobin"]["value"] == 14.5
        assert "WBC" in result
        assert result["WBC"]["value"] == 7500

    def test_parse_rejects_insane_values(self):
        from backend.services.parser_service import ParserService
        parser = ParserService()
        ocr_text = "Hemoglobin: 999.0 g/dL"  # Clearly wrong
        result = parser.parse(ocr_text)
        assert "Hemoglobin" not in result  # Should be rejected by sanity bounds

    def test_parse_empty_text(self):
        from backend.services.parser_service import ParserService
        parser = ParserService()
        result = parser.parse("")
        assert result == {}


class TestValidatorService:
    """Tests for backend.services.validator_service"""

    def test_validate_normal_hemoglobin(self):
        from backend.services.validator_service import ValidatorService
        validator = ValidatorService()
        raw = {"Hemoglobin": {"value": 14.0, "unit": "g/dL"}}
        result = validator.validate(raw)
        assert len(result) == 1
        assert result[0].status.value == "NORMAL"

    def test_validate_low_hemoglobin(self):
        from backend.services.validator_service import ValidatorService
        validator = ValidatorService()
        raw = {"Hemoglobin": {"value": 8.0, "unit": "g/dL"}}
        result = validator.validate(raw, age=30, gender="male")
        assert result[0].status.value in ("LOW", "CRITICAL")

    def test_validate_with_age_gender(self):
        from backend.services.validator_service import ValidatorService
        validator = ValidatorService()
        raw = {"Hemoglobin": {"value": 13.0, "unit": "g/dL"}}
        # 13.0 is normal for female but low for male adult
        male_result = validator.validate(raw, age=30, gender="male")
        female_result = validator.validate(raw, age=30, gender="female")
        assert male_result[0].status.value == "LOW"
        assert female_result[0].status.value == "NORMAL"

    def test_validate_unknown_parameter(self):
        from backend.services.validator_service import ValidatorService
        validator = ValidatorService()
        raw = {"SomeUnknown": {"value": 42.0, "unit": "U/L"}}
        result = validator.validate(raw)
        assert len(result) == 1
        assert result[0].status.value == "UNKNOWN"


# ── Pydantic Model Tests ─────────────────────────────────────


class TestModels:
    """Tests for backend.models"""

    def test_blood_parameter_creation(self):
        from backend.models.blood_parameter import BloodParameter, ParameterStatus
        param = BloodParameter(
            name="Hemoglobin", value=14.0, unit="g/dL",
            status=ParameterStatus.NORMAL
        )
        assert param.name == "Hemoglobin"
        assert param.value == 14.0

    def test_blood_parameter_json_serialization(self):
        from backend.models.blood_parameter import BloodParameter, ParameterStatus
        param = BloodParameter(
            name="Glucose", value=95.0, unit="mg/dL",
            status=ParameterStatus.NORMAL
        )
        data = param.model_dump()
        assert data["name"] == "Glucose"
        assert data["status"] == "NORMAL"

    def test_user_context_optional_fields(self):
        from backend.models.report import UserContext
        ctx = UserContext()
        assert ctx.age is None
        assert ctx.gender is None

    def test_user_context_with_data(self):
        from backend.models.report import UserContext
        ctx = UserContext(age=30, gender="male", is_smoker=False)
        assert ctx.age == 30
        assert ctx.gender == "male"

    def test_chat_request_validation(self):
        from backend.models.chat import ChatRequest
        req = ChatRequest(report_id="abc-123", message="What is my hemoglobin?")
        assert req.message == "What is my hemoglobin?"

    def test_health_response(self):
        from backend.models.health import HealthResponse, ProviderStatus
        resp = HealthResponse(
            status="ok",
            providers=[ProviderStatus(name="groq_llm", available=True, model="llama-3.1-8b-instant")]
        )
        assert resp.status == "ok"
        assert len(resp.providers) == 1
