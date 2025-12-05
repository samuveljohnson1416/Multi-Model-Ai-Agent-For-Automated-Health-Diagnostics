import re


def parse_blood_report(ocr_text):
    parameters = {}
    
    patterns = [
        (r'(?:Hemoglobin|HB|Hb|HEMOGLOBIN)\s*[:\-\s]*(\d+\.?\d*)\s*(?:g/dL|gm/dL|g/dl)?', 'Hemoglobin', 'g/dL'),
        (r'(?:RBC|Red Blood Cell|Red Blood Cells|RBC Count)\s*[:\-\s]*(\d+\.?\d*)\s*(?:million/µL|M/µL|mill/cumm)?', 'RBC', 'million/µL'),
        (r'(?:WBC|White Blood Cell|White Blood Cells|WBC Count|Total WBC)\s*[:\-\s]*(\d+\.?\d*)\s*(?:cells/µL|/µL|thou/cumm|x10\^3/µL)?', 'WBC', 'cells/µL'),
        (r'(?:Platelet|PLT|Platelets|Platelet Count)\s*[:\-\s]*(\d+\.?\d*)\s*(?:lakhs/µL|/µL|thou/cumm|x10\^3/µL)?', 'Platelet', 'lakhs/µL'),
        (r'(?:Glucose|Blood Sugar|Blood Glucose|Fasting Glucose)\s*[:\-\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)?', 'Glucose', 'mg/dL'),
        (r'(?:Cholesterol|CHOL|Total Cholesterol)\s*[:\-\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)?', 'Cholesterol', 'mg/dL'),
        (r'(?:Creatinine|CREAT|Serum Creatinine)\s*[:\-\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)?', 'Creatinine', 'mg/dL'),
        (r'(?:Urea|BUN|Blood Urea Nitrogen)\s*[:\-\s]*(\d+\.?\d*)\s*(?:mg/dL|mg/dl)?', 'BUN', 'mg/dL'),
    ]
    
    for pattern, param_name, default_unit in patterns:
        matches = re.finditer(pattern, ocr_text, re.IGNORECASE)
        for match in matches:
            value = match.group(1)
            
            if param_name not in parameters:
                try:
                    parameters[param_name] = {
                        "value": float(value),
                        "unit": default_unit
                    }
                except ValueError:
                    continue
    
    return parameters
