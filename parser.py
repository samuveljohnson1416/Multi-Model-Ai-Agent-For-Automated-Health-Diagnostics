import re
import json


def parse_json_report(json_text):
    """Parse structured JSON blood report"""
    try:
        data = json.loads(json_text)
        parameters = {}
        
        # Handle different JSON structures
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict) and 'value' in value:
                    parameters[key] = value
                elif isinstance(value, (int, float)):
                    parameters[key] = {"value": float(value), "unit": "N/A"}
        
        return parameters
    except:
        return {}


def parse_blood_report(ocr_text):
    # Try JSON parsing first
    json_params = parse_json_report(ocr_text)
    if json_params:
        return json_params
    
    parameters = {}
    
    # More flexible patterns - matches parameter name anywhere on line with a number
    patterns = [
        # Hemoglobin - very flexible
        (r'(?:Hemoglobin|HB|Hb|HEMOGLOBIN|hemoglobin|hb).*?(\d+\.?\d*)', 'Hemoglobin', 'g/dL'),
        
        # RBC - flexible
        (r'(?:RBC|Red Blood Cell|Red Blood Cells|RBC Count|rbc).*?(\d+\.?\d*)', 'RBC', 'million/µL'),
        
        # WBC - flexible
        (r'(?:WBC|White Blood Cell|White Blood Cells|WBC Count|Total WBC|wbc).*?(\d+\.?\d*)', 'WBC', 'cells/µL'),
        
        # Platelet - flexible
        (r'(?:Platelet|PLT|Platelets|Platelet Count|platelet|plt).*?(\d+\.?\d*)', 'Platelet', 'lakhs/µL'),
        
        # Glucose
        (r'(?:Glucose|Blood Sugar|Blood Glucose|Fasting Glucose|glucose).*?(\d+\.?\d*)', 'Glucose', 'mg/dL'),
        
        # Cholesterol
        (r'(?:Cholesterol|CHOL|Total Cholesterol|cholesterol).*?(\d+\.?\d*)', 'Cholesterol', 'mg/dL'),
        
        # Creatinine
        (r'(?:Creatinine|CREAT|Serum Creatinine|creatinine).*?(\d+\.?\d*)', 'Creatinine', 'mg/dL'),
        
        # Urea/BUN
        (r'(?:Urea|BUN|Blood Urea Nitrogen|urea|bun).*?(\d+\.?\d*)', 'BUN', 'mg/dL'),
    ]
    
    # Process line by line for better accuracy
    lines = ocr_text.split('\n')
    
    for line in lines:
        for pattern, param_name, default_unit in patterns:
            if param_name not in parameters:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    try:
                        float_value = float(value)
                        # Sanity check - ignore unrealistic values
                        if 0.1 <= float_value <= 100000:
                            parameters[param_name] = {
                                "value": float_value,
                                "unit": default_unit
                            }
                    except ValueError:
                        continue
    
    return parameters
