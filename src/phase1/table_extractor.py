import re
import csv
import io
from .phase1_extractor import SHARED_NOISE_PATTERNS


class MedicalTableExtractor:
    """Medical Table Extraction Agent - Faithful extraction only, no interpretation
    
    SIMPLIFIED - Uses shared noise patterns from phase1_extractor.py to avoid duplication.
    Primary extraction path uses phase1_extractor.Phase1MedicalImageExtractor.
    This class provides alternative table section extraction if needed."""
    
    def __init__(self):
        # USE SHARED NOISE PATTERNS from phase1_extractor
        self.noise_patterns = SHARED_NOISE_PATTERNS
        
        # Patterns to identify test names (anchors for table rows)
        self.test_name_patterns = [
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s+(\d+\.?\d*)',  # Test name followed by number
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s*:\s*(\d+\.?\d*)',  # Test name with colon
            r'^([A-Za-z][A-Za-z\s\(\)]{3,})\s+([A-Za-z]+)',  # Test name followed by text value
        ]
        
        # Method patterns
        self.method_patterns = [
            r'(?i)(calculated|electrical\s+impedance|vcs|immunoturbidimetry|photometry|flow\s+cytometry)',
            r'(?i)(automated|manual|enzymatic|colorimetric)',
        ]
    
    def is_noise_line(self, line):
        """Check if line is noise that should be ignored"""
        for pattern in self.noise_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def is_status_word(self, word):
        """Check if word is a status indicator, not a test name"""
        status_words = ['high', 'low', 'normal', 'abnormal', 'positive', 'negative', 'present', 'absent']
        return word.lower().strip() in status_words
    
    def extract_table_section(self, ocr_text):
        """Extract only the laboratory table section"""
        lines = ocr_text.split('\n')
        table_lines = []
        in_table_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious noise
            if self.is_noise_line(line):
                continue
            
            # Look for table start indicators
            if any(keyword in line.lower() for keyword in ['investigation', 'test', 'parameter', 'result', 'value']):
                in_table_section = True
                continue
            
            # Look for test names to identify table content
            if any(re.search(pattern, line) for pattern in self.test_name_patterns):
                in_table_section = True
            
            if in_table_section:
                # Stop at interpretation or footer sections
                if any(keyword in line.lower() for keyword in ['interpretation', 'conclusion', 'signature', 'end of report']):
                    break
                
                table_lines.append(line)
        
        return table_lines
    
    def is_status_word(self, word):
        """Check if word is a status indicator, not a test name"""
        status_words = ['high', 'low', 'normal', 'abnormal', 'positive', 'negative', 'present', 'absent']
        return word.lower().strip() in status_words
    
    def extract_method(self, text):
        """Extract method information if present"""
        for pattern in self.method_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def extract_to_csv(self, ocr_text):
        """Extract table data and return as CSV format
        
        NOTE: This is a secondary/legacy interface. For new code, use:
        from .phase1_extractor import Phase1MedicalImageExtractor
        extractor = Phase1MedicalImageExtractor()
        
        This method now delegates to phase1_extractor as the primary extraction path.
        """
        # Import here to avoid circular imports
        from .phase1_extractor import Phase1MedicalImageExtractor
        
        # Use primary extractor from phase1_extractor
        primary_extractor = Phase1MedicalImageExtractor()
        return primary_extractor.extract_to_csv(ocr_text)


def extract_medical_table(ocr_text):
    """Main function to extract medical table from OCR text
    
    DEPRECATED: Use phase1_extractor.Phase1MedicalImageExtractor instead.
    This is maintained for backward compatibility only.
    """
    extractor = MedicalTableExtractor()
    return extractor.extract_to_csv(ocr_text)