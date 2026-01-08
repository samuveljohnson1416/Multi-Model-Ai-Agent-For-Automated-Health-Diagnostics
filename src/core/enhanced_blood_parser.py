"""
Enhanced Blood Report Parser
Comprehensive parser for detailed blood reports including CBC, differential counts, and chemistry panels
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple


class EnhancedBloodParser:
    """
    Enhanced parser for comprehensive blood report analysis
    Handles detailed CBC, differential counts, chemistry panels, and more
    """
    
    def __init__(self):
        # Comprehensive parameter patterns with multiple variations
        self.parameter_patterns = {
            # Complete Blood Count (CBC)
            'White Blood Cell (WBC)': {
                'patterns': [
                    r'(?i)white\s+blood\s+cell\s*\(?\s*wbc\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)wbc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)total\s+wbc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)leucocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['WBC', 'White Blood Cell', 'Leucocyte Count', 'Total WBC']
            },
            
            'Red Blood Cell (RBC)': {
                'patterns': [
                    r'(?i)red\s+blood\s+cell\s*\(?\s*rbc\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)rbc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)erythrocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'M/mcL',
                'aliases': ['RBC', 'Red Blood Cell', 'Erythrocyte Count']
            },
            
            'Hemoglobin': {
                'patterns': [
                    r'(?i)hemoglobin\s*\(?\s*hb\s*/?\s*hgb\s*\)?\s*\)?\s*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)',
                    r'(?i)hemoglobin.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)hb\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)hgb.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)\(hb/hgb\)\s*\)?\s*(\d+\.?\d*)\s*([a-zA-Z/µμ]*)'
                ],
                'standard_unit': 'g/dL',
                'aliases': ['Hemoglobin', 'HB', 'Hgb', 'Haemoglobin']
            },
            
            'Hematocrit': {
                'patterns': [
                    r'(?i)hematocrit\s*\(?\s*hct\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)hct.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)packed\s+cell\s+volume.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Hematocrit', 'HCT', 'Packed Cell Volume', 'PCV']
            },
            
            'Mean Cell Volume (MCV)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+volume\s*\(?\s*mcv\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mcv.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'fL',
                'aliases': ['MCV', 'Mean Cell Volume', 'Mean Corpuscular Volume']
            },
            
            'Mean Cell Hemoglobin (MCH)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+hemoglobin\s*\(?\s*mch\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mch(?!\s*conc).*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'  # Avoid matching MCHC
                ],
                'standard_unit': 'pg',
                'aliases': ['MCH', 'Mean Cell Hemoglobin', 'Mean Corpuscular Hemoglobin']
            },
            
            'Mean Cell Hb Conc (MCHC)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+hb\s+conc\s*\(?\s*mchc\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mchc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mean\s+cell\s+hemoglobin\s+concentration.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'g/dL',
                'aliases': ['MCHC', 'Mean Cell Hb Conc', 'Mean Cell Hemoglobin Concentration']
            },
            
            'Red Cell Dist Width (RDW)': {
                'patterns': [
                    r'(?i)red\s+cell\s+dist\s+width\s*\(?\s*rdw\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)rdw.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)red\s+cell\s+distribution\s+width.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['RDW', 'Red Cell Dist Width', 'Red Cell Distribution Width']
            },
            
            'Platelet Count': {
                'patterns': [
                    r'(?i)platelet\s+count.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)platelets.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)plt.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)thrombocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Platelet Count', 'Platelets', 'PLT', 'Thrombocyte Count']
            },
            
            'Mean Platelet Volume': {
                'patterns': [
                    r'(?i)mean\s+platelet\s+volume.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mpv.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'fL',
                'aliases': ['Mean Platelet Volume', 'MPV']
            },
            
            # WBC Differential
            'Neutrophil': {
                'patterns': [
                    r'(?i)neutrophil\s*\(?\s*neut\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)neutrophils.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)neut\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Neutrophil', 'Neutrophils', 'Neut', 'Polymorphs']
            },
            
            'Lymphocyte': {
                'patterns': [
                    r'(?i)lymphocyte\s*\(?\s*lymph\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)lymphocytes.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)lymph\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Lymphocyte', 'Lymphocytes', 'Lymph']
            },
            
            'Monocyte': {
                'patterns': [
                    r'(?i)monocyte\s*\(?\s*mono\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)monocytes.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)mono\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Monocyte', 'Monocytes', 'Mono']
            },
            
            'Eosinophil': {
                'patterns': [
                    r'(?i)eosinophil\s*\(?\s*eos\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)eosinophils.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)eos\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Eosinophil', 'Eosinophils', 'Eos']
            },
            
            'Basophil': {
                'patterns': [
                    r'(?i)basophil\s*\(?\s*baso\s*\)?.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)basophils.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)baso\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)'
                ],
                'standard_unit': '%',
                'aliases': ['Basophil', 'Basophils', 'Baso']
            },
            
            # Absolute Counts
            'Neutrophil, Absolute': {
                'patterns': [
                    r'(?i)neutrophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+neutrophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+neut.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Neutrophil Absolute', 'Absolute Neutrophil', 'Abs Neut']
            },
            
            'Lymphocyte, Absolute': {
                'patterns': [
                    r'(?i)lymphocyte,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+lymphocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+lymph.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Lymphocyte Absolute', 'Absolute Lymphocyte', 'Abs Lymph']
            },
            
            'Monocyte, Absolute': {
                'patterns': [
                    r'(?i)monocyte,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+monocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+mono.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Monocyte Absolute', 'Absolute Monocyte', 'Abs Mono']
            },
            
            'Eosinophil, Absolute': {
                'patterns': [
                    r'(?i)eosinophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+eosinophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+eos.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Eosinophil Absolute', 'Absolute Eosinophil', 'Abs Eos']
            },
            
            'Basophil, Absolute': {
                'patterns': [
                    r'(?i)basophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+basophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+baso.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'K/mcL',
                'aliases': ['Basophil Absolute', 'Absolute Basophil', 'Abs Baso']
            },
            
            # Chemistry Panel
            'Glucose': {
                'patterns': [
                    r'(?i)glucose.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)blood\s+sugar.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)fasting\s+glucose.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'mg/dL',
                'aliases': ['Glucose', 'Blood Sugar', 'Fasting Glucose', 'Random Glucose']
            },
            
            'Cholesterol': {
                'patterns': [
                    r'(?i)total\s+cholesterol.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)cholesterol.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)chol.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'mg/dL',
                'aliases': ['Cholesterol', 'Total Cholesterol', 'CHOL']
            },
            
            'Creatinine': {
                'patterns': [
                    r'(?i)creatinine.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)serum\s+creatinine.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)creat.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)'
                ],
                'standard_unit': 'mg/dL',
                'aliases': ['Creatinine', 'Serum Creatinine', 'CREAT']
            }
        }
        
        # Reference range patterns
        self.reference_patterns = [
            r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',  # 4.8-10.8
            r'(\d+\.?\d*)\s*to\s*(\d+\.?\d*)',    # 4.8 to 10.8
            r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',     # 4.8 - 10.8
            r'<\s*(\d+\.?\d*)',                   # <200
            r'>\s*(\d+\.?\d*)',                   # >40
        ]
    
    def parse_enhanced_blood_report(self, text: str) -> Dict[str, Any]:
        """
        Parse comprehensive blood report with detailed parameter extraction
        
        Args:
            text: Raw text from blood report
            
        Returns:
            Dictionary of extracted parameters with detailed information
        """
        # Try JSON parsing first
        json_result = self._try_json_parsing(text)
        if json_result:
            return json_result
        
        # Parse text-based report
        parameters = {}
        lines = text.split('\n')
        
        # Process each line for parameter extraction
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Try to extract parameters from this line
            extracted_params = self._extract_parameters_from_line(line, lines, line_num)
            parameters.update(extracted_params)
        
        # Post-process to add missing information
        parameters = self._post_process_parameters(parameters, text)
        
        return parameters
    
    def _try_json_parsing(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to parse structured JSON data"""
        try:
            data = json.loads(text)
            if isinstance(data, dict) and any(key in data for key in ['parameters', 'medical_parameters', 'results']):
                return self._convert_json_to_standard_format(data)
        except (json.JSONDecodeError, ValueError):
            pass
        return None
    
    def _convert_json_to_standard_format(self, data: Dict) -> Dict[str, Any]:
        """Convert JSON data to standard parameter format"""
        parameters = {}
        
        # Handle different JSON structures
        if 'parameters' in data:
            for param in data['parameters']:
                name = param.get('name', 'Unknown')
                parameters[name] = {
                    'value': self._safe_float_conversion(param.get('value')),
                    'unit': param.get('unit', ''),
                    'reference_range': param.get('reference_range', ''),
                    'raw_text': param.get('raw_text', name),
                    'confidence': param.get('confidence', 0.95)
                }
        
        return parameters
    
    def _extract_parameters_from_line(self, line: str, all_lines: List[str], line_num: int) -> Dict[str, Any]:
        """Extract parameters from a single line"""
        extracted = {}
        line = line.strip()
        
        if not line:
            return extracted
        
        # Split the line into components
        parts = line.split()
        if len(parts) < 3:
            return extracted
        
        # Try to identify the pattern: Name (Abbrev) Value Status Unit Range
        # Find the first number (value)
        value_index = -1
        for i, part in enumerate(parts):
            if re.match(r'^\d+\.?\d*$', part):
                value_index = i
                break
        
        if value_index == -1:
            return extracted
        
        # Extract components
        param_name_parts = parts[:value_index]
        param_name_raw = ' '.join(param_name_parts)
        
        try:
            value = float(parts[value_index])
        except ValueError:
            return extracted
        
        # Look for status indicator (H, L, N, *)
        status_indicator = ''
        unit = ''
        reference_range = ''
        
        remaining_parts = parts[value_index + 1:]
        
        # Check if next part is status indicator
        if remaining_parts and re.match(r'^[HLN*]+\*?\*?$', remaining_parts[0]):
            status_indicator = remaining_parts[0]
            remaining_parts = remaining_parts[1:]
        
        # Check if next part is unit
        if remaining_parts and re.match(r'^[a-zA-Z/µμ%]+$', remaining_parts[0]):
            unit = remaining_parts[0]
            remaining_parts = remaining_parts[1:]
        
        # Remaining parts should be reference range
        if remaining_parts:
            reference_range = ' '.join(remaining_parts)
        
        # Map parameter names to standard names
        param_mapping = {
            'white blood cell (wbc)': 'White Blood Cell (WBC)',
            'red blood cell (rbc)': 'Red Blood Cell (RBC)',
            'hemoglobin (hb/hgb))': 'Hemoglobin',
            'hemoglobin (hb/hgb)': 'Hemoglobin',
            'hematocrit (hct)': 'Hematocrit',
            'mean cell volume (mcv)': 'Mean Cell Volume (MCV)',
            'mean cell hemoglobin (mch)': 'Mean Cell Hemoglobin (MCH)',
            'mean cell hb conc (mchc)': 'Mean Cell Hb Conc (MCHC)',
            'red cell dist width (rdw)': 'Red Cell Dist Width (RDW)',
            'platelet count': 'Platelet Count',
            'mean platelet volume': 'Mean Platelet Volume',
            'neutrophil (neut)': 'Neutrophil',
            'lymphocyte (lymph)': 'Lymphocyte',
            'monocyte (mono)': 'Monocyte',
            'eosinophil (eos)': 'Eosinophil',
            'basophil (baso)': 'Basophil',
            'neutrophil, absolute': 'Neutrophil, Absolute',
            'lymphocyte, absolute': 'Lymphocyte, Absolute',
            'monocyte, absolute': 'Monocyte, Absolute',
            'eosinophil, absolute': 'Eosinophil, Absolute',
            'basophil, absolute': 'Basophil, Absolute'
        }
        
        # Normalize parameter name
        param_name_lower = param_name_raw.lower()
        param_name = param_mapping.get(param_name_lower, param_name_raw)
        
        # Define unit defaults for all parameters
        unit_defaults = {
            'White Blood Cell (WBC)': 'K/mcL',
            'Red Blood Cell (RBC)': 'M/mcL',
            'Hemoglobin': 'g/dL',
            'Hematocrit': '%',
            'Mean Cell Volume (MCV)': 'fL',
            'Mean Cell Hemoglobin (MCH)': 'pg',
            'Mean Cell Hb Conc (MCHC)': 'g/dL',
            'Red Cell Dist Width (RDW)': '%',
            'Platelet Count': 'K/mcL',
            'Mean Platelet Volume': 'fL',
            'Neutrophil': '%',
            'Lymphocyte': '%',
            'Monocyte': '%',
            'Eosinophil': '%',
            'Basophil': '%',
            'Neutrophil, Absolute': 'K/mcL',
            'Lymphocyte, Absolute': 'K/mcL',
            'Monocyte, Absolute': 'K/mcL',
            'Eosinophil, Absolute': 'K/mcL',
            'Basophil, Absolute': 'K/mcL'
        }
        
        # Determine unit based on parameter type if not provided
        if not unit:
            unit = unit_defaults.get(param_name, '')
        else:
            unit = self._clean_unit(unit, unit)
        
        # Determine status
        status = self._determine_status(value, reference_range, param_name)
        
        # Only add if we have a valid parameter name mapping
        if param_name in param_mapping.values() or param_name in unit_defaults:
            extracted[param_name] = {
                'value': value,
                'unit': unit,
                'reference_range': reference_range,
                'status': status,
                'raw_text': line,
                'confidence': 0.99
            }
        
        return extracted
    
    def _extract_reference_range(self, line: str, all_lines: List[str], line_num: int) -> str:
        """Extract reference range from current or nearby lines"""
        # First try to find reference range in the same line
        for pattern in self.reference_patterns:
            match = re.search(pattern, line)
            if match:
                if '<' in pattern:
                    return f"<{match.group(1)}"
                elif '>' in pattern:
                    return f">{match.group(1)}"
                else:
                    return f"{match.group(1)}-{match.group(2)}"
        
        # Look in nearby lines (within 2 lines)
        for offset in [-1, 1, -2, 2]:
            check_line_num = line_num + offset
            if 0 <= check_line_num < len(all_lines):
                check_line = all_lines[check_line_num]
                for pattern in self.reference_patterns:
                    match = re.search(pattern, check_line)
                    if match:
                        if '<' in pattern:
                            return f"<{match.group(1)}"
                        elif '>' in pattern:
                            return f">{match.group(1)}"
                        else:
                            return f"{match.group(1)}-{match.group(2)}"
        
        return "N/A"
    
    def _determine_status(self, value: float, reference_range: str, param_name: str) -> str:
        """Determine if parameter value is normal, high, or low"""
        if reference_range == "N/A":
            return "UNKNOWN"
        
        try:
            if reference_range.startswith('<'):
                max_val = float(reference_range[1:])
                return "HIGH" if value >= max_val else "NORMAL"
            
            elif reference_range.startswith('>'):
                min_val = float(reference_range[1:])
                return "LOW" if value <= min_val else "NORMAL"
            
            elif '-' in reference_range:
                parts = reference_range.split('-')
                if len(parts) == 2:
                    min_val = float(parts[0].strip())
                    max_val = float(parts[1].strip())
                    
                    if value < min_val:
                        return "LOW"
                    elif value > max_val:
                        return "HIGH"
                    else:
                        return "NORMAL"
        
        except (ValueError, IndexError):
            pass
        
        return "UNKNOWN"
    
    def _clean_unit(self, extracted_unit: str, standard_unit: str) -> str:
        """Clean and standardize units"""
        if not extracted_unit or extracted_unit.isspace():
            return standard_unit
        
        # Unit mappings for standardization
        unit_mappings = {
            'k/mcl': 'K/mcL',
            'k/μl': 'K/mcL', 
            'k/ul': 'K/mcL',
            'm/mcl': 'M/mcL',
            'm/μl': 'M/mcL',
            'm/ul': 'M/mcL',
            'g/dl': 'g/dL',
            'mg/dl': 'mg/dL',
            'fl': 'fL',
            'pg': 'pg',
            '%': '%',
            'percent': '%'
        }
        
        cleaned = extracted_unit.lower().strip()
        return unit_mappings.get(cleaned, extracted_unit)
    
    def _calculate_confidence(self, line: str, param_name: str) -> float:
        """Calculate confidence score for parameter extraction"""
        confidence = 0.8  # Base confidence
        
        # Boost confidence if parameter name appears clearly
        if param_name.lower() in line.lower():
            confidence += 0.1
        
        # Boost confidence if units are present
        if any(unit in line.lower() for unit in ['g/dl', 'mg/dl', 'k/mcl', 'm/mcl', '%', 'fl', 'pg']):
            confidence += 0.05
        
        # Boost confidence if reference range is present
        if any(re.search(pattern, line) for pattern in self.reference_patterns):
            confidence += 0.05
        
        return min(confidence, 0.99)
    
    def _post_process_parameters(self, parameters: Dict[str, Any], full_text: str) -> Dict[str, Any]:
        """Post-process parameters to add missing information and validate"""
        
        # Add any missing critical parameters that might have been missed
        critical_params = ['Hemoglobin', 'White Blood Cell (WBC)', 'Red Blood Cell (RBC)', 'Platelet Count']
        
        for param in critical_params:
            if param not in parameters:
                # Try alternative extraction methods
                alternative_result = self._alternative_extraction(param, full_text)
                if alternative_result:
                    parameters[param] = alternative_result
        
        # Validate and clean up extracted parameters
        validated_parameters = {}
        for param_name, param_data in parameters.items():
            if self._validate_parameter(param_name, param_data):
                validated_parameters[param_name] = param_data
        
        return validated_parameters
    
    def _alternative_extraction(self, param_name: str, text: str) -> Optional[Dict[str, Any]]:
        """Alternative extraction method for missed parameters"""
        # Simplified patterns for critical parameters
        simple_patterns = {
            'Hemoglobin': r'(?i)h[bg].*?(\d+\.?\d*)',
            'White Blood Cell (WBC)': r'(?i)wbc.*?(\d+\.?\d*)',
            'Red Blood Cell (RBC)': r'(?i)rbc.*?(\d+\.?\d*)',
            'Platelet Count': r'(?i)platelet.*?(\d+\.?\d*)'
        }
        
        if param_name in simple_patterns:
            pattern = simple_patterns[param_name]
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1))
                    return {
                        'value': value,
                        'unit': self.parameter_patterns.get(param_name, {}).get('standard_unit', 'N/A'),
                        'reference_range': 'N/A',
                        'status': 'UNKNOWN',
                        'raw_text': match.group(0),
                        'confidence': 0.7
                    }
                except ValueError:
                    pass
        
        return None
    
    def _validate_parameter(self, param_name: str, param_data: Dict[str, Any]) -> bool:
        """Validate extracted parameter data"""
        value = param_data.get('value')
        
        # Basic validation - value should be a positive number
        if not isinstance(value, (int, float)) or value <= 0:
            return False
        
        # Parameter-specific validation ranges
        validation_ranges = {
            'Hemoglobin': (1, 25),
            'White Blood Cell (WBC)': (0.1, 100),
            'Red Blood Cell (RBC)': (0.5, 10),
            'Platelet Count': (10, 2000),
            'Hematocrit': (5, 70),
            'Mean Cell Volume (MCV)': (50, 150),
            'Mean Cell Hemoglobin (MCH)': (15, 50),
            'Mean Cell Hb Conc (MCHC)': (25, 40),
            'Red Cell Dist Width (RDW)': (8, 25),
            'Neutrophil': (0, 100),
            'Lymphocyte': (0, 100),
            'Monocyte': (0, 100),
            'Eosinophil': (0, 100),
            'Basophil': (0, 100)
        }
        
        if param_name in validation_ranges:
            min_val, max_val = validation_ranges[param_name]
            if not (min_val <= value <= max_val):
                return False
        
        return True
    
    def _safe_float_conversion(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point
                cleaned = re.sub(r'[^\d.]', '', value)
                return float(cleaned) if cleaned else 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0


# Convenience function for easy integration
def parse_enhanced_blood_report(text: str) -> Dict[str, Any]:
    """
    Parse comprehensive blood report using enhanced parser
    
    Args:
        text: Raw text from blood report
        
    Returns:
        Dictionary of extracted parameters
    """
    parser = EnhancedBloodParser()
    return parser.parse_enhanced_blood_report(text)