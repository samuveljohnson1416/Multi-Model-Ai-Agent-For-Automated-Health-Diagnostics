"""
Blood Report Q&A Assistant
Answers questions using ONLY the provided blood report analysis data
"""

import json
from typing import Dict, List, Any, Optional


class BloodReportQAAssistant:
    """
    Blood Report Q&A Assistant embedded inside the medical analysis system.
    
    Answers questions ONLY using the provided blood report analysis data including:
    - Parameter interpretations (Model 1)
    - Risk assessments (Model 2) 
    - Contextual adjustments (Model 3)
    - Synthesized findings
    - Generated recommendations
    
    STRICT RULES:
    - Do NOT use external or general medical knowledge
    - Do NOT diagnose diseases
    - Do NOT prescribe medications or treatments
    - Do NOT assume missing information
    - Do NOT modify, recompute, or infer new results
    - If answer is NOT supported by analysis, reply: "This information is not available in your blood report analysis."
    """
    
    def __init__(self):
        self.analysis_data = None
        self.disclaimer = "This information is for educational purposes only and is not a substitute for professional medical advice."
        
        # Question patterns for routing
        self.parameter_keywords = [
            'hemoglobin', 'cholesterol', 'glucose', 'wbc', 'rbc', 'platelet', 
            'hdl', 'ldl', 'triglycerides', 'creatinine', 'bun', 'alt', 'ast',
            'high', 'low', 'normal', 'abnormal', 'level', 'count', 'value'
        ]
        
        self.risk_keywords = [
            'risk', 'pattern', 'concern', 'worry', 'dangerous', 'serious',
            'problem', 'issue', 'finding', 'result'
        ]
        
        self.context_keywords = [
            'age', 'gender', 'why', 'because', 'reason', 'affect', 'influence',
            'context', 'demographic'
        ]
        
        self.recommendation_keywords = [
            'recommend', 'advice', 'suggest', 'should', 'do', 'next',
            'lifestyle', 'diet', 'exercise', 'follow'
        ]
    
    def load_analysis_data(self, analysis_result: Dict[str, Any]) -> None:
        """Load blood report analysis data for Q&A"""
        self.analysis_data = analysis_result
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question using ONLY the loaded blood report analysis data
        
        Args:
            question: User's question about their blood report
            
        Returns:
            Answer based on analysis data or unavailable message
        """
        if not self.analysis_data:
            return "No blood report analysis data is currently loaded. Please analyze a blood report first."
        
        question_lower = question.lower()
        
        # Route question to appropriate handler
        if any(keyword in question_lower for keyword in self.parameter_keywords):
            return self._answer_parameter_question(question_lower)
        elif any(keyword in question_lower for keyword in self.risk_keywords):
            return self._answer_risk_question(question_lower)
        elif any(keyword in question_lower for keyword in self.context_keywords):
            return self._answer_context_question(question_lower)
        elif any(keyword in question_lower for keyword in self.recommendation_keywords):
            return self._answer_recommendation_question(question_lower)
        else:
            # Try general analysis overview
            return self._answer_general_question(question_lower)
    
    def _answer_parameter_question(self, question: str) -> str:
        """Answer questions about specific parameters"""
        try:
            # Get parameter interpretations from Model 1
            interpretations = self._get_parameter_interpretations()
            if not interpretations:
                return "This information is not available in your blood report analysis."
            
            # Look for specific parameter mentions
            for param in interpretations:
                param_name = param.get('test_name', '').lower()
                if param_name in question:
                    classification = param.get('classification', 'Unknown')
                    value = param.get('value', 'Unknown')
                    ref_range = param.get('reference_range', 'Unknown')
                    
                    if classification == 'High':
                        response = f"Your {param.get('test_name', 'parameter')} level is {value}, which is above the normal range of {ref_range}. "
                        response += "This was identified as elevated in your analysis."
                    elif classification == 'Low':
                        response = f"Your {param.get('test_name', 'parameter')} level is {value}, which is below the normal range of {ref_range}. "
                        response += "This was identified as low in your analysis."
                    elif classification == 'Normal':
                        response = f"Your {param.get('test_name', 'parameter')} level is {value}, which is within the normal range of {ref_range}."
                    else:
                        response = f"Your {param.get('test_name', 'parameter')} level is {value}. The classification is {classification}."
                    
                    return f"{response}\n\n{self.disclaimer}"
            
            # General parameter overview
            abnormal_params = [p for p in interpretations if p.get('classification') in ['High', 'Low']]
            if abnormal_params:
                response = f"Your analysis found {len(abnormal_params)} parameter(s) outside normal ranges: "
                param_list = [f"{p.get('test_name', 'Unknown')} ({p.get('classification', 'Unknown')})" 
                             for p in abnormal_params[:3]]
                response += ", ".join(param_list)
                if len(abnormal_params) > 3:
                    response += f" and {len(abnormal_params) - 3} others"
            else:
                response = "All analyzed parameters appear to be within normal ranges according to your analysis."
            
            return f"{response}\n\n{self.disclaimer}"
            
        except Exception:
            return "This information is not available in your blood report analysis."
    
    def _answer_risk_question(self, question: str) -> str:
        """Answer questions about risks and patterns"""
        try:
            # Get risk assessment from synthesis
            synthesis = self._get_synthesis_data()
            if not synthesis:
                return "This information is not available in your blood report analysis."
            
            risk_level = synthesis.get('risk_level', 'Unknown')
            overall_status = synthesis.get('overall_status', 'Unknown')
            key_concerns = synthesis.get('key_concerns', [])
            
            response = f"Based on your blood report analysis, your overall status is: {overall_status}. "
            response += f"The risk level was assessed as: {risk_level}. "
            
            if key_concerns:
                response += f"Key areas of concern identified include: {', '.join(key_concerns[:3])}."
            else:
                response += "No specific areas of concern were identified in the analysis."
            
            # Add pattern information if available
            milestone2_features = synthesis.get('milestone2_enhancements', {})
            patterns = milestone2_features.get('patterns_detected', [])
            if patterns:
                response += f" The analysis detected {len(patterns)} pattern(s) across your parameters."
            
            return f"{response}\n\n{self.disclaimer}"
            
        except Exception:
            return "This information is not available in your blood report analysis."
    
    def _answer_context_question(self, question: str) -> str:
        """Answer questions about age/gender context"""
        try:
            # Get contextual analysis from Model 3
            milestone2_data = self._get_milestone2_data()
            if not milestone2_data:
                return "This information is not available in your blood report analysis."
            
            model3_context = milestone2_data.get('model3_context', {})
            context_status = model3_context.get('context_status', 'Unknown')
            demographic_info = model3_context.get('demographic_info', {})
            context_notes = model3_context.get('context_notes', [])
            
            if context_status == 'Context not available':
                response = "Age and gender information was not found in your blood report, so contextual adjustments could not be applied to your analysis."
            else:
                age_extracted = demographic_info.get('age_extracted', False)
                gender_extracted = demographic_info.get('gender_extracted', False)
                
                if age_extracted or gender_extracted:
                    response = "Your analysis included contextual adjustments based on "
                    context_factors = []
                    if age_extracted:
                        age_value = demographic_info.get('age_value', 'Unknown')
                        context_factors.append(f"age ({age_value})")
                    if gender_extracted:
                        gender_value = demographic_info.get('gender_value', 'Unknown')
                        context_factors.append(f"gender ({gender_value})")
                    
                    response += " and ".join(context_factors) + ". "
                    
                    if context_notes:
                        response += "Specific contextual considerations: " + "; ".join(context_notes[:2]) + "."
                else:
                    response = "No demographic context was available for your analysis."
            
            return f"{response}\n\n{self.disclaimer}"
            
        except Exception:
            return "This information is not available in your blood report analysis."
    
    def _answer_recommendation_question(self, question: str) -> str:
        """Answer questions about recommendations"""
        try:
            # Get recommendations from analysis
            recommendations = self._get_recommendations()
            if not recommendations:
                return "This information is not available in your blood report analysis."
            
            lifestyle_recs = recommendations.get('lifestyle_recommendations', [])
            follow_up = recommendations.get('follow_up_guidance', '')
            consultation = recommendations.get('healthcare_consultation', '')
            
            response = ""
            
            if lifestyle_recs:
                response += "The analysis generated these lifestyle recommendations: "
                response += "; ".join(lifestyle_recs[:3]) + ". "
            
            if follow_up:
                response += f"Follow-up guidance: {follow_up} "
            
            if consultation:
                response += f"Important: {consultation}"
            
            if not response:
                response = "No specific recommendations were generated in your analysis."
            
            return f"{response}\n\n{self.disclaimer}"
            
        except Exception:
            return "This information is not available in your blood report analysis."
    
    def _answer_general_question(self, question: str) -> str:
        """Answer general questions about the analysis"""
        try:
            # Provide general overview
            synthesis = self._get_synthesis_data()
            if not synthesis:
                return "This information is not available in your blood report analysis."
            
            summary = synthesis.get('summary', {})
            total_tests = summary.get('total_tests', 0)
            abnormal_count = summary.get('abnormal_count', 0)
            overall_status = synthesis.get('overall_status', 'Unknown')
            
            response = f"Your blood report analysis examined {total_tests} parameter(s). "
            response += f"{abnormal_count} parameter(s) were found outside normal ranges. "
            response += f"Overall status: {overall_status}."
            
            return f"{response}\n\n{self.disclaimer}"
            
        except Exception:
            return "This information is not available in your blood report analysis."
    
    def _get_parameter_interpretations(self) -> List[Dict]:
        """Extract parameter interpretations from analysis data"""
        try:
            if 'phase2_full_result' in self.analysis_data:
                param_interp = self.analysis_data['phase2_full_result'].get('parameter_interpretation', {})
                return param_interp.get('interpretations', [])
            return []
        except Exception:
            return []
    
    def _get_synthesis_data(self) -> Dict:
        """Extract synthesis data from analysis"""
        try:
            if 'phase2_full_result' in self.analysis_data:
                return self.analysis_data['phase2_full_result'].get('synthesis', {})
            return {}
        except Exception:
            return {}
    
    def _get_milestone2_data(self) -> Dict:
        """Extract Milestone-2 data from analysis"""
        try:
            if 'phase2_full_result' in self.analysis_data:
                detailed_results = self.analysis_data['phase2_full_result'].get('detailed_milestone2_results', {})
                return detailed_results.get('milestone2_analysis', {})
            return {}
        except Exception:
            return {}
    
    def _get_recommendations(self) -> Dict:
        """Extract recommendations from analysis"""
        try:
            if 'phase2_full_result' in self.analysis_data:
                return self.analysis_data['phase2_full_result'].get('recommendations', {})
            return {}
        except Exception:
            return {}
    
    def get_available_topics(self) -> List[str]:
        """Get list of topics that can be answered based on loaded analysis"""
        if not self.analysis_data:
            return ["No analysis data loaded"]
        
        topics = []
        
        # Check what data is available
        if self._get_parameter_interpretations():
            topics.append("Parameter levels and classifications")
        
        if self._get_synthesis_data():
            topics.append("Risk assessment and overall status")
        
        if self._get_milestone2_data():
            topics.append("Pattern analysis and contextual factors")
        
        if self._get_recommendations():
            topics.append("Lifestyle recommendations and follow-up guidance")
        
        return topics if topics else ["Limited analysis data available"]


# Convenience function for integration
def create_qa_assistant(analysis_result: Dict[str, Any]) -> BloodReportQAAssistant:
    """Create and load a Q&A assistant with analysis data"""
    assistant = BloodReportQAAssistant()
    assistant.load_analysis_data(analysis_result)
    return assistant