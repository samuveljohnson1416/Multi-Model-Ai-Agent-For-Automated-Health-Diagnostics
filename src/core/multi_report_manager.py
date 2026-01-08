"""
Multi-Report Manager
Manages analysis pipeline for multiple blood reports with data isolation
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .multi_report_detector import detect_multiple_reports
from core.parser import parse_blood_report
from core.validator import validate_parameters
from core.interpreter import interpret_results
from utils.csv_converter import json_to_ml_csv
from phase2.phase2_integration_safe import integrate_phase2_analysis


class MultiReportManager:
    """
    Manages multiple blood reports with complete data isolation and comparative analysis
    """
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.reports = {}  # report_id -> report_data
        self.analysis_results = {}  # report_id -> analysis_results
        self.comparison_results = None
        self.created_at = datetime.now()
    
    def process_document(self, raw_text: str, filename: str = "document") -> Dict[str, Any]:
        """
        Process a document that may contain multiple reports
        
        Args:
            raw_text: Raw extracted text from document
            filename: Original filename
            
        Returns:
            Processing results with report count and analysis status
        """
        # Step 1: Detect multiple reports
        detected_reports = detect_multiple_reports(raw_text)
        
        if not detected_reports:
            return {
                'status': 'error',
                'message': 'No valid medical reports detected in document',
                'report_count': 0,
                'reports': []
            }
        
        # Step 2: Process each report independently
        processing_results = []
        
        for report_data in detected_reports:
            report_id = report_data['report_id']
            
            try:
                # Process single report through complete pipeline
                result = self._process_single_report(report_data, filename)
                
                # Store in session memory
                self.reports[report_id] = report_data
                self.analysis_results[report_id] = result
                
                processing_results.append({
                    'report_id': report_id,
                    'status': 'success',
                    'metadata': report_data['metadata'],
                    'parameters_count': len(result.get('validated_data', {})),
                    'has_ai_analysis': result.get('phase2_available', False)
                })
                
            except Exception as e:
                processing_results.append({
                    'report_id': report_id,
                    'status': 'error',
                    'error': str(e),
                    'metadata': report_data['metadata']
                })
        
        # Step 3: Enable comparison mode if multiple valid reports
        valid_reports = [r for r in processing_results if r['status'] == 'success']
        
        if len(valid_reports) > 1:
            try:
                self.comparison_results = self._generate_comparison_analysis()
            except Exception as e:
                # Comparison failed, but individual reports are still valid
                pass
        
        return {
            'status': 'success',
            'session_id': self.session_id,
            'report_count': len(detected_reports),
            'valid_reports': len(valid_reports),
            'comparison_available': self.comparison_results is not None,
            'reports': processing_results,
            'filename': filename,
            'processed_at': datetime.now().isoformat()
        }
    
    def _process_single_report(self, report_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """
        Process a single report through the complete analysis pipeline
        """
        content = report_data['content']
        report_id = report_data['report_id']
        
        # Step 1: Parse blood report
        parsed_data = parse_blood_report(content)
        
        if not parsed_data:
            # Be more lenient - create a basic structure even if no parameters detected
            parsed_data = {
                "raw_content": {
                    "value": "Content detected but no structured parameters found",
                    "unit": "text",
                    "reference_range": "N/A",
                    "status": "UNKNOWN",
                    "confidence": 0.5
                }
            }
        
        # Step 2: Validate parameters
        validated_data = validate_parameters(parsed_data)
        
        if not validated_data:
            # Use the parsed data as validated data if validation fails
            validated_data = parsed_data
        
        # Step 3: Interpret results
        try:
            interpretation = interpret_results(validated_data)
        except Exception as e:
            # Create basic interpretation if it fails
            interpretation = {
                "summary": {
                    "total_parameters": len(validated_data),
                    "normal": 0,
                    "low": 0,
                    "high": 0
                },
                "abnormal_parameters": [],
                "status": "analysis_incomplete",
                "message": f"Basic processing completed for {report_id}"
            }
        
        # Step 4: Convert to ML CSV for Phase-2
        # Create a mock ingestion result for CSV conversion
        mock_ingestion = json.dumps({
            "medical_parameters": [
                {
                    "name": param_name,
                    "value": param_data.get("value", ""),
                    "unit": param_data.get("unit", ""),
                    "reference_range": param_data.get("reference_range", ""),
                    "status": param_data.get("status", "UNKNOWN"),
                    "confidence": param_data.get("confidence", "0.95")
                }
                for param_name, param_data in validated_data.items()
            ],
            "raw_text": content
        })
        
        try:
            ml_csv = json_to_ml_csv(mock_ingestion)
        except Exception as e:
            ml_csv = f"# CSV conversion failed: {str(e)}\n# Raw content length: {len(content)} characters"
        
        # Step 5: Phase-2 AI Analysis (if available)
        phase2_result = None
        phase2_available = False
        
        try:
            # Extract demographics from metadata or content
            metadata = report_data.get('metadata', {})
            age = self._extract_age_from_content(content)
            gender = self._extract_gender_from_content(content)
            
            phase2_result = integrate_phase2_analysis(ml_csv, age=age, gender=gender)
            
            if phase2_result and phase2_result.get("phase2_summary", {}).get("available", False):
                phase2_available = True
                
        except Exception as e:
            # Phase-2 analysis failed, continue with basic analysis
            pass
        
        return {
            'report_id': report_id,
            'filename': filename,
            'metadata': report_data['metadata'],
            'parsed_data': parsed_data,
            'validated_data': validated_data,
            'interpretation': interpretation,
            'ml_csv': ml_csv,
            'phase2_result': phase2_result,
            'phase2_available': phase2_available,
            'content': content,
            'processed_at': datetime.now().isoformat()
        }
    
    def _extract_age_from_content(self, content: str) -> Optional[int]:
        """Extract age from report content"""
        import re
        
        age_patterns = [
            r'(?i)age\s*:?\s*(\d{1,3})\s*(?:years?|yrs?|y)?',
            r'(?i)(\d{1,3})\s*(?:years?|yrs?|y)\s*(?:old)?',
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, content)
            if match:
                age = int(match.group(1))
                if 0 <= age <= 120:
                    return age
        
        return None
    
    def _extract_gender_from_content(self, content: str) -> Optional[str]:
        """Extract gender from report content"""
        import re
        
        gender_patterns = [
            r'(?i)(?:sex|gender)\s*:?\s*(male|female|m|f)\b',
            r'(?i)\b(male|female)\b',
            r'(?i)\b(mr|mrs|ms|miss)\b',
        ]
        
        for pattern in gender_patterns:
            match = re.search(pattern, content)
            if match:
                gender_text = match.group(1).lower()
                
                if gender_text in ['male', 'm', 'mr']:
                    return 'Male'
                elif gender_text in ['female', 'f', 'mrs', 'ms', 'miss']:
                    return 'Female'
        
        return None
    
    def _generate_comparison_analysis(self) -> Dict[str, Any]:
        """
        Generate comparative analysis between multiple reports
        """
        if len(self.analysis_results) < 2:
            return None
        
        # Get all report IDs sorted by date or order
        report_ids = sorted(self.analysis_results.keys())
        
        # Find common parameters across all reports
        common_parameters = self._find_common_parameters()
        
        if not common_parameters:
            return {
                'status': 'no_common_parameters',
                'message': 'No common parameters found across reports for comparison'
            }
        
        # Generate parameter comparisons
        parameter_comparisons = {}
        
        for param_name in common_parameters:
            comparison = self._compare_parameter_across_reports(param_name, report_ids)
            if comparison:
                parameter_comparisons[param_name] = comparison
        
        # Generate trend analysis
        trend_analysis = self._analyze_trends(parameter_comparisons, report_ids)
        
        # Generate summary
        summary = self._generate_comparison_summary(parameter_comparisons, trend_analysis)
        
        return {
            'status': 'success',
            'report_ids': report_ids,
            'common_parameters': list(common_parameters),
            'parameter_comparisons': parameter_comparisons,
            'trend_analysis': trend_analysis,
            'summary': summary,
            'generated_at': datetime.now().isoformat()
        }
    
    def _find_common_parameters(self) -> set:
        """Find parameters that exist in all reports"""
        if not self.analysis_results:
            return set()
        
        # Start with parameters from first report
        first_report = list(self.analysis_results.values())[0]
        common_params = set(first_report['validated_data'].keys())
        
        # Intersect with parameters from other reports
        for result in list(self.analysis_results.values())[1:]:
            report_params = set(result['validated_data'].keys())
            common_params = common_params.intersection(report_params)
        
        return common_params
    
    def _compare_parameter_across_reports(self, param_name: str, report_ids: List[str]) -> Dict[str, Any]:
        """Compare a single parameter across multiple reports"""
        values = []
        
        for report_id in report_ids:
            result = self.analysis_results[report_id]
            param_data = result['validated_data'].get(param_name, {})
            
            try:
                value = float(param_data.get('value', 0))
                unit = param_data.get('unit', '')
                status = param_data.get('status', 'UNKNOWN')
                
                values.append({
                    'report_id': report_id,
                    'value': value,
                    'unit': unit,
                    'status': status,
                    'metadata': self.reports[report_id]['metadata']
                })
            except (ValueError, TypeError):
                # Non-numeric value, skip comparison
                continue
        
        if len(values) < 2:
            return None
        
        # Calculate changes
        changes = []
        for i in range(1, len(values)):
            prev_val = values[i-1]['value']
            curr_val = values[i]['value']
            
            if prev_val != 0:
                percent_change = ((curr_val - prev_val) / prev_val) * 100
            else:
                percent_change = 0
            
            change_type = 'stable'
            if percent_change > 5:
                change_type = 'increase'
            elif percent_change < -5:
                change_type = 'decrease'
            
            changes.append({
                'from_report': values[i-1]['report_id'],
                'to_report': values[i]['report_id'],
                'from_value': prev_val,
                'to_value': curr_val,
                'absolute_change': curr_val - prev_val,
                'percent_change': round(percent_change, 2),
                'change_type': change_type
            })
        
        return {
            'parameter_name': param_name,
            'values': values,
            'changes': changes,
            'unit': values[0]['unit'] if values else '',
            'trend': self._determine_overall_trend(changes)
        }
    
    def _determine_overall_trend(self, changes: List[Dict[str, Any]]) -> str:
        """Determine overall trend from changes"""
        if not changes:
            return 'stable'
        
        increases = sum(1 for c in changes if c['change_type'] == 'increase')
        decreases = sum(1 for c in changes if c['change_type'] == 'decrease')
        
        if increases > decreases:
            return 'increasing'
        elif decreases > increases:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_trends(self, parameter_comparisons: Dict[str, Any], report_ids: List[str]) -> Dict[str, Any]:
        """Analyze overall trends across all parameters"""
        trends = {
            'improving': [],
            'worsening': [],
            'stable': [],
            'mixed': []
        }
        
        for param_name, comparison in parameter_comparisons.items():
            trend = comparison['trend']
            
            # Determine if trend is good or bad based on parameter
            if trend == 'stable':
                trends['stable'].append(param_name)
            elif self._is_improvement(param_name, trend):
                trends['improving'].append(param_name)
            elif self._is_worsening(param_name, trend):
                trends['worsening'].append(param_name)
            else:
                trends['mixed'].append(param_name)
        
        return {
            'trends': trends,
            'total_parameters': len(parameter_comparisons),
            'report_span': f"{report_ids[0]} to {report_ids[-1]}"
        }
    
    def _is_improvement(self, param_name: str, trend: str) -> bool:
        """Determine if trend represents improvement for given parameter"""
        # This is a simplified heuristic - in practice, this would be more sophisticated
        param_lower = param_name.lower()
        
        if 'cholesterol' in param_lower and trend == 'decreasing':
            return True
        elif 'glucose' in param_lower and trend == 'decreasing':
            return True
        elif 'hemoglobin' in param_lower and trend == 'increasing':
            return True
        
        return False
    
    def _is_worsening(self, param_name: str, trend: str) -> bool:
        """Determine if trend represents worsening for given parameter"""
        param_lower = param_name.lower()
        
        if 'cholesterol' in param_lower and trend == 'increasing':
            return True
        elif 'glucose' in param_lower and trend == 'increasing':
            return True
        elif 'hemoglobin' in param_lower and trend == 'decreasing':
            return True
        
        return False
    
    def _generate_comparison_summary(self, parameter_comparisons: Dict[str, Any], trend_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate high-level comparison summary"""
        trends = trend_analysis['trends']
        
        return {
            'total_reports': len(self.analysis_results),
            'parameters_compared': len(parameter_comparisons),
            'improving_parameters': len(trends['improving']),
            'worsening_parameters': len(trends['worsening']),
            'stable_parameters': len(trends['stable']),
            'overall_assessment': self._get_overall_assessment(trends),
            'key_changes': self._get_key_changes(parameter_comparisons)
        }
    
    def _get_overall_assessment(self, trends: Dict[str, List[str]]) -> str:
        """Get overall health trend assessment"""
        improving = len(trends['improving'])
        worsening = len(trends['worsening'])
        
        if improving > worsening:
            return 'improving'
        elif worsening > improving:
            return 'declining'
        else:
            return 'stable'
    
    def _get_key_changes(self, parameter_comparisons: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get most significant parameter changes"""
        key_changes = []
        
        for param_name, comparison in parameter_comparisons.items():
            changes = comparison.get('changes', [])
            
            for change in changes:
                if abs(change['percent_change']) > 10:  # Significant change threshold
                    key_changes.append({
                        'parameter': param_name,
                        'change_type': change['change_type'],
                        'percent_change': change['percent_change'],
                        'from_report': change['from_report'],
                        'to_report': change['to_report']
                    })
        
        # Sort by absolute percent change
        key_changes.sort(key=lambda x: abs(x['percent_change']), reverse=True)
        
        return key_changes[:5]  # Top 5 most significant changes
    
    def get_report_data(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis data for a specific report"""
        return self.analysis_results.get(report_id)
    
    def get_all_reports(self) -> Dict[str, Any]:
        """Get all reports and analysis results"""
        return {
            'session_id': self.session_id,
            'reports': self.reports,
            'analysis_results': self.analysis_results,
            'comparison_results': self.comparison_results,
            'created_at': self.created_at.isoformat()
        }
    
    def get_comparison_results(self) -> Optional[Dict[str, Any]]:
        """Get comparison analysis results"""
        return self.comparison_results


# Global session storage (in production, this would be a proper session store)
_session_storage = {}


def get_or_create_session(session_id: str = None) -> MultiReportManager:
    """Get existing session or create new one"""
    if session_id and session_id in _session_storage:
        return _session_storage[session_id]
    
    manager = MultiReportManager()
    _session_storage[manager.session_id] = manager
    return manager


def cleanup_old_sessions(max_age_hours: int = 24):
    """Cleanup old sessions to prevent memory leaks"""
    current_time = datetime.now()
    
    expired_sessions = []
    for session_id, manager in _session_storage.items():
        age_hours = (current_time - manager.created_at).total_seconds() / 3600
        if age_hours > max_age_hours:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del _session_storage[session_id]