"""
Enhanced AI Agent
Integrates all AI agent components for intelligent, goal-oriented medical report analysis
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .intent_inference_engine import IntentInferenceEngine, infer_user_intent
from .clarifying_question_generator import ClarifyingQuestionGenerator, generate_clarifying_questions
from .goal_oriented_workflow_manager import GoalOrientedWorkflowManager, create_goal_oriented_workflow
from .advanced_context_manager import AdvancedContextManager, create_context_manager
from .workflow_actions import create_workflow_actions
from .qa_assistant import BloodReportQAAssistant


class EnhancedAIAgent:
    """
    Enhanced AI Agent that combines intent inference, context management, 
    workflow orchestration, and intelligent interaction for medical report analysis
    """
    
    def __init__(self, db_path: str = "user_context.db"):
        # Initialize core components
        self.intent_engine = IntentInferenceEngine()
        self.question_generator = ClarifyingQuestionGenerator()
        self.workflow_manager = GoalOrientedWorkflowManager()
        self.context_manager = create_context_manager(db_path)
        
        # Initialize workflow actions
        self.workflow_actions = create_workflow_actions(context_manager=self.context_manager)
        
        # Register action functions with workflow manager
        self._register_workflow_actions()
        
        # Agent state
        self.current_user_id = None
        self.current_session_id = None
        self.active_workflows = {}
        self.analysis_data = {}  # Store current analysis data
        
        # Response generation settings
        self.response_style = {
            'tone': 'professional_friendly',
            'detail_level': 'adaptive',
            'include_explanations': True,
            'medical_safety': True
        }
    
    def start_user_session(self, user_id: str = None, session_type: str = "analysis") -> str:
        """
        Start a new user session with full context initialization
        """
        # Start context manager session
        session_id = self.context_manager.start_session(user_id, session_type)
        
        self.current_user_id = self.context_manager.current_user_id
        self.current_session_id = session_id
        
        return session_id
    
    def process_user_message(self, message: str, additional_context: Dict = None) -> Dict[str, Any]:
        """
        Process user message with full AI agent capabilities
        
        Args:
            message: User's input message
            additional_context: Additional context (e.g., uploaded files, UI state)
            
        Returns:
            Comprehensive response with actions, clarifications, or results
        """
        try:
            # Step 1: Gather comprehensive context
            context = self._gather_comprehensive_context(additional_context)
            
            # Step 2: Infer user intent
            intent_analysis = self.intent_engine.infer_intent(
                message, 
                context.get('recent_conversation', {}).get('recent_messages', []),
                context
            )
            
            # Step 3: Log conversation message
            self.context_manager.add_conversation_message(
                role='user',
                content=message,
                intent=intent_analysis.get('primary_intent'),
                context_used=context,
                metadata={'intent_confidence': intent_analysis.get('confidence')}
            )
            
            # Step 4: Determine response strategy
            response_strategy = self._determine_response_strategy(intent_analysis, context)
            
            # Step 5: Execute appropriate response strategy
            if response_strategy == 'clarification_needed':
                response = self._handle_clarification_request(message, intent_analysis, context)
            
            elif response_strategy == 'workflow_execution':
                response = self._handle_workflow_execution(message, intent_analysis, context)
            
            elif response_strategy == 'direct_answer':
                response = self._handle_direct_answer(message, intent_analysis, context)
            
            elif response_strategy == 'context_gathering':
                response = self._handle_context_gathering(message, intent_analysis, context)
            
            else:
                response = self._handle_fallback_response(message, intent_analysis, context)
            
            # Step 6: Log assistant response
            self.context_manager.add_conversation_message(
                role='assistant',
                content=response.get('message', ''),
                intent=intent_analysis.get('primary_intent'),
                metadata={
                    'response_strategy': response_strategy,
                    'actions_taken': response.get('actions', [])
                }
            )
            
            # Step 7: Update user preferences based on interaction
            self._update_user_preferences_from_interaction(intent_analysis, response, context)
            
            return response
        
        except Exception as e:
            # Error handling with graceful degradation
            return self._handle_error_response(str(e), message)
    
    def _gather_comprehensive_context(self, additional_context: Dict = None) -> Dict[str, Any]:
        """Gather all available context for decision making"""
        # Get context from context manager
        context = self.context_manager.get_contextual_information()
        
        # Add analysis data if available
        if hasattr(self, 'analysis_data') and self.analysis_data:
            context['analysis_data'] = self.analysis_data
            context['has_report'] = True
        else:
            context['has_report'] = False
        
        # Add additional context from UI or other sources
        if additional_context:
            context['additional_context'] = additional_context
            if additional_context.get('reports_uploaded'):
                context['has_report'] = True
        
        return context
    
    def _determine_response_strategy(self, intent_analysis: Dict, context: Dict) -> str:
        """Determine the best response strategy based on intent and context"""
        primary_intent = intent_analysis.get('primary_intent')
        confidence = intent_analysis.get('confidence', 0)
        clarification_needed = intent_analysis.get('clarification_needed', False)
        
        # Check if we have report data available
        has_reports = context.get('has_report', False)
        
        # If we have reports, prioritize direct answers
        if has_reports:
            if clarification_needed and confidence < 0.3:
                return 'clarification_needed'
            return 'direct_answer'
        
        # No reports loaded - check what user needs
        if primary_intent in ['analyze_report']:
            return 'context_gathering'
        
        # For general questions, try direct answer
        if confidence > 0.4:
            return 'direct_answer'
        
        # Only ask clarification for very ambiguous queries
        if clarification_needed and confidence < 0.3:
            return 'clarification_needed'
        
        return 'direct_answer'
    
    def _handle_clarification_request(self, message: str, intent_analysis: Dict, 
                                    context: Dict) -> Dict[str, Any]:
        """Handle requests that need clarification"""
        clarification_result = self.question_generator.generate_clarifying_questions(
            message, intent_analysis, context.get('analysis_data', {})
        )
        
        questions = clarification_result.get('questions', [])
        
        if questions:
            response_message = f"💭 {questions[0]['question']}"
        else:
            response_message = "Could you tell me more about what you'd like to know?"
        
        return {
            'type': 'clarification_request',
            'message': response_message,
            'questions': questions[:1],
            'intent_analysis': intent_analysis
        }
    
    def _handle_workflow_execution(self, message: str, intent_analysis: Dict, 
                                 context: Dict) -> Dict[str, Any]:
        """Handle requests that can be executed via workflows"""
        try:
            workflow_id = self.workflow_manager.create_workflow_for_intent(
                intent_analysis, context.get('analysis_data', {})
            )
            
            workflow_results = self.workflow_manager.execute_workflow(
                workflow_id, 
                {
                    'user_message': message,
                    'context': context
                }
            )
            
            workflow_status = self.workflow_manager.get_workflow_status(workflow_id)
            self.context_manager.save_workflow_execution(
                workflow_id,
                workflow_status.get('goal_description', ''),
                intent_analysis.get('primary_intent'),
                list(workflow_results.keys()),
                1.0 if workflow_status.get('status') == 'completed' else 0.5,
                (datetime.now() - datetime.fromisoformat(workflow_status.get('started_at', datetime.now().isoformat()))).total_seconds()
            )
            
            response = self._format_workflow_response(
                intent_analysis.get('primary_intent'), 
                workflow_results, 
                context
            )
            
            response['workflow_id'] = workflow_id
            response['workflow_status'] = workflow_status
            
            return response
        
        except Exception as e:
            return {
                'type': 'workflow_error',
                'message': f"I encountered an issue: {str(e)}. Let me try a different approach.",
                'fallback_available': True
            }
    
    def _handle_direct_answer(self, message: str, intent_analysis: Dict, 
                            context: Dict) -> Dict[str, Any]:
        """Handle requests with direct answers"""
        primary_intent = intent_analysis.get('primary_intent')
        
        # Generate helpful response
        response = self._generate_helpful_response(message, intent_analysis, context)
        
        return {
            'type': 'direct_answer',
            'message': response,
            'source': 'general_knowledge',
            'intent': primary_intent
        }
    
    def _generate_helpful_response(self, message: str, intent_analysis: Dict, context: Dict) -> str:
        """Generate helpful response for general health questions"""
        message_lower = message.lower()
        
        # Food/diet recommendations
        if any(word in message_lower for word in ['food', 'diet', 'eat', 'nutrition', 'meal']):
            return """🍎 **General Healthy Eating Guidelines:**

• **Fruits & Vegetables**: Aim for 5+ servings daily
• **Whole Grains**: Choose brown rice, oats, whole wheat
• **Lean Proteins**: Fish, chicken, beans, lentils
• **Healthy Fats**: Olive oil, nuts, avocados
• **Limit**: Processed foods, sugar, excess salt

**For personalized recommendations based on your blood work**, please upload your blood report and I can suggest specific dietary changes based on your results.

⚠️ *Always consult a healthcare provider or dietitian for personalized advice.*"""
        
        # Exercise recommendations
        if any(word in message_lower for word in ['exercise', 'workout', 'fitness', 'physical']):
            return """🏃 **General Exercise Guidelines:**

• **Cardio**: 150 mins moderate or 75 mins vigorous per week
• **Strength**: 2+ days per week for major muscle groups
• **Flexibility**: Stretching or yoga regularly
• **Start slow**: Gradually increase intensity

**Upload your blood report** for exercise recommendations tailored to your health status.

⚠️ *Consult your doctor before starting new exercise programs.*"""
        
        # Lifestyle recommendations
        if any(word in message_lower for word in ['lifestyle', 'health', 'improve', 'better']):
            return """💪 **General Health Tips:**

• **Sleep**: 7-9 hours quality sleep
• **Hydration**: 8+ glasses of water daily
• **Stress**: Practice relaxation techniques
• **Regular checkups**: Annual health screenings
• **Avoid**: Smoking, excessive alcohol

**For personalized advice**, upload your blood report for analysis.

⚠️ *This is general guidance. Consult healthcare providers for personal advice.*"""
        
        # Default helpful response
        return self._generate_general_response(message, intent_analysis, context)
    
    def _handle_context_gathering(self, message: str, intent_analysis: Dict, 
                                context: Dict) -> Dict[str, Any]:
        """Handle requests that need more context"""
        primary_intent = intent_analysis.get('primary_intent')
        
        if primary_intent == 'analyze_report':
            return {
                'type': 'context_request',
                'message': "I'd be happy to help analyze your blood report! Please upload your medical report (PDF, image, or JSON format) to get started.",
                'required_context': 'blood_reports',
                'upload_instructions': [
                    "Supported formats: PDF, PNG, JPG, JPEG, JSON, CSV",
                    "Ensure reports are clear and readable"
                ],
                'next_steps': [
                    "Upload your report",
                    "I'll automatically extract and analyze the data",
                    "Ask questions about your results"
                ]
            }
        
        return {
            'type': 'context_request',
            'message': "To provide the most helpful response, I need a bit more information. What specific aspect of blood report analysis can I help you with?",
            'suggestions': [
                "Upload a blood report for analysis",
                "Ask about specific blood parameters",
                "Learn about health recommendations"
            ]
        }
    
    def _handle_fallback_response(self, message: str, intent_analysis: Dict, 
                                context: Dict) -> Dict[str, Any]:
        """Handle requests when other strategies aren't suitable"""
        return {
            'type': 'general_assistance',
            'message': "I'm here to help with blood report analysis and health insights. I can analyze your reports, explain parameters, provide health recommendations, and compare results over time. What would you like to explore?",
            'capabilities': [
                "📊 Analyze blood reports (PDF, images, JSON)",
                "🔍 Explain medical parameters and values",
                "📈 Compare multiple reports and track trends",
                "💡 Provide personalized health recommendations",
                "❓ Answer questions about your results"
            ],
            'getting_started': "Upload a blood report or ask me a specific question to begin!"
        }
    
    def _format_workflow_response(self, intent: str, workflow_results: Dict, 
                                context: Dict) -> Dict[str, Any]:
        """Format workflow results into user-friendly response"""
        if intent == 'analyze_report':
            return {
                'type': 'analysis_complete',
                'message': "I've completed the analysis of your blood report. Here are the key findings:",
                'results': workflow_results,
                'next_actions': [
                    "Ask questions about specific parameters",
                    "Get health recommendations",
                    "Export results"
                ]
            }
        
        else:
            return {
                'type': 'workflow_complete',
                'message': "I've processed your request successfully.",
                'results': workflow_results,
                'intent': intent
            }
    
    def _suggest_follow_up_actions(self, intent: str, context: Dict) -> List[str]:
        """Suggest relevant follow-up actions based on intent and context"""
        actions = []
        
        if intent == 'analyze_report':
            actions.extend([
                "Ask about specific abnormal values",
                "Get personalized health recommendations",
                "Learn about lifestyle changes"
            ])
        
        elif intent == 'health_advice':
            actions.extend([
                "Learn about specific dietary changes",
                "Understand exercise recommendations",
                "Ask about lifestyle modifications"
            ])
        
        elif intent == 'risk_assessment':
            actions.extend([
                "Explore prevention strategies",
                "Understand monitoring recommendations",
                "Ask about follow-up testing"
            ])
        
        return actions[:3]  # Limit to top 3 suggestions
    
    def _generate_general_response(self, message: str, intent_analysis: Dict, 
                                 context: Dict) -> str:
        """Generate general response when specific data isn't available"""
        intent = intent_analysis.get('primary_intent')
        
        responses = {
            'explain_parameter': "I'd be happy to explain blood parameters! Once you upload a report, I can provide detailed explanations of your specific values and what they mean for your health.",
            
            'health_advice': "I can provide personalized health recommendations based on your blood report results. Upload your report first, and I'll analyze your values to suggest relevant dietary, lifestyle, and monitoring advice.",
            
            'risk_assessment': "Risk assessment requires analyzing your specific blood values. Please upload your blood report, and I'll evaluate various health risk factors based on your results.",
            
            'general_question': "I'm here to help with blood report analysis and health insights. I can analyze reports, explain parameters, track trends, and provide recommendations. What specific aspect interests you most?"
        }
        
        return responses.get(intent, responses['general_question'])
    
    def _get_helpful_suggestions(self, intent: str, context: Dict) -> List[str]:
        """Get helpful suggestions based on intent and context"""
        base_suggestions = [
            "Upload a blood report for personalized analysis",
            "Ask about specific blood parameters",
            "Learn about health recommendations"
        ]
        
        intent_specific = {
            'explain_parameter': [
                "Ask about cholesterol levels",
                "Learn about blood sugar ranges",
                "Understand blood count parameters"
            ],
            'health_advice': [
                "Get dietary recommendations",
                "Learn about exercise guidelines",
                "Understand lifestyle modifications"
            ],
            'risk_assessment': [
                "Assess cardiovascular risk",
                "Evaluate metabolic health",
                "Understand prevention strategies"
            ]
        }
        
        return intent_specific.get(intent, base_suggestions)
    
    def _update_user_preferences_from_interaction(self, intent_analysis: Dict, 
                                                response: Dict, context: Dict):
        """Update user preferences based on interaction patterns"""
        # Track preferred detail level
        if response.get('type') == 'direct_answer':
            # User accepted direct answer - they prefer efficiency
            current_prefs = context.get('user_preferences', {})
            current_prefs['prefers_direct_answers'] = True
            self.context_manager.update_user_preferences(current_prefs)
        
        # Track common intents
        intent = intent_analysis.get('primary_intent')
        if intent:
            # This would update user's common concerns/interests
            pass
    
    def _register_workflow_actions(self):
        """Register action functions with the workflow manager"""
        if not self.workflow_actions:
            # Create temporary workflow actions for initial registration
            temp_actions = create_workflow_actions()
            action_functions = {
                'get_user_reports': temp_actions.get_user_reports,
                'analyze_parameters': temp_actions.analyze_parameters,
                'pattern_analysis': temp_actions.pattern_analysis,
                'generate_report_summary': temp_actions.generate_report_summary,
                'explain_comparison_requirements': temp_actions.explain_comparison_requirements,
                'generate_clarifying_questions': self._generate_clarifying_questions_action,
                'provide_emotional_support': temp_actions.provide_emotional_support,
                'add_medical_disclaimer': temp_actions.add_medical_disclaimer,
                'request_report_upload': temp_actions.request_report_upload,
                'align_report_parameters': temp_actions.align_report_parameters,
                'calculate_parameter_changes': temp_actions.calculate_parameter_changes,
                'analyze_trends': temp_actions.calculate_parameter_changes,
                'present_trend_analysis': temp_actions.generate_comparison_report,
                'generate_comparison_report': temp_actions.generate_comparison_report,
                'analyze_current_findings': temp_actions.analyze_current_findings,
                'identify_health_concerns': temp_actions.identify_health_concerns,
                'generate_health_recommendations': temp_actions.generate_health_recommendations,
                'add_medical_disclaimers': temp_actions.add_medical_disclaimer,
                'calculate_risk_scores': temp_actions.pattern_analysis,
                'assess_risk_patterns': temp_actions.pattern_analysis,
                'contextualize_risks': temp_actions.pattern_analysis,
                'present_risk_assessment': temp_actions.generate_report_summary,
                'get_historical_reports': temp_actions.get_historical_reports,
                'calculate_parameter_trends': temp_actions.calculate_parameter_changes,
                'identify_trend_patterns': temp_actions.calculate_parameter_changes,
                'explain_trend_requirements': temp_actions.explain_trend_requirements,
                'identify_target_parameters': self._identify_target_parameters,
                'get_parameter_values': temp_actions.get_parameter_values,
                'explain_parameters': self._explain_parameters,
                'provide_medical_context': self._provide_medical_context,
                'present_clarifying_questions': self._present_clarifying_questions,
                'analyze_general_context': self._analyze_general_context,
                'provide_general_help': self._provide_general_help,
                'offer_export_options': temp_actions.offer_export_options
            }
        else:
            # Use properly initialized workflow actions
            action_functions = {
                'get_user_reports': self.workflow_actions.get_user_reports,
                'analyze_parameters': self.workflow_actions.analyze_parameters,
                'pattern_analysis': self.workflow_actions.pattern_analysis,
                'generate_report_summary': self.workflow_actions.generate_report_summary,
                'explain_comparison_requirements': self.workflow_actions.explain_comparison_requirements,
                'generate_clarifying_questions': self._generate_clarifying_questions_action,
                'provide_emotional_support': self.workflow_actions.provide_emotional_support,
                'add_medical_disclaimer': self.workflow_actions.add_medical_disclaimer,
                'request_report_upload': self.workflow_actions.request_report_upload,
                'align_report_parameters': self.workflow_actions.align_report_parameters,
                'calculate_parameter_changes': self.workflow_actions.calculate_parameter_changes,
                'analyze_trends': self.workflow_actions.calculate_parameter_changes,
                'present_trend_analysis': self.workflow_actions.generate_comparison_report,
                'generate_comparison_report': self.workflow_actions.generate_comparison_report,
                'analyze_current_findings': self.workflow_actions.analyze_current_findings,
                'identify_health_concerns': self.workflow_actions.identify_health_concerns,
                'generate_health_recommendations': self.workflow_actions.generate_health_recommendations,
                'add_medical_disclaimers': self.workflow_actions.add_medical_disclaimer,
                'calculate_risk_scores': self.workflow_actions.pattern_analysis,
                'assess_risk_patterns': self.workflow_actions.pattern_analysis,
                'contextualize_risks': self.workflow_actions.pattern_analysis,
                'present_risk_assessment': self.workflow_actions.generate_report_summary,
                'get_historical_reports': self.workflow_actions.get_historical_reports,
                'calculate_parameter_trends': self.workflow_actions.calculate_parameter_changes,
                'identify_trend_patterns': self.workflow_actions.calculate_parameter_changes,
                'explain_trend_requirements': self.workflow_actions.explain_trend_requirements,
                'identify_target_parameters': self._identify_target_parameters,
                'get_parameter_values': self.workflow_actions.get_parameter_values,
                'explain_parameters': self._explain_parameters,
                'provide_medical_context': self._provide_medical_context,
                'present_clarifying_questions': self._present_clarifying_questions,
                'analyze_general_context': self._analyze_general_context,
                'provide_general_help': self._provide_general_help,
                'offer_export_options': self.workflow_actions.offer_export_options
            }
        
        for name, function in action_functions.items():
            self.workflow_manager.register_action_function(name, function)
    
    # Action function implementations
    def _identify_target_parameters(self, user_message="", **kwargs) -> List[str]:
        """Identify which parameters user is asking about"""
        message_lower = user_message.lower()
        
        # Common parameter mappings
        parameter_keywords = {
            'cholesterol': ['cholesterol', 'chol', 'ldl', 'hdl'],
            'glucose': ['glucose', 'sugar', 'blood sugar', 'diabetes'],
            'hemoglobin': ['hemoglobin', 'hb', 'hgb', 'anemia'],
            'rbc': ['rbc', 'red blood cell', 'red cell'],
            'wbc': ['wbc', 'white blood cell', 'white cell'],
            'platelet': ['platelet', 'plt', 'clotting']
        }
        
        identified_parameters = []
        
        for param, keywords in parameter_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                identified_parameters.append(param)
        
        return identified_parameters if identified_parameters else ['all_available']
    
    def _explain_parameters(self, target_parameters=None, **kwargs) -> str:
        """Generate detailed parameter explanations"""
        if not target_parameters:
            target_parameters = kwargs.get('result_identify_parameters', ['general'])
        
        explanations = []
        
        parameter_info = {
            'cholesterol': "Cholesterol measures fats in your blood. High levels can increase heart disease risk.",
            'glucose': "Blood glucose (sugar) indicates how well your body processes sugar. High levels may suggest diabetes risk.",
            'hemoglobin': "Hemoglobin carries oxygen in your blood. Low levels may indicate anemia.",
            'rbc': "Red blood cells carry oxygen throughout your body. Abnormal counts can indicate various health conditions.",
            'wbc': "White blood cells fight infections. High or low counts may indicate immune system issues.",
            'platelet': "Platelets help blood clot. Abnormal counts can affect bleeding and clotting."
        }
        
        if 'all_available' in target_parameters:
            explanations.append("Here are explanations for common blood parameters:")
            for param, explanation in parameter_info.items():
                explanations.append(f"• **{param.title()}**: {explanation}")
        else:
            for param in target_parameters:
                if param in parameter_info:
                    explanations.append(f"**{param.title()}**: {parameter_info[param]}")
        
        return "\n".join(explanations) if explanations else "I can explain various blood parameters once you specify which ones interest you."
    
    def _provide_medical_context(self, **kwargs) -> str:
        """Provide medical context and significance"""
        return "Understanding your blood test results helps you make informed health decisions. Each parameter provides insights into different aspects of your health, from heart function to immune system status. Always discuss results with your healthcare provider for personalized medical advice."
    
    def _generate_clarifying_questions_action(self, **kwargs) -> Dict[str, Any]:
        """Generate clarifying questions as workflow action"""
        intent_analysis = kwargs.get('intent_analysis', {})
        user_context = kwargs.get('user_context', {})
        
        return generate_clarifying_questions(
            kwargs.get('user_message', ''),
            intent_analysis,
            user_context
        )
    
    def _present_clarifying_questions(self, questions_data=None, **kwargs) -> str:
        """Present clarifying questions to user"""
        if not questions_data:
            questions_data = kwargs.get('result_generate_questions', {})
        
        questions = questions_data.get('questions', [])
        
        if not questions:
            return "I'd like to better understand what you're looking for. Could you provide more details about your question?"
        
        response_parts = ["I'd like to better understand what you're looking for:"]
        
        for i, question in enumerate(questions[:3], 1):
            response_parts.append(f"{i}. {question.get('question', '')}")
            
            suggested_answers = question.get('suggested_answers', [])
            if suggested_answers:
                response_parts.append(f"   *Suggestions: {', '.join(suggested_answers[:3])}*")
        
        return "\n".join(response_parts)
    
    def _analyze_general_context(self, **kwargs) -> Dict[str, Any]:
        """Analyze available context and user needs"""
        intent_analysis = kwargs.get('intent_analysis', {})
        user_context = kwargs.get('user_context', {})
        
        return {
            'context_available': bool(user_context),
            'intent_confidence': intent_analysis.get('confidence', 0),
            'suggested_approach': 'provide_general_guidance'
        }
    
    def _provide_general_help(self, context_analysis=None, **kwargs) -> str:
        """Provide general assistance and guidance"""
        return """I'm here to help with blood report analysis and health insights. Here's what I can do:

📊 **Analyze Blood Reports**: Upload your reports for comprehensive analysis
🔍 **Explain Parameters**: Get detailed explanations of blood test values  
📈 **Compare Reports**: Track changes and trends over time
💡 **Health Recommendations**: Receive personalized advice based on your results
❓ **Answer Questions**: Ask about specific aspects of your health data

To get started, you can:
• Upload a blood report for analysis
• Ask about specific blood parameters
• Request health recommendations based on your results

What would you like to explore?"""
    
    def _handle_error_response(self, error: str, original_message: str) -> Dict[str, Any]:
        """Handle errors gracefully"""
        return {
            'type': 'error',
            'message': "I encountered an issue processing your request. Let me try to help in a different way. Could you rephrase your question or provide more details?",
            'error_context': 'Processing error occurred',
            'suggestions': [
                "Try rephrasing your question",
                "Upload a blood report if you haven't already",
                "Ask about a specific aspect of blood analysis"
            ],
            'fallback_available': True
        }
    
    def end_session(self, goals_achieved: List[str] = None):
        """End the current session"""
        if self.context_manager:
            self.context_manager.end_session(goals_achieved)
        
        self.current_user_id = None
        self.current_session_id = None


# Convenience function for easy integration
def create_enhanced_ai_agent(db_path: str = "user_context.db") -> EnhancedAIAgent:
    """Create and return an enhanced AI agent instance"""
    return EnhancedAIAgent(db_path)