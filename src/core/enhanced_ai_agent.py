"""
Simplified AI Agent - Report Q&A WRAPPER ONLY
==============================================

⚠️ CRITICAL DESIGN:
This agent ONLY provides Q&A based on analyzed report data.
No intent inference, no workflow execution, no medical analysis.

All medical analysis is performed elsewhere:
- src/core/medical_logic.py: Rule-based parameter classification
- src/phase2/phase2_orchestrator.py: Rule-based decision making
- src/core/interpreter.py: Rule-based result synthesis

This agent:
1. Stores analyzed report data
2. Answers user questions based on that data
3. Uses Q&A assistant for LLM explanations only

No other complexity.
"""

from typing import Dict, Any

from .qa_assistant import BloodReportQAAssistant


class EnhancedAIAgent:
    """
    Report Q&A Wrapper - Responses Based Only on Analyzed Data
    
    ⚠️ DESIGN PRINCIPLE:
    Responses come from analyzed report data.
    No intent inference. No workflow execution. No complexity.
    
    If report data exists → answer based on it via Q&A assistant
    If no report data → ask user to upload
    
    That's all this agent does.
    """
    
    def __init__(self):
        """Initialize with Q&A assistant"""
        self.qa_assistant = BloodReportQAAssistant()
        self.analysis_data = {}  # Store current analysis data only
    
    def load_report_data(self, analysis_result: Dict[str, Any]) -> None:
        """Load analyzed report data for Q&A"""
        self.analysis_data = analysis_result
        self.qa_assistant.load_analysis_data(analysis_result)
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Process user question based on loaded report data.
        
        Returns explanation from Q&A assistant or asks for upload.
        
        Args:
            message: User's question
            
        Returns:
            Dict with response type and message
        """
        try:
            # No report data → ask user to upload
            if not self.analysis_data:
                return {
                    'type': 'no_data',
                    'message': "Please upload a blood report first for analysis and questions.",
                }
            
            # Report data exists → answer based on it
            response_message = self.qa_assistant.answer_question(message)
            
            return {
                'type': 'answer',
                'message': response_message,
            }
        
        except Exception as e:
            return {
                'type': 'error',
                'message': f"Error: {str(e)}"
            }
    
    def clear_data(self) -> None:
        """Clear loaded report data"""
        self.analysis_data = {}
        self.qa_assistant.load_analysis_data({})


def create_enhanced_ai_agent() -> EnhancedAIAgent:
    """Create and return AI agent instance"""
    return EnhancedAIAgent()
