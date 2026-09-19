from backend.services.parser_service import ParserService


def test_pipe_table_rows_keep_their_values():
    # pdfplumber PDFs yield a text layer plus a pipe table; table rows used to
    # come back with value=None and shadow the good regex results.
    text = (
        "PCV 42.0 % 40-50\nNeutrophils 85 % 50-62 High\n"
        "Investigation | Result | Units | Ref. Range | Flag\n"
        "PCV | 42.0 | % | 40-50 | \n"
        "Neutrophils | 85 | % | 50-62 | High\n"
    )
    p = ParserService().parse(text)
    assert p["PCV"]["value"] == 42.0 and p["PCV"]["unit"] == "%"
    assert p["Neutrophils"]["value"] == 85.0


def test_report_reference_range_takes_priority():
    from backend.services.validator_service import ValidatorService

    v = ValidatorService()
    raw = {"Hemoglobin": {"value": 13.8, "unit": "g/dL", "reference_range": "13.0 - 17.0"}}
    p = v.validate(raw, age=42, gender="male")[0]
    assert (p.reference_min, p.reference_max) == (13.0, 17.0) and p.status.value == "NORMAL"

    # implausible range (OCR noise) is ignored -> built-in range used instead
    raw["Hemoglobin"]["reference_range"] = "1.0 - 2.0"
    p = v.validate(raw)[0]
    assert (p.reference_min, p.reference_max) == (12.0, 17.0)
