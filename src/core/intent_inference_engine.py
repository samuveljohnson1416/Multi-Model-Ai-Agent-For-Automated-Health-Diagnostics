"""
Intent Inference Engine
Analyzes user input, conversation history, and contextual cues to determine underlying user intent
"""

import json
import re
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class UserIntent(Enum):
    """Enumeration of possible user intents"""
    ANALYZE_REPORT = "analyze_report"
    COMPARE_REPORTS = "compare_reports"
    EXPLAIN_PARAMETER = "explain_parameter"
    HEALTH_ADVICE = "health_advice"
    RISK_ASSESSMENT = "risk_assessment"
    TREND_ANALYSIS = "trend_analysis"
    CLARIFICATION_NEEDED = "clarification_needed"
    GENERAL_QUESTION = "general_question"
    EXPORT_DATA = "export_data"
    SCHEDULE_FOLLOWUP = "schedule_followup"


class IntentInferenceEngine:
    """
    Advanced Intent Inference Engine using LLM and pattern analysis
    Determines user's true goals from vague or implicit requests
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "mistral:7b-instruct"
        
        # Intent classification patterns
        self.intent_patterns = {
            UserIntent.ANALYZE_REPORT: [
                r'(?i)analyze|analysis|interpret|what does.*mean|explain.*report',
                r'(?i)results|findings|summary|overview|check.*report',
                r'(?i)tell me about.*report|show me.*results|what.*this.*report',
                r'(?i)blood.*report|test.*results|lab.*results'
            ],
            UserIntent.COMPARE_REPORTS: [
                r'(?i)compare|comparison|difference|between.*reports',
                r'(?i)change|improvement|worse|better.*report',
                r'(?i)trend|progress|over time|previous.*report',
                r'(?i)vs|versus|against.*report'
            ],
            UserIntent.EXPLAIN_PARAMETER: [
                r'(?i)what is.*(?:hemoglobin|cholesterol|glucose|rbc|wbc|platelet)',
                r'(?i)explain.*(?:level|value|number|parameter)',
                r'(?i)why.*(?:high|low|normal)|what does.*(?:high|low|normal).*mean',
                r'(?i)(?:hemoglobin|cholesterol|glucose|rbc|wbc|platelet).*mean'
            ],
            UserIntent.HEALTH_ADVICE: [
                r'(?i)what should i.*(?:do|eat|avoid)|food.*recommend',
                r'(?i)recommend|advice|suggest|help.*health',
                r'(?i)diet|exercise|lifestyle|food.*advice',
                r'(?i)how.*improve|what.*eat|nutrition'
            ],
            UserIntent.RISK_ASSESSMENT: [
                r'(?i)risk|danger|concern|worry|problem.*health',
                r'(?i)serious|bad|good|healthy.*am.*i',
                r'(?i)should i be.*(?:worried|concerned)|at.*risk',
                r'(?i)health.*risk|medical.*risk'
            ],
            UserIntent.TREND_ANALYSIS: [
                r'(?i)trend|pattern|change.*time|over.*time',
                r'(?i)getting.*(?:better|worse)|improving|declining',
                r'(?i)progress|improvement|decline|history',
                r'(?i)track.*change|monitor.*progress'
            ]
        }
        
        # Context keywords for intent refinement
        self.context_keywords = {
            'urgency': ['urgent', 'emergency', 'immediately', 'asap', 'quickly'],
            'uncertainty': ['maybe', 'perhaps', 'not sure', 'confused', 'unclear'],
            'comparison': ['compare', 'versus', 'vs', 'difference', 'between'],
            'temporal': ['now', 'before', 'after', 'next', 'previous', 'last'],
            'emotional': ['worried', 'scared', 'concerned', 'happy', 'relieved']
        }
        
        # LLM system prompt for intent inference
        self.intent_system_prompt = """You are an expert at understanding user intentions in medical contexts.

Analyze the user's message and determine their true intent, even if not explicitly stated.

Consider:
- Literal request vs underlying goal
- Emotional context and concerns
- Implicit questions or needs
- Medical anxiety or confusion

Return JSON with:
{
    "primary_intent": "intent_name",
    "confidence": 0.0-1.0,
    "secondary_intents": ["intent2", "intent3"],
    "emotional_context": "calm|anxious|confused|urgent",
    "implicit_questions": ["question1", "question2"],
    "suggested_actions": ["action1", "action2"],
    "clarification_needed": true/false,
    "reasoning": "explanation"
}

Intents: analyze_report, compare_reports, explain_parameter, health_advice, risk_assessment, trend_analysis, general_question, export_data, clarification_needed"""
    
    def infer_intent(self, user_message: str, conversation_history: List[Dict] = None, 
                    user_context: Dict = None) -> Dict[str, Any]:
        """
        Infer user intent from message, conversation history, and context
        
        Args:
            user_message: Current user input
            conversation_history: Previous conversation messages
            user_context: User state and available data context
            
        Returns:
            Intent analysis with confidence scores and suggested actions
        """
        # Step 1: Pattern-based intent detection (fast)
        pattern_intent = self._pattern_based_inference(user_message)
        
        # Step 2: Context-aware refinement
        context_refined = self._refine_with_context(
            pattern_intent, conversation_history, user_context
        )
        
        # Step 3: LLM-based deep analysis (for complex cases)
        if context_refined['confidence'] < 0.7 or context_refined['clarification_needed']:
            llm_analysis = self._llm_intent_analysis(
                user_message, conversation_history, user_context
            )
            # Merge pattern and LLM results
            final_intent = self._merge_intent_analyses(context_refined, llm_analysis)
        else:
            final_intent = context_refined
        
        # Step 4: Generate actionable response plan
        final_intent['action_plan'] = self._generate_action_plan(final_intent, user_context)
        
        return final_intent
    
    def _pattern_based_inference(self, message: str) -> Dict[str, Any]:
        """Fast pattern-based intent detection"""
        message_lower = message.lower()
        intent_scores = {}
        
        # Score each intent based on pattern matches
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message):
                    score += 1
            
            if score > 0:
                intent_scores[intent] = score / len(patterns)
        
        # Determine primary intent
        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[primary_intent]
            
            # Get secondary intents
            secondary_intents = [
                intent.value for intent, score in intent_scores.items() 
                if intent != primary_intent and score > 0.3
            ]
        else:
            primary_intent = UserIntent.GENERAL_QUESTION
            confidence = 0.3
            secondary_intents = []
        
        # Detect emotional context
        emotional_context = self._detect_emotional_context(message)
        
        # Check if clarification needed
        clarification_needed = self._needs_clarification(message, confidence)
        
        return {
            'primary_intent': primary_intent.value,
            'confidence': confidence,
            'secondary_intents': secondary_intents,
            'emotional_context': emotional_context,
            'clarification_needed': clarification_needed,
            'method': 'pattern_based'
        }
    
    def _detect_emotional_context(self, message: str) -> str:
        """Detect emotional context from message"""
        message_lower = message.lower()
        
        # Check for emotional keywords
        for emotion, keywords in self.context_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if emotion == 'uncertainty':
                    return 'confused'
                elif emotion == 'emotional':
                    if any(word in message_lower for word in ['worried', 'scared', 'concerned']):
                        return 'anxious'
                    else:
                        return 'positive'
        
        # Check for urgency indicators
        if any(word in message_lower for word in self.context_keywords['urgency']):
            return 'urgent'
        
        # Check for question marks and uncertainty
        if '?' in message and any(word in message_lower for word in ['what', 'how', 'why', 'should']):
            return 'questioning'
        
        return 'calm'
    
    def _needs_clarification(self, message: str, confidence: float) -> bool:
        """Determine if clarification is needed"""
        # Low confidence indicates unclear intent
        if confidence < 0.5:
            return True
        
        # Very short messages might need clarification
        if len(message.split()) < 3:
            return True
        
        # Vague terms indicate need for clarification
        vague_terms = ['this', 'that', 'it', 'something', 'anything', 'help']
        message_words = message.lower().split()
        
        if len([word for word in message_words if word in vague_terms]) > 1:
            return True
        
        return False
    
    def _refine_with_context(self, pattern_intent: Dict, conversation_history: List[Dict], 
                           user_context: Dict) -> Dict[str, Any]:
        """Refine intent using conversation history and user context"""
        refined_intent = pattern_intent.copy()
        
        # Boost confidence if context supports the intent
        if user_context:
            # If user has multiple reports, boost comparison intents
            if user_context.get('report_count', 0) > 1:
                if pattern_intent['primary_intent'] in ['compare_reports', 'trend_analysis']:
                    refined_intent['confidence'] = min(1.0, refined_intent['confidence'] + 0.2)
            
            # If user has abnormal results, boost health advice intent
            if user_context.get('has_abnormal_results', False):
                if pattern_intent['primary_intent'] == 'health_advice':
                    refined_intent['confidence'] = min(1.0, refined_intent['confidence'] + 0.15)
        
        # Use conversation history for context
        if conversation_history:
            recent_topics = self._extract_recent_topics(conversation_history)
            
            # If user was asking about specific parameters, boost explain_parameter
            if 'parameters' in recent_topics and pattern_intent['primary_intent'] == 'explain_parameter':
                refined_intent['confidence'] = min(1.0, refined_intent['confidence'] + 0.1)
        
        return refined_intent
    
    def _extract_recent_topics(self, conversation_history: List[Dict]) -> List[str]:
        """Extract topics from recent conversation"""
        topics = []
        
        # Look at last 5 messages
        recent_messages = conversation_history[-5:] if conversation_history else []
        
        for message in recent_messages:
            content = message.get('content', '').lower()
            
            # Extract medical parameter mentions
            medical_terms = ['hemoglobin', 'cholesterol', 'glucose', 'rbc', 'wbc', 'platelet']
            for term in medical_terms:
                if term in content:
                    topics.append('parameters')
                    break
            
            # Extract other topics
            if any(word in content for word in ['compare', 'difference', 'change']):
                topics.append('comparison')
            
            if any(word in content for word in ['risk', 'danger', 'concern']):
                topics.append('risk')
        
        return list(set(topics))
    
    def _llm_intent_analysis(self, message: str, conversation_history: List[Dict], 
                           user_context: Dict) -> Dict[str, Any]:
        """Deep intent analysis using LLM"""
        try:
            # Prepare context for LLM
            context_info = ""
            if user_context:
                context_info = f"User Context: {json.dumps(user_context, indent=2)}\n"
            
            history_info = ""
            if conversation_history:
                recent_history = conversation_history[-3:]  # Last 3 messages
                history_info = "Recent Conversation:\n"
                for msg in recent_history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')[:100]  # Truncate for brevity
                    history_info += f"{role}: {content}\n"
            
            prompt = f"""Analyze this user message for intent:

{context_info}
{history_info}

User Message: "{message}"

Determine the user's true intent and provide analysis in the specified JSON format."""
            
            # Call LLM
            response = self._call_ollama(prompt, self.intent_system_prompt)
            
            # Parse JSON response
            try:
                llm_result = json.loads(response)
                llm_result['method'] = 'llm_analysis'
                return llm_result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'primary_intent': 'general_question',
                    'confidence': 0.4,
                    'secondary_intents': [],
                    'emotional_context': 'calm',
                    'clarification_needed': True,
                    'method': 'llm_fallback',
                    'error': 'JSON parsing failed'
                }
        
        except Exception as e:
            # Fallback on LLM failure
            return {
                'primary_intent': 'general_question',
                'confidence': 0.3,
                'secondary_intents': [],
                'emotional_context': 'calm',
                'clarification_needed': True,
                'method': 'llm_error',
                'error': str(e)
            }
    
    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call Ollama API for LLM analysis"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.8,
                    "num_predict": 500
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return ""
        except Exception:
            return ""
    
    def _merge_intent_analyses(self, pattern_result: Dict, llm_result: Dict) -> Dict[str, Any]:
        """Merge pattern-based and LLM-based intent analyses"""
        # Use LLM result as primary if it has higher confidence
        if llm_result.get('confidence', 0) > pattern_result.get('confidence', 0):
            primary = llm_result
            secondary = pattern_result
        else:
            primary = pattern_result
            secondary = llm_result
        
        # Merge the results
        merged = primary.copy()
        
        # Combine secondary intents
        all_secondary = set(primary.get('secondary_intents', []))
        all_secondary.update(secondary.get('secondary_intents', []))
        if secondary.get('primary_intent') != primary.get('primary_intent'):
            all_secondary.add(secondary.get('primary_intent'))
        
        merged['secondary_intents'] = list(all_secondary)
        merged['analysis_methods'] = [primary.get('method'), secondary.get('method')]
        
        return merged
    
    def _generate_action_plan(self, intent_analysis: Dict, user_context: Dict) -> List[Dict[str, Any]]:
        """Generate actionable response plan based on inferred intent"""
        primary_intent = intent_analysis.get('primary_intent')
        emotional_context = intent_analysis.get('emotional_context', 'calm')
        
        action_plan = []
        
        # Generate actions based on primary intent
        if primary_intent == 'analyze_report':
            if user_context and user_context.get('report_count', 0) > 0:
                action_plan.append({
                    'action': 'show_report_summary',
                    'priority': 'high',
                    'description': 'Display comprehensive report analysis'
                })
            else:
                action_plan.append({
                    'action': 'request_report_upload',
                    'priority': 'high',
                    'description': 'Ask user to upload a blood report'
                })
        
        elif primary_intent == 'compare_reports':
            if user_context and user_context.get('report_count', 0) > 1:
                action_plan.append({
                    'action': 'show_comparison_analysis',
                    'priority': 'high',
                    'description': 'Display comparative analysis between reports'
                })
            else:
                action_plan.append({
                    'action': 'explain_comparison_requirements',
                    'priority': 'high',
                    'description': 'Explain that multiple reports are needed for comparison'
                })
        
        elif primary_intent == 'health_advice':
            action_plan.append({
                'action': 'provide_personalized_recommendations',
                'priority': 'high',
                'description': 'Generate health advice based on report findings'
            })
            
            if emotional_context == 'anxious':
                action_plan.append({
                    'action': 'provide_reassurance',
                    'priority': 'medium',
                    'description': 'Offer calming context and perspective'
                })
        
        elif primary_intent == 'risk_assessment':
            action_plan.append({
                'action': 'show_risk_analysis',
                'priority': 'high',
                'description': 'Display risk assessment and factors'
            })
            
            action_plan.append({
                'action': 'medical_disclaimer',
                'priority': 'high',
                'description': 'Emphasize need for professional medical consultation'
            })
        
        # Add clarification action if needed
        if intent_analysis.get('clarification_needed', False):
            action_plan.insert(0, {
                'action': 'ask_clarifying_questions',
                'priority': 'highest',
                'description': 'Ask questions to better understand user needs'
            })
        
        # Add emotional support if user seems anxious
        if emotional_context in ['anxious', 'urgent']:
            action_plan.append({
                'action': 'provide_emotional_support',
                'priority': 'medium',
                'description': 'Offer reassurance and context'
            })
        
        return action_plan


# Convenience function for easy integration
def infer_user_intent(message: str, conversation_history: List[Dict] = None, 
                     user_context: Dict = None) -> Dict[str, Any]:
    """
    Convenience function to infer user intent
    
    Args:
        message: User's current message
        conversation_history: Previous conversation messages
        user_context: Available user and system context
        
    Returns:
        Intent analysis with action plan
    """
    engine = IntentInferenceEngine()
    return engine.infer_intent(message, conversation_history, user_context)