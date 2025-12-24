import re
import csv
import io


class Phase1MedicalImageExtractor:
    """Phase-1 Medical Image Extraction Agent - Image-aware OCR reconstruction"""
    
    def __init__(self):
        # Valid laboratory test anchors (case-insensitive)
        self.valid_anchors = [
            'hemoglobin', 'total rbc count', 'rbc count', 'pcv', 'packed cell volume',
            'mcv', 'mch', 'mchc', 'rdw', 'total wbc count', 'wbc count',
            'neutrophils', 'lymphocytes', 'eosinophils', 'monocytes', 'basophils',
            'platelet count', 'platelets'
        ]
        
        # OCR noise patterns to completely ignore
        self.noise_patterns = [
            r'(?i)(?:address|location|phone|tel|mobile|email)',
            r'(?i)(?:dr\.|doctor|physician|pathologist|consultant)',
            r'(?i)(?:laboratory|lab\s+name|hospital|clinic)',
            r'(?i)(?:page|pg)\s*\d+',
            r'(?i)(?:qr\s*code|barcode)',
            r'(?i)(?:interpretation|conclusion|comment|remarks)',
            r'(?i)(?:signature|authorized|verified|approved)',
            r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',  # Dates
            r'\d{1,2}:\d{2}(?::\d{2})?',  # Times
            r'^[A-Z\s]{15,}$',  # Long all-caps headers
            r'(?i)(?:high|low|normal|abnormal)$',  # Isolated status words
        ]
        
        # Method patterns that may appear on separate lines
        self.method_patterns = [
            r'(?i)(calculated)',
            r'(?i)(electrical\s+impedance)',
            r'(?i)(vcs)',
            r'(?i)(immunoturbidimetry)',
            r'(?i)(photometry)',
            r'(?i)(flow\s+cytometry)',
        ]
        
        # Unit patterns
        self.unit_patterns = [
            r'(?i)(g/dl|gm/dl|g%)',
            r'(?i)(mill/cumm|million/cumm)',
            r'(?i)(thou/cumm|thousand/cumm)',
            r'(?i)(/cumm|cells/cumm)',
            r'(?i)(fl|pg|%|percent)',
        ]
    
    def is_ocr_failure(self, ocr_text):
        """Detect OCR failure conditions"""
        if not ocr_text or len(ocr_text.strip()) < 10:
            return True
        
        # Check if text contains any numbers (medical reports should have values)
        if not re.search(r'\d', ocr_text):
            return True
        
        # Check if any valid anchors are present
        text_lower = ocr_text.lower()
        has_anchor = any(anchor in text_lower for anchor in self.valid_anchors)
        
        return not has_anchor
    
    def is_noise_line(self, line):
        """Check if line is OCR noise that should be ignored"""
        for pattern in self.noise_patterns:
            if re.search(pattern, line):
                return True
        return False
    
    def find_anchor_in_line(self, line):
        """Find valid laboratory test anchor in line"""
        line_lower = line.lower().strip()
        
        for anchor in self.valid_anchors:
            if anchor in line_lower:
                # Verify it's not just a substring match
                # Look for word boundaries or start of line
                pattern = r'(?:^|\W)' + re.escape(anchor) + r'(?:\W|$)'
                if re.search(pattern, line_lower):
                    return anchor
        
        return None
    
    def extract_value_from_text(self, text):
        """Extract numeric value from text"""
        # Look for decimal numbers first, then integers
        decimal_match = re.search(r'\b(\d+\.\d+)\b', text)
        if decimal_match:
            return decimal_match.group(1)
        
        integer_match = re.search(r'\b(\d+)\b', text)
        if integer_match:
            return integer_match.group(1)
        
        return ""
    
    def extract_unit_from_text(self, text):
        """Extract unit from text"""
        for pattern in self.unit_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def extract_reference_range_from_text(self, text):
        """Extract reference range from text"""
        # Look for patterns like "13.0 - 17.0" or "4.5-5.5"
        range_patterns = [
            r'(\d+\.?\d*\s*[-–—]\s*\d+\.?\d*)',
            r'(\d+\.?\d*\s*to\s*\d+\.?\d*)',
        ]
        
        for pattern in range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_method_from_text(self, text):
        """Extract method from text"""
        for pattern in self.method_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def reconstruct_table_rows(self, ocr_text):
        """Reconstruct ALL table rows - NEVER skip any detected test"""
        lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
        
        # Filter out noise lines
        clean_lines = []
        for line in lines:
            if not self.is_noise_line(line):
                clean_lines.append(line)
        
        if not clean_lines:
            return []
        
        # Find ALL test names in the entire OCR text
        all_found_tests = self.find_all_test_names_in_text(ocr_text)
        
        if not all_found_tests:
            return []
        
        # Group lines into logical rows for ALL found tests
        rows = []
        processed_anchors = set()
        
        for test_info in all_found_tests:
            anchor = test_info['anchor']
            anchor_line = test_info['line']
            
            # Skip if we already processed this exact anchor
            if anchor in processed_anchors:
                continue
            
            processed_anchors.add(anchor)
            
            # Find the anchor line in clean_lines
            anchor_line_index = -1
            for i, clean_line in enumerate(clean_lines):
                if anchor.lower() in clean_line.lower():
                    anchor_line_index = i
                    break
            
            # Collect lines for this test
            row_lines = []
            
            if anchor_line_index >= 0:
                # Start with the anchor line
                row_lines.append(clean_lines[anchor_line_index])
                
                # Look for continuation lines (next few lines that might belong to this test)
                for j in range(anchor_line_index + 1, min(anchor_line_index + 4, len(clean_lines))):
                    next_line = clean_lines[j]
                    
                    # Stop if we hit another test name
                    if any(other_anchor in next_line.lower() for other_anchor in self.valid_anchors):
                        break
                    
                    # Add line if it contains relevant data
                    if (re.search(r'\d', next_line) or 
                        any(method in next_line.lower() for method in ['calculated', 'electrical', 'vcs', 'immunoturbidimetry'])):
                        row_lines.append(next_line)
            else:
                # Fallback: use the original line from found tests
                row_lines.append(anchor_line)
            
            # CRITICAL: Always add the row, even if minimal data
            rows.append({
                'anchor': anchor,
                'lines': row_lines if row_lines else [anchor_line]
            })
        
        return rows
    
    def find_all_test_names_in_text(self, ocr_text):
        """Find ALL occurrences of valid test names in OCR text"""
        text_lower = ocr_text.lower()
        found_tests = []
        
        # Search for each valid anchor in the entire text
        for anchor in self.valid_anchors:
            # Find all occurrences of this anchor
            pattern = r'(?:^|\W)' + re.escape(anchor) + r'(?:\W|$)'
            matches = list(re.finditer(pattern, text_lower))
            
            for match in matches:
                # Find the line containing this match
                lines = ocr_text.split('\n')
                char_count = 0
                
                for line_num, line in enumerate(lines):
                    line_start = char_count
                    line_end = char_count + len(line)
                    
                    if line_start <= match.start() <= line_end:
                        found_tests.append({
                            'anchor': anchor,
                            'line': line.strip(),
                            'line_number': line_num
                        })
                        break
                    
                    char_count += len(line) + 1  # +1 for newline
        
        return found_tests
    
    def extract_row_data(self, row_info):
        """Extract structured data from a reconstructed row"""
        anchor = row_info['anchor']
        lines = row_info['lines']
        
        # Combine all lines for this row
        combined_text = ' '.join(lines)
        
        # Extract fields
        test_name = anchor.title()  # Normalize anchor to title case
        value = self.extract_value_from_text(combined_text)
        unit = self.extract_unit_from_text(combined_text)
        reference_range = self.extract_reference_range_from_text(combined_text)
        method = self.extract_method_from_text(combined_text)
        raw_text = combined_text
        
        return {
            'test_name': test_name,
            'value': value,
            'unit': unit,
            'reference_range': reference_range,
            'method': method,
            'raw_text': raw_text
        }
    
    def extract_to_csv(self, ocr_text):
        """Main extraction method - returns CSV format only"""
        
        # Check for OCR failure
        if self.is_ocr_failure(ocr_text):
            # Return empty CSV with headers
            return "test_name,value,unit,reference_range,method,raw_text\n"
        
        # Reconstruct table rows using image-aware reasoning
        reconstructed_rows = self.reconstruct_table_rows(ocr_text)
        
        if not reconstructed_rows:
            # No valid rows found - return empty CSV with headers
            return "test_name,value,unit,reference_range,method,raw_text\n"
        
        # Extract data from each row - COMPLETENESS RULE: Include ALL detected tests
        extracted_data = []
        for row_info in reconstructed_rows:
            row_data = self.extract_row_data(row_info)
            
            # ALWAYS include if we have a test name (completeness rule)
            if row_data['test_name']:
                # Fill missing fields with "NA" for ML compatibility
                if not row_data['value']:
                    row_data['value'] = 'NA'
                if not row_data['unit']:
                    row_data['unit'] = 'NA'
                if not row_data['reference_range']:
                    row_data['reference_range'] = 'NA'
                if not row_data['method']:
                    row_data['method'] = 'NA'
                
                extracted_data.append(row_data)
        
        # Generate CSV output
        if not extracted_data:
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


def extract_phase1_medical_image(ocr_text):
    """Phase-1 Medical Image Extraction - Main entry point"""
    extractor = Phase1MedicalImageExtractor()
    return extractor.extract_to_csv(ocr_text)