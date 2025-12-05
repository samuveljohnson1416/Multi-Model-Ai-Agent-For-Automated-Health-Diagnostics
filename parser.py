import re


def parse_blood_report(ocr_text):
    """
    Parses blood report text and extracts parameters with values and units.
    Returns a dictionary of extracted parameters.
    """
    parameters = {}
    
    # Common blood test parameter patterns
    patterns = [
        r'(Hemoglobin|HB|Hb)\s*[:\-]?\s*(\d+\.?\d*)\s*(g/dL|gm/dL)?',
        r'(RBC|Red Blood Cell)\s*[:\-]?\s*(\d+\.?\d*)\s*(million/µL|M/µL)?',
        r'(WBC|White Blood Cell)\s*[:\-]?\s*(\d+\.?\d*)\s*(cells/µL|/µL)?',
        r'(Platelet|PLT)\s*[:\-]?\s*(\d+\.?\d*)\s*(lakhs/µL|/µL)?',
        r'(Glucose|Blood Sugar)\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dL)?',
        r'(Cholesterol|CHOL)\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dL)?',
        r'(Creatinine|CREAT)\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dL)?',
        r'(Urea|BUN)\s*[:\-]?\s*(\d+\.?\d*)\s*(mg/dL)?',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
        for match in matches:
            param_name = match.group(1)
            value = match.group(2)
            unit = match.group(3) if len(match.groups()) > 2 else ""
            
            # Normalize parameter names
            param_name = param_name.upper()
            if param_name in ["HB", "HEMOGLOBIN"]:
                param_name = "Hemoglobin"
            
            parameters[param_name] = {
                "value": float(value),
                "unit": unit if unit else "N/A"
            }
    
    return parameters
