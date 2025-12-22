import re
import csv
import io


class MedicalTableExtractor:
    """Medical Table Extraction Agent - Faithful extraction only, no interpretation"""
    
    def __init__(self):
        # Patterns to identify noise that should be ignored
        self.noise_patterns = [
            r'(?i)(?:address|email|phone|tel|fax|mobile)',
            r'(?i)(?:patient\s+name|patient\s+id|registration)',
            r'(?i)(?:doctor|dr\.|physician|consultant)',
            r'(?i)(?:laboratory|lab\s+name|department)',
            r'(?i)(?:collected|received|reported|printed)',
            r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Dates
            r'\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?',  # Times
            r'(?i)(?:interpretation|conclusion|comment|note)',
            r'(?i)(?:signature|authorized|verified)',
            r'^[A-Z\s]{10,}$',  # All caps headers
        ]
        
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
    
    def merge_broken_lines(self, lines):
        """Merge broken lines that belong to the same test row"""
        merged_rows = []
        current_row = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new test (has test name pattern)
            is_new_test = False
            for pattern in self.test_name_patterns:
                if re.search(pattern, line):
                    is_new_test = True
                    break
            
            if is_new_test:
                # Save previous row if exists
                if current_row:
                    merged_rows.append(current_row)
                current_row = line
            else:
                # Continuation of current row
                if current_row:
                    current_row += " " + line
                else:
                    current_row = line
        
        # Add the last row
        if current_row:
            merged_rows.append(current_row)
        
        return merged_rows
    
    def extract_method(self, text):
        """Extract method information if present"""
        for pattern in self.method_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""
    
    def parse_table_row(self, row_text):
        """Parse a single table row into structured data"""
        # Try different parsing patterns
        patterns = [
            # Pattern 1: test_name value unit reference_range
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s+(\d+\.?\d*)\s+([A-Za-z/%]+)\s+(.+)$',
            
            # Pattern 2: test_name value unit
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s+(\d+\.?\d*)\s+([A-Za-z/%]+)(?:\s|$)',
            
            # Pattern 3: test_name : value unit reference_range
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s*:\s*(\d+\.?\d*)\s+([A-Za-z/%]+)\s+(.+)$',
            
            # Pattern 4: test_name : value
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s*:\s*(\d+\.?\d*)(?:\s|$)',
            
            # Pattern 5: test_name text_value
            r'^([A-Za-z][A-Za-z\s\(\)]+?)\s+([A-Za-z]+)(?:\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, row_text.strip())
            if match:
                test_name = match.group(1).strip()
                value = match.group(2).strip()
                
                # Skip if test name is actually a status word
                if self.is_status_word(test_name):
                    continue
                
                unit = ""
                reference_range = ""
                
                if len(match.groups()) > 2:
                    unit = match.group(3).strip()
                
                if len(match.groups()) > 3:
                    reference_range = match.group(4).strip()
                    
                    # Check if unit is actually part of reference range
                    if re.match(r'\d+\.?\d*\s*[-–]\s*\d+\.?\d*', unit):
                        reference_range = unit + " " + reference_range
                        unit = ""
                
                # Extract method
                method = self.extract_method(row_text)
                
                return {
                    'test_name': test_name,
                    'value': value,
                    'unit': unit,
                    'reference_range': reference_range,
                    'method': method,
                    'raw_text': row_text
                }
        
        return None
    
    def extract_to_csv(self, ocr_text):
        """Extract table data and return as CSV format"""
        # Step 1: Extract table section
        table_lines = self.extract_table_section(ocr_text)
        
        # Step 2: Merge broken lines
        merged_rows = self.merge_broken_lines(table_lines)
        
        # Step 3: Parse each row
        extracted_data = []
        for row_text in merged_rows:
            parsed_row = self.parse_table_row(row_text)
            if parsed_row:
                extracted_data.append(parsed_row)
        
        # Step 4: Generate CSV
        if not extracted_data:
            # Return empty CSV with headers
            return "test_name,value,unit,reference_range,method,raw_text\n"
        
        # Create CSV string
        output = io.StringIO()
        fieldnames = ['test_name', 'value', 'unit', 'reference_range', 'method', 'raw_text']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in extracted_data:
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content


def extract_medical_table(ocr_text):
    """Main function to extract medical table from OCR text"""
    extractor = MedicalTableExtractor()
    return extractor.extract_to_csv(ocr_text)