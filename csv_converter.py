import json
import pandas as pd
import re


def normalize_unit(unit):
    """Normalize units to standard format"""
    if not unit or unit == "N/A":
        return "NA"
    
    # Common unit normalizations
    unit_map = {
        'g/dl': 'g/dL',
        'gm/dl': 'g/dL',
        'mg/dl': 'mg/dL',
        'cells/ul': 'cells/µL',
        'cells/µl': 'cells/µL',
        '/ul': '/µL',
        '/µl': '/µL',
        'million/ul': 'million/µL',
        'million/µl': 'million/µL',
        'lakhs/ul': 'lakhs/µL',
        'lakhs/µl': 'lakhs/µL',
    }
    
    normalized = unit.lower().strip()
    return unit_map.get(normalized, unit.strip())


def normalize_value(value):
    """Normalize numeric values"""
    if not value or value == "N/A":
        return "NA"
    
    try:
        # Convert to float and back to remove unnecessary decimals
        num_val = float(str(value))
        if num_val == int(num_val):
            return str(int(num_val))
        else:
            return f"{num_val:.2f}".rstrip('0').rstrip('.')
    except:
        return str(value)


def normalize_reference_range(ref_range):
    """Normalize reference ranges"""
    if not ref_range or ref_range == "N/A":
        return "NA"
    
    # Clean up common reference range formats
    cleaned = re.sub(r'\s+', ' ', str(ref_range).strip())
    cleaned = re.sub(r'[-–—]', '-', cleaned)  # Normalize dashes
    
    return cleaned if cleaned else "NA"


def clean_raw_text(raw_text):
    """Clean raw text for CSV"""
    if not raw_text or raw_text == "N/A":
        return "NA"
    
    # Remove newlines, extra spaces, and CSV-breaking characters
    cleaned = re.sub(r'\s+', ' ', str(raw_text).strip())
    cleaned = cleaned.replace(',', ';').replace('"', "'")
    
    return cleaned if cleaned else "NA"


def json_to_ml_csv(json_text, confidence="NA"):
    """Convert OCR JSON to ML-ready CSV format"""
    try:
        # Parse JSON
        data = json.loads(json_text)
        
        # Extract parameters
        parameters = data.get("parameters", [])
        ocr_confidence = data.get("ocr_confidence", confidence)
        
        # Create CSV rows
        csv_rows = []
        
        for param in parameters:
            row = {
                'name': param.get('name', 'NA'),
                'value': normalize_value(param.get('value')),
                'unit': normalize_unit(param.get('unit')),
                'reference_range': normalize_reference_range(param.get('reference_range')),
                'raw_text': clean_raw_text(param.get('raw_text')),
                'confidence': ocr_confidence.replace('%', '') if '%' in str(ocr_confidence) else ocr_confidence
            }
            csv_rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(csv_rows)
        
        # Fill missing values with NA
        df = df.fillna('NA')
        
        # Sort alphabetically by name
        df = df.sort_values('name')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        # Convert to CSV string
        csv_string = df.to_csv(index=False)
        
        return csv_string
        
    except Exception as e:
        # Fallback: create empty CSV with headers
        df = pd.DataFrame(columns=['name', 'value', 'unit', 'reference_range', 'raw_text', 'confidence'])
        return df.to_csv(index=False)