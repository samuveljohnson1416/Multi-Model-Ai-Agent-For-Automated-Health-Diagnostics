"""
Core module for blood report analysis system.
Contains OCR, parsing, validation, interpretation, and AI components.
"""

from .ocr_engine import extract_text_from_file
from .parser import parse_blood_report
from .enhanced_blood_parser import parse_enhanced_blood_report
from .validator import validate_parameters
from .interpreter import interpret_results
from .multi_report_manager import MultiReportManager, get_or_create_session
from .multi_report_detector import detect_multiple_reports
from .multi_report_qa_assistant import MultiReportQAAssistant, create_multi_report_qa_assistant
from .enhanced_ai_agent import EnhancedAIAgent, create_enhanced_ai_agent

__all__ = [
    'extract_text_from_file',
    'parse_blood_report',
    'parse_enhanced_blood_report',
    'validate_parameters',
    'interpret_results',
    'MultiReportManager',
    'get_or_create_session',
    'detect_multiple_reports',
    'MultiReportQAAssistant',
    'create_multi_report_qa_assistant',
    'EnhancedAIAgent',
    'create_enhanced_ai_agent',
]
