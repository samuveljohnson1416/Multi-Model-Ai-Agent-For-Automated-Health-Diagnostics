"""
Multi-Report Detection System
Detects and separates multiple blood reports within a single document
"""

import re
import json
from typing import List, Dict, Any, Tuple
from datetime import datetime


class MultiReportDetector:
    """
    Detects multiple blood reports within a single document and separates them
    """
    
    def __init__(self):
        # Patterns to identify report boundaries
        self.report_header_patterns = [
            r'(?i)(?:blood|lab|laboratory|medical)\s+(?:test|report|analysis)',
            r'(?i)(?:complete|comprehensive)\s+(?:blood|metabolic)\s+panel',
            r'(?i)(?:patient|report)\s+(?:id|number|name)\s*:',
            r'(?i)(?:test|collection|sample)\s+date\s*:',
            r'(?i)(?:laboratory|lab)\s+(?:name|report)',
            r'(?i)(?:pathology|diagnostic)\s+report',
            r'(?i)(?:reference|normal)\s+(?:range|values)',
            r'(?i)(?:hemoglobin|glucose|cholesterol|rbc|wbc)',
        ]
        
        # Patient metadata patterns
        self.patient_patterns = [
            r'(?i)patient\s+(?:name|id)\s*:\s*([^\n]+)',
            r'(?i)(?:mr\.|mrs\.|ms\.|dr\.)\s+([A-Za-z\s]+)',
            r'(?i)name\s*:\s*([A-Za-z\s]+)',
            r'(?i)id\s*:\s*([A-Za-z0-9\-]+)',
        ]
        
        # Date patterns for report separation
        self.date_patterns = [
            r'(?i)(?:test|collection|sample|report)\s+date\s*:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(?i)date\s*:\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
        ]
        
        # Page break indicators
        self.page_break_patterns = [
            r'(?i)page\s+\d+',
            r'(?i)--- page \d+ ---',
            r'(?i)end of report',
            r'(?i)new report',
            r'\f',  # Form feed character
        ]
    
    def detect_multiple_reports(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect and separate multiple reports in the given text
        
        Returns:
            List of report dictionaries with metadata and content
        """
        if not text or len(text.strip()) < 50:
            return []
        
        # Step 1: Find potential report boundaries
        boundaries = self._find_report_boundaries(text)
        
        if len(boundaries) <= 1:
            # Single report detected
            return [{
                'report_id': 'Report_1',
                'content': text,
                'start_pos': 0,
                'end_pos': len(text),
                'metadata': self._extract_metadata(text),
                'confidence': 0.95
            }]
        
        # Step 2: Split text into separate reports
        reports = []
        for i, boundary in enumerate(boundaries):
            report_id = f"Report_{i + 1}"
            
            # Determine content boundaries
            start_pos = boundary['position']
            end_pos = boundaries[i + 1]['position'] if i + 1 < len(boundaries) else len(text)
            
            content = text[start_pos:end_pos].strip()
            
            if len(content) > 50:  # Minimum content threshold
                metadata = self._extract_metadata(content)
                
                reports.append({
                    'report_id': report_id,
                    'content': content,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'metadata': metadata,
                    'confidence': boundary['confidence']
                })
        
        return reports
    
    def _find_report_boundaries(self, text: str) -> List[Dict[str, Any]]:
        """Find potential boundaries between reports"""
        boundaries = []
        lines = text.split('\n')
        
        # Always include the start of the document
        boundaries.append({
            'position': 0,
            'type': 'document_start',
            'confidence': 1.0,
            'line_number': 0
        })
        
        current_pos = 0
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                current_pos += len(line) + 1
                continue
            
            # Check for report header patterns
            header_confidence = self._check_header_patterns(line_stripped)
            if header_confidence > 0.7:
                boundaries.append({
                    'position': current_pos,
                    'type': 'header_pattern',
                    'confidence': header_confidence,
                    'line_number': line_num,
                    'content': line_stripped
                })
            
            # Check for patient metadata changes
            patient_confidence = self._check_patient_patterns(line_stripped)
            if patient_confidence > 0.8:
                boundaries.append({
                    'position': current_pos,
                    'type': 'patient_metadata',
                    'confidence': patient_confidence,
                    'line_number': line_num,
                    'content': line_stripped
                })
            
            # Check for date patterns
            date_confidence = self._check_date_patterns(line_stripped)
            if date_confidence > 0.6:
                boundaries.append({
                    'position': current_pos,
                    'type': 'date_pattern',
                    'confidence': date_confidence,
                    'line_number': line_num,
                    'content': line_stripped
                })
            
            # Check for page breaks
            page_confidence = self._check_page_break_patterns(line_stripped)
            if page_confidence > 0.9:
                boundaries.append({
                    'position': current_pos,
                    'type': 'page_break',
                    'confidence': page_confidence,
                    'line_number': line_num,
                    'content': line_stripped
                })
            
            current_pos += len(line) + 1
        
        # Remove duplicate boundaries and sort by position
        unique_boundaries = []
        seen_positions = set()
        
        for boundary in sorted(boundaries, key=lambda x: x['position']):
            if boundary['position'] not in seen_positions:
                unique_boundaries.append(boundary)
                seen_positions.add(boundary['position'])
        
        # Filter boundaries that are too close together (within 100 characters)
        filtered_boundaries = [unique_boundaries[0]]  # Always keep the first
        
        for boundary in unique_boundaries[1:]:
            if boundary['position'] - filtered_boundaries[-1]['position'] > 100:
                filtered_boundaries.append(boundary)
        
        return filtered_boundaries
    
    def _check_header_patterns(self, line: str) -> float:
        """Check if line matches report header patterns"""
        matches = 0
        total_patterns = len(self.report_header_patterns)
        
        for pattern in self.report_header_patterns:
            if re.search(pattern, line):
                matches += 1
        
        return matches / total_patterns
    
    def _check_patient_patterns(self, line: str) -> float:
        """Check if line contains patient metadata"""
        for pattern in self.patient_patterns:
            if re.search(pattern, line):
                return 0.9
        return 0.0
    
    def _check_date_patterns(self, line: str) -> float:
        """Check if line contains date information"""
        for pattern in self.date_patterns:
            if re.search(pattern, line):
                return 0.8
        return 0.0
    
    def _check_page_break_patterns(self, line: str) -> float:
        """Check if line indicates a page break"""
        for pattern in self.page_break_patterns:
            if re.search(pattern, line):
                return 0.95
        return 0.0
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from report content"""
        metadata = {
            'patient_name': None,
            'patient_id': None,
            'test_date': None,
            'report_date': None,
            'lab_name': None,
            'page_number': None
        }
        
        lines = content.split('\n')[:20]  # Check first 20 lines for metadata
        
        for line in lines:
            line_stripped = line.strip()
            
            # Extract patient name
            for pattern in self.patient_patterns:
                match = re.search(pattern, line_stripped)
                if match and not metadata['patient_name']:
                    metadata['patient_name'] = match.group(1).strip()
                    break
            
            # Extract dates
            for pattern in self.date_patterns:
                match = re.search(pattern, line_stripped)
                if match and not metadata['test_date']:
                    metadata['test_date'] = match.group(1).strip()
                    break
            
            # Extract lab name
            lab_patterns = [
                r'(?i)(?:laboratory|lab)\s+name\s*:\s*([^\n]+)',
                r'(?i)([A-Za-z\s]+(?:laboratory|lab|medical center|hospital))',
            ]
            
            for pattern in lab_patterns:
                match = re.search(pattern, line_stripped)
                if match and not metadata['lab_name']:
                    metadata['lab_name'] = match.group(1).strip()
                    break
            
            # Extract page number
            page_match = re.search(r'(?i)page\s+(\d+)', line_stripped)
            if page_match and not metadata['page_number']:
                metadata['page_number'] = int(page_match.group(1))
        
        return metadata
    
    def validate_reports(self, reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate detected reports and filter out invalid ones"""
        valid_reports = []
        
        for report in reports:
            content = report['content']
            
            # Very lenient validation - accept almost any content
            content_stripped = content.strip()
            
            # Check minimum content length (very lenient)
            if len(content_stripped) < 20:  # Reduced from 50 to 20
                continue
            
            # Accept if content has any text and numbers
            has_text = bool(re.search(r'[a-zA-Z]{2,}', content))
            has_numbers = bool(re.search(r'\d', content))
            
            # Very lenient - accept if we have either text OR numbers
            if has_text or has_numbers:
                valid_reports.append(report)
                continue
            
            # Last resort - if content is reasonably long, accept it anyway
            if len(content_stripped) >= 100:
                valid_reports.append(report)
        
        return valid_reports


def detect_multiple_reports(text: str) -> List[Dict[str, Any]]:
    """
    Convenience function to detect multiple reports in text
    
    Args:
        text: Raw text from document
        
    Returns:
        List of detected reports with metadata
    """
    detector = MultiReportDetector()
    reports = detector.detect_multiple_reports(text)
    return detector.validate_reports(reports)