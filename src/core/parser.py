import re
import json
from .enhanced_blood_parser import parse_enhanced_blood_report


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
    """
    Enhanced blood report parser with comprehensive parameter extraction
    """
    # Try enhanced parsing first
    enhanced_result = parse_enhanced_blood_report(ocr_text)
    if enhanced_result:
        return enhanced_result
    
    # Fallback to original parsing for compatibility
    return _parse_blood_report_fallback(ocr_text)


def _parse_blood_report_fallback(ocr_text):
    """Original parsing logic as fallback"""
    # Try parsing structured OCR JSON first
    try:
        ocr_data = json.loads(ocr_text)
        if "parameters" in ocr_data:
            # Convert structured OCR format to our format
            parameters = {}
            for param in ocr_data["parameters"]:
                param_name = param.get("name", "Unknown")
                parameters[param_name] = {
                    "value": float(param.get("value", 0)),
                    "unit": param.get("unit", "N/A"),
                    "reference_range": param.get("reference_range", "N/A"),
                    "raw_text": param.get("raw_text", "N/A")
                }
            return parameters
    except:
        pass
    
    # Try regular JSON parsing
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
