"""
Enhanced Blood Report Parser
Strict parser that only extracts parameters when clearly present in text
"""

import re
from typing import Dict, Any, Optional, List


class EnhancedBloodParser:
    """
    Strict parser that extracts blood parameters only when clearly identified
    Avoids false positives by requiring parameter name and value on same line
    """
    
    def __init__(self):
        # Parameter definitions with strict patterns
        self.parameters = {
            # CBC - Complete Blood Count
            'Hemoglobin': {
                'patterns': [
                    r'(?i)hemoglobin[:\s]+(\d+\.?\d*)',
                    r'(?i)haemoglobin[:\s]+(\d+\.?\d*)',
                    r'(?i)\bhb\b[:\s]+(\d+\.?\d*)',
                    r'(?i)\bhgb\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'g/dL',
                'min': 12.0, 'max': 17.0
            },
            'RBC': {
                'patterns': [
                    r'(?i)rbc[:\s]+(\d+\.?\d*)',
                    r'(?i)red\s+blood\s+cell[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)erythrocyte[s]?[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'million/µL',
                'min': 4.0, 'max': 6.0
            },
            'WBC': {
                'patterns': [
                    r'(?i)wbc[:\s]+(\d+\.?\d*)',
                    r'(?i)white\s+blood\s+cell[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)leucocyte[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)total\s+wbc[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'cells/µL',
                'min': 4000, 'max': 11000
            },
            'Platelet Count': {
                'patterns': [
                    r'(?i)platelet[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)platelet\s+count[:\s]+(\d+\.?\d*)',
                    r'(?i)\bplt\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '/µL',
                'min': 150000, 'max': 400000
            },
            'Hematocrit': {
                'patterns': [
                    r'(?i)hematocrit[:\s]+(\d+\.?\d*)',
                    r'(?i)\bhct\b[:\s]+(\d+\.?\d*)',
                    r'(?i)pcv[:\s]+(\d+\.?\d*)',
                    r'(?i)packed\s+cell\s+volume[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 36, 'max': 50
            },
            'MCV': {
                'patterns': [
                    r'(?i)\bmcv\b[:\s]+(\d+\.?\d*)',
                    r'(?i)mean\s+cell\s+volume[:\s]+(\d+\.?\d*)',
                    r'(?i)mean\s+corpuscular\s+volume[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'fL',
                'min': 80, 'max': 100
            },
            'MCH': {
                'patterns': [
                    r'(?i)\bmch\b(?!\s*c)[:\s]+(\d+\.?\d*)',  # MCH but not MCHC
                    r'(?i)mean\s+cell\s+hemoglobin(?!\s+conc)[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'pg',
                'min': 27, 'max': 33
            },
            'MCHC': {
                'patterns': [
                    r'(?i)\bmchc\b[:\s]+(\d+\.?\d*)',
                    r'(?i)mean\s+cell\s+hb\s+conc[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'g/dL',
                'min': 32, 'max': 36
            },
            'RDW': {
                'patterns': [
                    r'(?i)\brdw\b[:\s]+(\d+\.?\d*)',
                    r'(?i)red\s+cell\s+dist[ribution]*\s+width[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 11.5, 'max': 14.5
            },
            
            # Differential Count
            'Neutrophils': {
                'patterns': [
                    r'(?i)neutrophil[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)\bneut\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 40, 'max': 70
            },
            'Lymphocytes': {
                'patterns': [
                    r'(?i)lymphocyte[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)\blymph\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 20, 'max': 40
            },
            'Monocytes': {
                'patterns': [
                    r'(?i)monocyte[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)\bmono\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 2, 'max': 8
            },
            'Eosinophils': {
                'patterns': [
                    r'(?i)eosinophil[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)\beos\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 1, 'max': 4
            },
            'Basophils': {
                'patterns': [
                    r'(?i)basophil[s]?[:\s]+(\d+\.?\d*)',
                    r'(?i)\bbaso\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 0, 'max': 1
            },
            
            # Chemistry
            'Glucose': {
                'patterns': [
                    r'(?i)glucose[:\s]+(\d+\.?\d*)',
                    r'(?i)blood\s+sugar[:\s]+(\d+\.?\d*)',
                    r'(?i)fasting\s+glucose[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mg/dL',
                'min': 70, 'max': 100
            },
            'Cholesterol': {
                'patterns': [
                    r'(?i)(?:total\s+)?cholesterol[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mg/dL',
                'min': 0, 'max': 200
            },
            'Creatinine': {
                'patterns': [
                    r'(?i)creatinine[:\s]+(\d+\.?\d*)',
                    r'(?i)serum\s+creatinine[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mg/dL',
                'min': 0.7, 'max': 1.3
            },
            'Urea': {
                'patterns': [
                    r'(?i)\burea\b[:\s]+(\d+\.?\d*)',
                    r'(?i)blood\s+urea[:\s]+(\d+\.?\d*)',
                    r'(?i)\bbun\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mg/dL',
                'min': 7, 'max': 20
            },
            
            # Liver Function
            'SGPT': {
                'patterns': [
                    r'(?i)\bsgpt\b[:\s]+(\d+\.?\d*)',
                    r'(?i)\balt\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'U/L',
                'min': 7, 'max': 56
            },
            'SGOT': {
                'patterns': [
                    r'(?i)\bsgot\b[:\s]+(\d+\.?\d*)',
                    r'(?i)\bast\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'U/L',
                'min': 10, 'max': 40
            },
            'Bilirubin': {
                'patterns': [
                    r'(?i)bilirubin[:\s]+(\d+\.?\d*)',
                    r'(?i)total\s+bilirubin[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mg/dL',
                'min': 0.1, 'max': 1.2
            },
            
            # Thyroid
            'TSH': {
                'patterns': [
                    r'(?i)\btsh\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mIU/L',
                'min': 0.4, 'max': 4.0
            },
            
            # Others
            'ESR': {
                'patterns': [
                    r'(?i)\besr\b[:\s]+(\d+\.?\d*)',
                ],
                'unit': 'mm/hr',
                'min': 0, 'max': 20
            },
            'HbA1c': {
                'patterns': [
                    r'(?i)hba1c[:\s]+(\d+\.?\d*)',
                    r'(?i)glycated\s+hemoglobin[:\s]+(\d+\.?\d*)',
                ],
                'unit': '%',
                'min': 4.0, 'max': 5.6
            },
        }
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse blood report text and extract parameters
        Only extracts when parameter name and value are clearly on same line
        """
        if not text or len(text.strip()) < 20:
            return {}
        
        parameters = {}
        lines = text.split('\n')
        
        # Process each line
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Try to extract each parameter from this line
            for param_name, config in self.parameters.items():
                if param_name in parameters:
                    continue  # Already found this parameter
                
                for pattern in config['patterns']:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            value = float(match.group(1))
                            
                            # Validate value is in reasonable range
                            min_val = config['min']
                            max_val = config['max']
                            
                            # Allow some tolerance (0.1x to 10x of expected range)
                            if min_val * 0.1 <= value <= max_val * 10:
                                # Determine status
                                if value < min_val:
                                    status = "LOW"
                                elif value > max_val:
                                    status = "HIGH"
                                else:
                                    status = "NORMAL"
                                
                                # Extract reference range from line if present
                                ref_range = self._extract_reference_range(line)
                                if not ref_range:
                                    ref_range = f"{min_val}-{max_val}"
                                
                                parameters[param_name] = {
                                    'value': value,
                                    'unit': config['unit'],
                                    'reference_range': ref_range,
                                    'status': status,
                                    'raw_text': line
                                }
                                break
                        except ValueError:
                            continue
                
                if param_name in parameters:
                    break
        
        return parameters
    
    def _extract_reference_range(self, line: str) -> Optional[str]:
        """Extract reference range from line if present"""
        # Look for patterns like "13.0-17.0" or "13.0 - 17.0"
        patterns = [
            r'(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, line)
            if len(matches) >= 1:
                # Take the last match (usually the reference range)
                match = matches[-1]
                return f"{match[0]}-{match[1]}"
        
        return None


def parse_enhanced_blood_report(text: str) -> Dict[str, Any]:
    """
    Main entry point for enhanced blood report parsing
    """
    parser = EnhancedBloodParser()
    return parser.parse(text)
