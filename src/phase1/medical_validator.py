import json
import re


class MedicalDocumentValidator:
    """Medical Document Extraction and Validation Agent for CBC reports"""
    
    def __init__(self):
        # Valid CBC parameters with their common variations
        self.valid_cbc_parameters = {
            'hemoglobin': ['hemoglobin', 'hb', 'hgb'],
            'total_rbc_count': ['total rbc count', 'rbc count', 'rbc', 'red blood cell count', 'red blood cells'],
            'pcv': ['pcv', 'packed cell volume', 'hematocrit', 'hct'],
            'mcv': ['mcv', 'mean corpuscular volume'],
            'mch': ['mch', 'mean corpuscular hemoglobin'],
            'mchc': ['mchc', 'mean corpuscular hemoglobin concentration'],
            'rdw': ['rdw', 'red cell distribution width'],
            'total_wbc_count': ['total wbc count', 'wbc count', 'wbc', 'white blood cell count', 'white blood cells'],
            'neutrophils': ['neutrophils', 'neutrophil', 'neutro'],
            'lymphocytes': ['lymphocytes', 'lymphocyte', 'lympho'],
            'eosinophils': ['eosinophils', 'eosinophil', 'eosi', 'eos'],
            'monocytes': ['monocytes', 'monocyte', 'mono'],
            'basophils': ['basophils', 'basophil', 'baso'],
            'platelet_count': ['platelet count', 'platelets', 'platelet', 'plt']
        }
        
        # Noise patterns to ignore
        self.ignore_patterns = [
            r'(?i)(?:address|email|phone|tel|fax)',
            r'(?i)(?:mindray|sysmex|beckman|abbott|roche)',
            r'(?i)(?:fully automated|cell counter|analyzer)',
            r'(?i)(?:date|time|collected|received|reported)',
            r'(?i)(?:registration|patient id|lab no)',
            r'(?i)(?:department|laboratory|pathology)',
            r'(?i)(?:doctor|physician|consultant)',
            r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Dates
            r'\d{1,2}:\d{2}(?::\d{2})?',  # Times
            r'[A-Z]{2,}\s*\d+',  # Lab codes
            r'(?i)(?:high|low|normal|absent)$',  # Standalone status words
        ]
    
    def is_noise(self, text):
        """Check if text is noise that should be ignored"""
        for pattern in self.ignore_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def normalize_parameter_name(self, name):
        """Normalize parameter name to standard CBC parameter"""
        name_lower = name.lower().strip()
        
        for standard_name, variations in self.valid_cbc_parameters.items():
            for variation in variations:
                if variation in name_lower:
                    return standard_name.replace('_', ' ').title()
        
        return None  # Not a valid CBC parameter
    
    def normalize_unit(self, unit):
        """Normalize units to standard format"""
        if not unit:
            return "UNKNOWN"
        
        unit_map = {
            'g/dl': 'g/dL',
            'gm/dl': 'g/dL',
            'g%': 'g/dL',
            'mill/cumm': 'mill/cumm',
            'million/cumm': 'mill/cumm',
            'thou/cumm': 'thou/cumm',
            'thousand/cumm': 'thou/cumm',
            '/cumm': '/cumm',
            'cells/cumm': '/cumm',
            'fl': 'fL',
            'pg': 'pg',
            '%': '%',
            'percent': '%'
        }
        
        normalized = unit.lower().strip()
        return unit_map.get(normalized, unit.strip())
    
    def normalize_reference_range(self, ref_range):
        """Normalize reference range format"""
        if not ref_range or ref_range.lower() in ['unknown', 'na', 'n/a']:
            return "UNKNOWN"
        
        # Clean and normalize range format
        cleaned = re.sub(r'\s+', ' ', str(ref_range).strip())
        cleaned = re.sub(r'[-–—]', ' - ', cleaned)
        
        return cleaned
    
    def determine_status(self, value, ref_range):
        """Determine if value is Low, High, Normal, or UNKNOWN"""
        if not value or not ref_range or ref_range == "UNKNOWN":
            return "UNKNOWN"
        
        try:
            numeric_value = float(str(value))
            
            # Extract range bounds
            range_match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', ref_range)
            if range_match:
                low_bound = float(range_match.group(1))
                high_bound = float(range_match.group(2))
                
                if numeric_value < low_bound:
                    return "Low"
                elif numeric_value > high_bound:
                    return "High"
                else:
                    return "Normal"
        except (ValueError, AttributeError):
            pass
        
        return "UNKNOWN"
    
    def extract_table_section(self, text):
        """Extract only the investigation/result table section"""
        lines = text.split('\n')
        table_lines = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious noise
            if self.is_noise(line):
                continue
            
            # Look for table indicators
            if any(keyword in line.lower() for keyword in ['investigation', 'test', 'parameter', 'result', 'value', 'reference']):
                in_table = True
                continue
            
            # If we find a line with medical parameters, we're in the table
            if any(param in line.lower() for variations in self.valid_cbc_parameters.values() for param in variations):
                in_table = True
            
            if in_table:
                # Stop if we hit footer/signature section
                if any(keyword in line.lower() for keyword in ['signature', 'doctor', 'pathologist', 'end of report']):
                    break
                
                table_lines.append(line)
        
        return '\n'.join(table_lines)
    
    def merge_broken_lines(self, text):
        """Merge broken lines that belong to the same test"""
        lines = text.split('\n')
        merged_lines = []
        current_line = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # If line starts with a valid parameter name, start new line
            param_name = self.normalize_parameter_name(line.split()[0] if line.split() else "")
            if param_name:
                if current_line:
                    merged_lines.append(current_line)
                current_line = line
            else:
                # Continuation of previous line
                if current_line:
                    current_line += " " + line
                else:
                    current_line = line
        
        if current_line:
            merged_lines.append(current_line)
        
        return merged_lines
    
    def extract_parameter_from_line(self, line):
        """Extract parameter data from a single line"""
        # Pattern to match: parameter_name value unit reference_range
        patterns = [
            r'^([A-Za-z\s]+?)\s+(\d+\.?\d*)\s+([A-Za-z/%]+)\s+(.+)$',
            r'^([A-Za-z\s]+?)\s+(\d+\.?\d*)\s+(.+)$',
            r'^([A-Za-z\s]+?)\s+(\d+\.?\d*)$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line.strip())
            if match:
                param_name = match.group(1).strip()
                value = match.group(2).strip()
                
                # Normalize parameter name
                normalized_name = self.normalize_parameter_name(param_name)
                if not normalized_name:
                    return None  # Not a valid CBC parameter
                
                unit = "UNKNOWN"
                ref_range = "UNKNOWN"
                
                if len(match.groups()) > 2:
                    remaining = match.group(3).strip()
                    
                    # Try to separate unit and reference range
                    unit_match = re.search(r'^([A-Za-z/%]+)', remaining)
                    if unit_match:
                        unit = self.normalize_unit(unit_match.group(1))
                        ref_range = remaining[len(unit_match.group(1)):].strip()
                    else:
                        ref_range = remaining
                
                if len(match.groups()) > 3:
                    ref_range = match.group(4).strip()
                
                # Normalize reference range
                ref_range = self.normalize_reference_range(ref_range)
                
                # Determine status
                status = self.determine_status(value, ref_range)
                
                return {
                    "name": normalized_name,
                    "value": float(value) if '.' in value else int(value),
                    "unit": unit,
                    "reference_range": ref_range,
                    "status": status
                }
        
        return None
    
    def validate_and_extract(self, ocr_text):
        """Main validation and extraction method"""
        # Step 1: Extract table section only
        table_text = self.extract_table_section(ocr_text)
        
        # Step 2: Merge broken lines
        merged_lines = self.merge_broken_lines(table_text)
        
        # Step 3: Extract parameters from each line
        extracted_parameters = {}
        
        for line in merged_lines:
            param_data = self.extract_parameter_from_line(line)
            if param_data:
                test_name = param_data["name"]
                extracted_parameters[test_name] = {
                    "value": param_data["value"],
                    "unit": param_data["unit"],
                    "reference_range": param_data["reference_range"],
                    "status": param_data["status"]
                }
        
        # Step 4: Quality check - prefer correctness over completeness
        if not extracted_parameters:
            return {}
        
        return extracted_parameters


def process_medical_document(ocr_text):
    """Process OCR text through Medical Document Validation Agent"""
    validator = MedicalDocumentValidator()
    
    try:
        # Extract and validate medical parameters
        validated_data = validator.validate_and_extract(ocr_text)
        
        # Return strict JSON format
        return json.dumps(validated_data, indent=2)
        
    except Exception as e:
        # Return empty result on error
        return json.dumps({})