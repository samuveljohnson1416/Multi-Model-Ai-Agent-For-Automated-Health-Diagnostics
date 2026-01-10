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


def json_to_ml_csv(ingestion_result):
    """Convert OCR and Data Ingestion output to ML-ready CSV"""
    
    csv_rows = []
    
    try:
        # Parse ingestion result
        data = json.loads(ingestion_result)
        
        # Handle different file types
        if "file_type" in data:
            file_type = data["file_type"]
            
            if file_type == "CSV":
                # Return CSV as-is
                return data["csv_content"]
            
            elif file_type == "JSON":
                # Convert JSON data to CSV format
                json_data = data["data"]
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        csv_rows.append({
                            'name': key,
                            'value': normalize_value(value),
                            'unit': 'NA',
                            'reference_range': 'NA',
                            'raw_text': clean_raw_text(f"{key}: {value}"),
                            'confidence': '1.00'
                        })
        
        # Handle structured medical parameters
        if "medical_parameters" in data:
            parameters = data["medical_parameters"]
            
            for param in parameters:
                csv_rows.append({
                    'name': param.get('name', 'NA'),
                    'value': normalize_value(param.get('value')),
                    'unit': normalize_unit(param.get('unit')),
                    'reference_range': normalize_reference_range(param.get('reference_range')),
                    'raw_text': clean_raw_text(param.get('raw_text', param.get('name', ''))),
                    'confidence': param.get('confidence', 'NA')
                })
        
        # Handle OCR-extracted parameters (old format)
        elif "parameters" in data:
            parameters = data["parameters"]
            
            for param in parameters:
                csv_rows.append({
                    'name': param.get('name', 'NA'),
                    'value': normalize_value(param.get('value')),
                    'unit': normalize_unit(param.get('unit')),
                    'reference_range': normalize_reference_range(param.get('reference_range')),
                    'raw_text': clean_raw_text(param.get('raw_text')),
                    'confidence': param.get('confidence', 'NA')
                })
        
        # If no structured data found, try fallback extraction
        if not csv_rows and "raw_text" in data:
            csv_rows = fallback_extraction(data["raw_text"])
            
    except json.JSONDecodeError:
        # Fallback for plain text
        csv_rows = fallback_extraction(ingestion_result)
    
    # Create DataFrame
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        # Remove duplicates and sort
        df = df.drop_duplicates(subset=['name'], keep='first')
        df = df.sort_values('name').reset_index(drop=True)
        df = df.fillna('NA')
    else:
        # Empty DataFrame with headers
        df = pd.DataFrame(columns=['name', 'value', 'unit', 'reference_range', 'raw_text', 'confidence'])
    
    return df.to_csv(index=False)


def fallback_extraction(text):
    """Fallback extraction for plain text"""
    csv_rows = []
    lines = text.split('\n')
    
    patterns = {
        'Hemoglobin': r'(?i)(?:hemoglobin|hb|hgb).*?(\d+\.?\d*)',
        'RBC': r'(?i)(?:rbc|red blood cell).*?(\d+\.?\d*)',
        'WBC': r'(?i)(?:wbc|white blood cell).*?(\d+\.?\d*)',
        'Platelet': r'(?i)(?:platelet|plt).*?(\d+\.?\d*)',
        'Glucose': r'(?i)glucose.*?(\d+\.?\d*)',
        'Cholesterol': r'(?i)cholesterol.*?(\d+\.?\d*)',
        'Creatinine': r'(?i)creatinine.*?(\d+\.?\d*)',
        'BUN': r'(?i)(?:bun|urea).*?(\d+\.?\d*)',
    }
    
    for line in lines:
        for param_name, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                value = match.group(1)
                try:
                    float_val = float(value)
                    if 0.1 <= float_val <= 50000:
                        csv_rows.append({
                            'name': param_name,
                            'value': normalize_value(value),
                            'unit': 'NA',
                            'reference_range': 'NA',
                            'raw_text': clean_raw_text(line),
                            'confidence': '0.70'
                        })
                        break
                except ValueError:
                    continue
    
    return csv_rows