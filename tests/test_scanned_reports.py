"""Scanned / photographed reports: PDF rendering, OCR post-processing, row parsing (no network)."""
import io

from backend.services.ocr_service import _detections_to_text, _pdf_to_images, _vision_rows_to_lines
from backend.services.parser_service import ParserService
from backend.services.validator_service import ValidatorService


def test_scanned_pdf_renders_without_poppler():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (300, 200), "white").save(buf, format="PDF")
    images = _pdf_to_images(buf.getvalue(), dpi=100)
    assert len(images) == 1 and images[0].width > 300


def _det(text, x, y):  # one NVIDIA text detection, box 0.1 wide and 0.01 tall
    pts = [{"x": x, "y": y}, {"x": x + 0.1, "y": y}, {"x": x + 0.1, "y": y + 0.01}, {"x": x, "y": y + 0.01}]
    return {"text_prediction": {"text": text}, "bounding_box": {"points": pts}}


def test_nvidia_detections_become_ordered_lines():
    dets = [_det("6.22", 0.2, 0.301), _det("RBC", 0.1, 0.30), _det("HGB", 0.1, 0.35), _det("17.4", 0.2, 0.352)]
    assert _detections_to_text(dets) == "RBC 6.22\nHGB 17.4"


def test_vision_rows_to_lines():
    reply = "name|value|unit|range_low|range_high\nHGB|17.4|g/dL|11.5|17.0\nCRP|3.8||0|6\nnoise line\nWBC|x|u|1|2"
    assert _vision_rows_to_lines(reply) == ["HGB 17.4 g/dL 11.5 - 17", "CRP 3.8  0 - 6"]


def test_range_comes_from_the_parameters_own_row():
    # HGB has no range of its own; it must not inherit RBC's from the row above.
    parsed = ParserService().parse("RBC 6.22 10^6/uL 3.8 - 6\nHGB 17.4 g/dL\nHCT 53.4 % 35 - 52")
    assert "reference_range" not in parsed["Hemoglobin"]
    assert parsed["PCV"]["reference_range"] == "35 - 52"


def test_differential_row_uses_percent_not_absolute_count():
    parsed = ParserService().parse("NEU 2.63 1.60-7.00 51.1 40.0-73.0")
    assert parsed["Neutrophils"] == {"value": 51.1, "unit": "%", "reference_range": "40.0 - 73.0"}


def test_thousands_units_are_scaled_not_flagged_critical():
    # x10^3/uL printed values (182, 5.14) vs built-in per-cumm ranges
    parsed = ParserService().parse("PLT 182 10^3/uL 150 - 400\nWBC 5.14 10^3/uL 3.5 - 10")
    params = {p.name: p for p in ValidatorService().validate(parsed, age=21)}
    assert params["Platelet"].value == 182000 and params["Platelet"].status.value == "NORMAL"
    assert params["WBC"].value == 5140 and params["WBC"].status.value == "NORMAL"

    # OCR garbled the unit (10%/L) but the printed range still shows the scale
    raw = {"Platelet": {"value": 182.0, "unit": "/cumm", "reference_range": "150 - 400"}}
    p = ValidatorService().validate(raw)[0]
    assert p.value == 182000 and p.status.value == "NORMAL"
