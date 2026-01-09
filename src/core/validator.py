"""
Blood Report Parameter Validator
Validates extracted parameters and determines status (NORMAL/HIGH/LOW)
"""

import json
import os


# Built-in reference ranges for common blood parameters
DEFAULT_REFERENCE_RANGES = {
    # CBC
    'Hemoglobin': {'min': 12.0, 'max': 17.0, 'unit': 'g/dL'},
    'RBC': {'min': 4.0, 'max': 6.0, 'unit': 'million/µL'},
    'WBC': {'min': 4000, 'max': 11000, 'unit': 'cells/µL'},
    'Platelet Count': {'min': 150000, 'max': 400000, 'unit': '/µL'},
    'Hematocrit': {'min': 36, 'max': 50, 'unit': '%'},
    'MCV': {'min': 80, 'max': 100, 'unit': 'fL'},
    'MCH': {'min': 27, 'max': 33, 'unit': 'pg'},
    'MCHC': {'min': 32, 'max': 36, 'unit': 'g/dL'},
    'RDW': {'min': 11.5, 'max': 14.5, 'unit': '%'},
    'MPV': {'min': 7.5, 'max': 11.5, 'unit': 'fL'},
    
    # Differential
    'Neutrophils': {'min': 40, 'max': 70, 'unit': '%'},
    'Lymphocytes': {'min': 20, 'max': 40, 'unit': '%'},
    'Monocytes': {'min': 2, 'max': 8, 'unit': '%'},
    'Eosinophils': {'min': 1, 'max': 4, 'unit': '%'},
    'Basophils': {'min': 0, 'max': 1, 'unit': '%'},
    
    # Chemistry
    'Glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
    'Total Cholesterol': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
    'HDL Cholesterol': {'min': 40, 'max': 60, 'unit': 'mg/dL'},
    'LDL Cholesterol': {'min': 0, 'max': 100, 'unit': 'mg/dL'},
    'Triglycerides': {'min': 0, 'max': 150, 'unit': 'mg/dL'},
    'Creatinine': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL'},
    'BUN': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
    'Uric Acid': {'min': 3.5, 'max': 7.2, 'unit': 'mg/dL'},
    
    # Liver Function
    'SGPT/ALT': {'min': 7, 'max': 56, 'unit': 'U/L'},
    'SGOT/AST': {'min': 10, 'max': 40, 'unit': 'U/L'},
    'Bilirubin Total': {'min': 0.1, 'max': 1.2, 'unit': 'mg/dL'},
    'Alkaline Phosphatase': {'min': 44, 'max': 147, 'unit': 'U/L'},
    
    # Thyroid
    'TSH': {'min': 0.4, 'max': 4.0, 'unit': 'mIU/L'},
    'T3': {'min': 80, 'max': 200, 'unit': 'ng/dL'},
    'T4': {'min': 5.0, 'max': 12.0, 'unit': 'µg/dL'},
    
    # Others
    'ESR': {'min': 0, 'max': 20, 'unit': 'mm/hr'},
    'HbA1c': {'min': 4.0, 'max': 5.6, 'unit': '%'},
    'Vitamin D': {'min': 30, 'max': 100, 'unit': 'ng/mL'},
    'Vitamin B12': {'min': 200, 'max': 900, 'unit': 'pg/mL'},
    'Iron': {'min': 60, 'max': 170, 'unit': 'µg/dL'},
    'Ferritin': {'min': 12, 'max': 300, 'unit': 'ng/mL'},
    'Calcium': {'min': 8.5, 'max': 10.5, 'unit': 'mg/dL'},
    'Sodium': {'min': 136, 'max': 145, 'unit': 'mEq/L'},
    'Potassium': {'min': 3.5, 'max': 5.0, 'unit': 'mEq/L'},
    'Chloride': {'min': 98, 'max': 106, 'unit': 'mEq/L'},
}


def load_reference_ranges():
    """Load reference ranges from file or use defaults"""
    # Try to load from config file
    config_paths = [
        'config/reference_ranges.json',
        'reference_ranges.json',
        os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'reference_ranges.json')
    ]
    
    for path in config_paths:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except:
            continue
    
    # Return default ranges if file not found
    return DEFAULT_REFERENCE_RANGES


def validate_parameters(parsed_data):
    """
    Validate parsed parameters and determine status
    
    Args:
        parsed_data: Dictionary of parsed parameters from parser
        
    Returns:
        Dictionary with validated parameters including status
    """
    if not parsed_data:
        return {}
    
    reference_ranges = load_reference_ranges()
    validated_data = {}
    
    for param_name, param_info in parsed_data.items():
        try:
            value = param_info.get("value")
            unit = param_info.get("unit", "")
            existing_status = param_info.get("status", "")
            existing_ref_range = param_info.get("reference_range", "")
            
            # Skip if no value
            if value is None:
                continue
            
            # Convert value to float if string
            if isinstance(value, str):
                try:
                    value = float(value.replace(',', ''))
                except ValueError:
                    continue
            
            # Initialize validated entry
            validated_data[param_name] = {
                "value": value,
                "unit": unit,
                "status": "UNKNOWN",
                "reference_range": existing_ref_range if existing_ref_range else "N/A"
            }
            
            # If parser already determined status, use it
            if existing_status and existing_status in ["NORMAL", "HIGH", "LOW"]:
                validated_data[param_name]["status"] = existing_status
                continue
            
            # Try to find reference range for this parameter
            ref = None
            
            # Direct match
            if param_name in reference_ranges:
                ref = reference_ranges[param_name]
            else:
                # Try case-insensitive match
                for ref_name, ref_data in reference_ranges.items():
                    if ref_name.lower() == param_name.lower():
                        ref = ref_data
                        break
                    # Try partial match
                    if ref_name.lower() in param_name.lower() or param_name.lower() in ref_name.lower():
                        ref = ref_data
                        break
            
            # Determine status based on reference range
            if ref:
                min_val = ref.get("min", 0)
                max_val = ref.get("max", float('inf'))
                ref_unit = ref.get("unit", "")
                
                validated_data[param_name]["reference_range"] = f"{min_val}-{max_val} {ref_unit}".strip()
                
                if value < min_val:
                    validated_data[param_name]["status"] = "LOW"
                elif value > max_val:
                    validated_data[param_name]["status"] = "HIGH"
                else:
                    validated_data[param_name]["status"] = "NORMAL"
            else:
                # No reference range found - try to parse from existing reference_range string
                if existing_ref_range and existing_ref_range != "N/A":
                    status = _determine_status_from_range_string(value, existing_ref_range)
                    if status:
                        validated_data[param_name]["status"] = status
                        
        except Exception as e:
            # If any error, still include the parameter with UNKNOWN status
            validated_data[param_name] = {
                "value": param_info.get("value"),
                "unit": param_info.get("unit", ""),
                "status": "UNKNOWN",
                "reference_range": "N/A"
            }
    
    return validated_data


def _determine_status_from_range_string(value, range_string):
    """
    Determine status from a reference range string like "13.0-17.0"
    """
    import re
    
    try:
        # Try to parse range like "13.0-17.0" or "13.0 - 17.0"
        match = re.search(r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)', range_string)
        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))
            
            if value < min_val:
                return "LOW"
            elif value > max_val:
                return "HIGH"
            else:
                return "NORMAL"
        
        # Try to parse "<200" format
        match = re.search(r'<\s*(\d+\.?\d*)', range_string)
        if match:
            max_val = float(match.group(1))
            return "HIGH" if value >= max_val else "NORMAL"
        
        # Try to parse ">40" format
        match = re.search(r'>\s*(\d+\.?\d*)', range_string)
        if match:
            min_val = float(match.group(1))
            return "LOW" if value <= min_val else "NORMAL"
            
    except:
        pass
    
    return None
