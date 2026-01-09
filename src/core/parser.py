import re
import json
import csv
import io
from .enhanced_blood_parser import parse_enhanced_blood_report
from src.phase1.phase1_extractor import Phase1MedicalImageExtractor
from src.phase1.table_extractor import MedicalTableExtractor


# Standard parameter name mappings for normalization
PARAMETER_ALIASES = {
    # Hemoglobin
    'hemoglobin': 'Hemoglobin', 'hb': 'Hemoglobin', 'hgb': 'Hemoglobin', 'haemoglobin': 'Hemoglobin',
    # RBC
    'rbc': 'RBC', 'rbc count': 'RBC', 'total rbc count': 'RBC', 'red blood cell': 'RBC', 'red blood cells': 'RBC', 'erythrocytes': 'RBC',
    # WBC
    'wbc': 'WBC', 'wbc count': 'WBC', 'total wbc count': 'WBC', 'white blood cell': 'WBC', 'white blood cells': 'WBC', 'leucocytes': 'WBC',
    # Platelets
    'platelet': 'Platelet Count', 'platelets': 'Platelet Count', 'platelet count': 'Platelet Count', 'plt': 'Platelet Count',
    # PCV/Hematocrit
    'pcv': 'Hematocrit', 'packed cell volume': 'Hematocrit', 'hematocrit': 'Hematocrit', 'hct': 'Hematocrit',
    # MCV
    'mcv': 'MCV', 'mean cell volume': 'MCV', 'mean corpuscular volume': 'MCV',
    # MCH
    'mch': 'MCH', 'mean cell hemoglobin': 'MCH', 'mean corpuscular hemoglobin': 'MCH',
    # MCHC
    'mchc': 'MCHC', 'mean cell hb conc': 'MCHC',
    # RDW
    'rdw': 'RDW', 'red cell distribution width': 'RDW',
    # Differential
    'neutrophils': 'Neutrophils', 'neut': 'Neutrophils',
    'lymphocytes': 'Lymphocytes', 'lymph': 'Lymphocytes',
    'monocytes': 'Monocytes', 'mono': 'Monocytes',
    'eosinophils': 'Eosinophils', 'eos': 'Eosinophils',
    'basophils': 'Basophils', 'baso': 'Basophils',
    # Chemistry
    'glucose': 'Glucose', 'blood sugar': 'Glucose', 'fasting glucose': 'Glucose',
    'cholesterol': 'Cholesterol', 'total cholesterol': 'Cholesterol',
    'creatinine': 'Creatinine', 'serum creatinine': 'Creatinine',
    'urea': 'Urea', 'blood urea': 'Urea', 'bun': 'Urea',
    # Liver
    'sgpt': 'SGPT', 'alt': 'SGPT',
    'sgot': 'SGOT', 'ast': 'SGOT',
    'bilirubin': 'Bilirubin', 'total bilirubin': 'Bilirubin',
    # Thyroid
    'tsh': 'TSH',
    # Others
    'esr': 'ESR',
    'hba1c': 'HbA1c', 'glycated hemoglobin': 'HbA1c',
}


def _normalize_parameter_name(name: str) -> str:
    """Normalize parameter name to standard form"""
    if not name:
        return name
    
    # Convert to lowercase for lookup
    name_lower = name.lower().strip()
    
    # Check if we have a standard mapping
    if name_lower in PARAMETER_ALIASES:
        return PARAMETER_ALIASES[name_lower]
    
    # Return title case if no mapping found
    return name.strip().title()


def parse_json_report(json_text):
    """Parse structured JSON blood report"""
    try:
        data = json.loads(json_text)
        parameters = {}
        
        # Handle different JSON structures
        if isinstance(data, dict):
            for key, value in data.items():
                normalized_key = _normalize_parameter_name(key)
                if isinstance(value, dict) and 'value' in value:
                    parameters[normalized_key] = value
                elif isinstance(value, (int, float)):
                    parameters[normalized_key] = {"value": float(value), "unit": "N/A"}
        
        return parameters
    except:
        return {}


def _csv_to_parameters(csv_content: str) -> dict:
    """Convert CSV output from phase1 extractors to parameter dict"""
    parameters = {}
    
    # Parameters to exclude (not actual test results)
    excluded_params = {'age', 'gender', 'sex', 'name', 'patient', 'date', 'time', 'id'}
    
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        for row in reader:
            test_name = row.get('test_name', '').strip()
            value = row.get('value', '').strip()
            
            # Skip empty or NA values
            if not test_name or not value or value == 'NA':
                continue
            
            # Skip excluded parameters
            if test_name.lower() in excluded_params:
                continue
            
            # Normalize parameter name
            normalized_name = _normalize_parameter_name(test_name)
            
            # Skip if already have this parameter
            if normalized_name in parameters:
                continue
            
            try:
                float_value = float(value)
                
                # Sanity check - ignore unrealistic values
                if 0.001 <= float_value <= 1000000:
                    unit = row.get('unit', 'N/A')
                    if unit == 'NA':
                        unit = 'N/A'
                    
                    ref_range = row.get('reference_range', 'N/A')
                    if ref_range == 'NA':
                        ref_range = 'N/A'
                    
                    parameters[normalized_name] = {
                        "value": float_value,
                        "unit": unit,
                        "reference_range": ref_range,
                        "raw_text": row.get('raw_text', '')
                    }
            except ValueError:
                continue
    except Exception:
        pass
    
    return parameters


def parse_blood_report(ocr_text):
    """
    Enhanced blood report parser with comprehensive parameter extraction
    Uses multiple extraction strategies and combines results
    """
    all_parameters = {}
    
    # Strategy 1: Enhanced Blood Parser (most accurate - pattern-based with line matching)
    try:
        enhanced_result = parse_enhanced_blood_report(ocr_text)
        if enhanced_result:
            for param_name, param_data in enhanced_result.items():
                normalized = _normalize_parameter_name(param_name)
                if normalized not in all_parameters:
                    all_parameters[normalized] = param_data
    except Exception:
        pass
    
    # Strategy 2: Phase1 Medical Image Extractor (good for structured tables)
    try:
        phase1_extractor = Phase1MedicalImageExtractor()
        csv_result = phase1_extractor.extract_to_csv(ocr_text)
        phase1_params = _csv_to_parameters(csv_result)
        # Only add parameters not already found
        for param_name, param_data in phase1_params.items():
            normalized = _normalize_parameter_name(param_name)
            if normalized not in all_parameters:
                all_parameters[normalized] = param_data
    except Exception:
        pass
    
    # Strategy 3: Table Extractor (good for various table formats)
    try:
        table_extractor = MedicalTableExtractor()
        csv_result = table_extractor.extract_to_csv(ocr_text)
        table_params = _csv_to_parameters(csv_result)
        # Only add parameters not already found (normalized)
        for param_name, param_data in table_params.items():
            normalized = _normalize_parameter_name(param_name)
            if normalized not in all_parameters:
                all_parameters[normalized] = param_data
    except Exception:
        pass
    
    # Strategy 4: Fallback parsing if still no results
    if not all_parameters:
        all_parameters = _parse_blood_report_fallback(ocr_text)
    
    return all_parameters


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
