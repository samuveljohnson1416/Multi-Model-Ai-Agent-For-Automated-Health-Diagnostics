"""
Clarifying Question Generator
Generates intelligent clarifying questions when user requests are ambiguous or incomplete
"""

import json
import requests
from typing import Dict, List, Any, Optional
from enum import Enum


class QuestionType(Enum):
    """Types of clarifying questions"""
    SCOPE_CLARIFICATION = "scope_clarification"
    PARAMETER_SPECIFICATION = "parameter_specification"
    TIME_FRAME = "time_frame"
    COMPARISON_TARGET = "comparison_target"
    DETAIL_LEVEL = "detail_level"
    CONTEXT_GATHERING = "context_gathering"
    PREFERENCE_ELICITATION = "preference_elicitation"


class ClarifyingQuestionGenerator:
    """
    Generates intelligent clarifying questions to resolve ambiguity in user requests
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "mistral:7b-instruct"
        
        # Template questions for different scenarios
        self.question_templates = {
            QuestionType.SCOPE_CLARIFICATION: [
                "Would you like me to analyze {scope_options}?",
                "Are you interested in {specific_aspect} or a general overview?",
                "Should I focus on {focus_area} specifically?"
            ],
            QuestionType.PARAMETER_SPECIFICATION: [
                "Which specific parameters are you most concerned about?",
                "Are you asking about {parameter_list}?",
                "Would you like details on {suggested_parameters}?"
            ],
            QuestionType.TIME_FRAME: [
                "Are you asking about your latest report or comparing over time?",
                "Should I look at {time_options}?",
                "Which time period interests you most?"
            ],
            QuestionType.COMPARISON_TARGET: [
                "What would you like me to compare your results against?",
                "Should I compare {comparison_options}?",
                "Are you interested in comparing with {reference_points}?"
            ],
            QuestionType.DETAIL_LEVEL: [
                "Would you prefer a quick summary or detailed explanation?",
                "How much detail would be helpful for you?",
                "Should I provide {detail_options}?"
            ],
            QuestionType.CONTEXT_GATHERING: [
                "To give you better advice, could you tell me {context_needed}?",
                "It would help to know {additional_info}.",
                "For more personalized insights, I'd like to understand {context_request}."
            ]
        }
        
        # LLM system prompt for question generation
        self.question_system_prompt = """You are an expert at generating helpful clarifying questions for medical report analysis.

When users make vague or ambiguous requests, generate 2-3 specific, helpful questions that will:
1. Clarify their true intent
2. Gather necessary context
3. Help them get the most relevant information

Make questions:
- Specific and actionable
- Medically appropriate
- User-friendly (avoid jargon)
- Focused on their likely needs

Return JSON:
{
    "questions": [
        {
            "question": "specific question text",
            "type": "question_type",
            "rationale": "why this question helps",
            "suggested_answers": ["option1", "option2", "option3"]
        }
    ],
    "primary_question": "most important question",
    "context_needed": "what information would help most"
}"""
    
    def generate_clarifying_questions(self, user_message: str, intent_analysis: Dict, 
                                    user_context: Dict = None) -> Dict[str, Any]:
        """
        Generate clarifying questions based on ambiguous user input
        
        Args:
            user_message: Original user message
            intent_analysis: Results from intent inference
            user_context: Available context about user and reports
            
        Returns:
            Generated clarifying questions with rationale
        """
        # Determine what type of clarification is needed
        clarification_needs = self._analyze_clarification_needs(
            user_message, intent_analysis, user_context
        )
        
        # Generate questions using templates and LLM
        template_questions = self._generate_template_questions(clarification_needs, user_context)
        llm_questions = self._generate_llm_questions(user_message, intent_analysis, user_context)
        
        # Combine and rank questions
        all_questions = self._combine_and_rank_questions(template_questions, llm_questions)
        
        # Select best questions
        final_questions = self._select_best_questions(all_questions, clarification_needs)
        
        return {
            'questions': final_questions,
            'clarification_strategy': clarification_needs,
            'user_message': user_message,
            'generated_at': 'now'
        }
    
    def _analyze_clarification_needs(self, message: str, intent_analysis: Dict, 
                                   user_context: Dict) -> Dict[str, Any]:
        """Analyze what type of clarification is needed"""
        needs = {
            'ambiguity_sources': [],
            'missing_context': [],
            'question_types_needed': [],
            'priority_level': 'medium'
        }
        
        message_lower = message.lower()
        primary_intent = intent_analysis.get('primary_intent')
        confidence = intent_analysis.get('confidence', 0)
        
        # Analyze ambiguity sources
        if confidence < 0.5:
            needs['ambiguity_sources'].append('low_intent_confidence')
            needs['priority_level'] = 'high'
        
        # Check for vague pronouns
        vague_pronouns = ['this', 'that', 'it', 'these', 'those']
        if any(pronoun in message_lower.split() for pronoun in vague_pronouns):
            needs['ambiguity_sources'].append('vague_references')
            needs['question_types_needed'].append(QuestionType.SCOPE_CLARIFICATION)
        
        # Check for incomplete requests
        if len(message.split()) < 4:
            needs['ambiguity_sources'].append('too_brief')
            needs['question_types_needed'].append(QuestionType.CONTEXT_GATHERING)
        
        # Intent-specific clarification needs
        if primary_intent == 'compare_reports':
            if not user_context or user_context.get('report_count', 0) < 2:
                needs['missing_context'].append('insufficient_reports')
                needs['question_types_needed'].append(QuestionType.COMPARISON_TARGET)
            
            if 'what' in message_lower and 'compare' in message_lower:
                needs['question_types_needed'].append(QuestionType.PARAMETER_SPECIFICATION)
        
        elif primary_intent == 'explain_parameter':
            # Check if specific parameter mentioned
            medical_terms = ['hemoglobin', 'cholesterol', 'glucose', 'rbc', 'wbc']
            if not any(term in message_lower for term in medical_terms):
                needs['missing_context'].append('parameter_not_specified')
                needs['question_types_needed'].append(QuestionType.PARAMETER_SPECIFICATION)
        
        elif primary_intent == 'health_advice':
            if 'what should i' in message_lower:
                needs['question_types_needed'].append(QuestionType.SCOPE_CLARIFICATION)
                needs['question_types_needed'].append(QuestionType.DETAIL_LEVEL)
        
        # Check for temporal ambiguity
        temporal_words = ['when', 'time', 'now', 'before', 'after']
        if any(word in message_lower for word in temporal_words):
            needs['question_types_needed'].append(QuestionType.TIME_FRAME)
        
        return needs
    
    def _generate_template_questions(self, clarification_needs: Dict, 
                                   user_context: Dict) -> List[Dict[str, Any]]:
        """Generate questions using predefined templates"""
        questions = []
        
        for question_type in clarification_needs.get('question_types_needed', []):
            templates = self.question_templates.get(question_type, [])
            
            for template in templates[:2]:  # Limit to 2 per type
                question_data = self._customize_template(template, question_type, user_context)
                if question_data:
                    questions.append({
                        'question': question_data['question'],
                        'type': question_type.value,
                        'source': 'template',
                        'rationale': question_data['rationale'],
                        'suggested_answers': question_data.get('suggested_answers', [])
                    })
        
        return questions
    
    def _customize_template(self, template: str, question_type: QuestionType, 
                          user_context: Dict) -> Optional[Dict[str, Any]]:
        """Customize template with context-specific information"""
        if not user_context:
            user_context = {}
        
        customizations = {}
        
        if question_type == QuestionType.SCOPE_CLARIFICATION:
            if user_context.get('report_count', 0) > 1:
                customizations['scope_options'] = "all your reports or focus on specific ones"
                customizations['specific_aspect'] = "overall health trends or specific parameters"
                customizations['focus_area'] = "abnormal results or general health status"
            else:
                customizations['scope_options'] = "your entire report or specific sections"
                customizations['specific_aspect'] = "abnormal values or overall health"
                customizations['focus_area'] = "specific health concerns"
        
        elif question_type == QuestionType.PARAMETER_SPECIFICATION:
            available_params = user_context.get('available_parameters', [])
            if available_params:
                customizations['parameter_list'] = ", ".join(available_params[:3])
                customizations['suggested_parameters'] = " or ".join(available_params[:2])
            else:
                customizations['parameter_list'] = "cholesterol, blood sugar, or blood count"
                customizations['suggested_parameters'] = "cholesterol or blood sugar levels"
        
        elif question_type == QuestionType.TIME_FRAME:
            if user_context.get('report_count', 0) > 1:
                customizations['time_options'] = "your latest results or changes over time"
            else:
                customizations['time_options'] = "current results or historical context"
        
        elif question_type == QuestionType.COMPARISON_TARGET:
            customizations['comparison_options'] = "normal ranges, previous results, or risk factors"
            customizations['reference_points'] = "standard ranges or your previous tests"
        
        elif question_type == QuestionType.DETAIL_LEVEL:
            customizations['detail_options'] = "a quick overview or detailed medical explanation"
        
        elif question_type == QuestionType.CONTEXT_GATHERING:
            customizations['context_needed'] = "your main health concerns"
            customizations['additional_info'] = "what specific aspect worries you most"
            customizations['context_request'] = "your health goals or concerns"
        
        # Apply customizations to template
        try:
            customized_question = template.format(**customizations)
            
            return {
                'question': customized_question,
                'rationale': f"Helps clarify {question_type.value.replace('_', ' ')}",
                'suggested_answers': self._generate_suggested_answers(question_type, user_context)
            }
        except KeyError:
            # Template couldn't be customized, return generic version
            return {
                'question': template,
                'rationale': f"Helps clarify {question_type.value.replace('_', ' ')}",
                'suggested_answers': []
            }
    
    def _generate_suggested_answers(self, question_type: QuestionType, 
                                  user_context: Dict) -> List[str]:
        """Generate suggested answers for questions"""
        if question_type == QuestionType.SCOPE_CLARIFICATION:
            return ["Overall health summary", "Specific abnormal values", "Risk assessment"]
        
        elif question_type == QuestionType.PARAMETER_SPECIFICATION:
            available_params = user_context.get('available_parameters', [])
            if available_params:
                return available_params[:4]
            return ["Cholesterol", "Blood sugar", "Blood count", "Kidney function"]
        
        elif question_type == QuestionType.TIME_FRAME:
            if user_context.get('report_count', 0) > 1:
                return ["Latest report only", "Compare with previous", "Show trends over time"]
            return ["Current results", "Historical context", "Future monitoring"]
        
        elif question_type == QuestionType.DETAIL_LEVEL:
            return ["Quick summary", "Detailed explanation", "Technical details"]
        
        elif question_type == QuestionType.COMPARISON_TARGET:
            return ["Normal ranges", "Previous results", "Age/gender averages"]
        
        return []
    
    def _generate_llm_questions(self, message: str, intent_analysis: Dict, 
                              user_context: Dict) -> List[Dict[str, Any]]:
        """Generate questions using LLM for complex scenarios"""
        try:
            # Prepare context for LLM
            context_info = f"""
User Message: "{message}"
Intent Analysis: {json.dumps(intent_analysis, indent=2)}
User Context: {json.dumps(user_context or {}, indent=2)}
"""
            
            prompt = f"""Generate clarifying questions for this ambiguous medical query:

{context_info}

The user's request is unclear. Generate 2-3 specific questions that will help understand what they really need.

Focus on:
- What specific information they want
- What level of detail is appropriate
- What context would be most helpful

Provide questions in the specified JSON format."""
            
            response = self._call_ollama(prompt, self.question_system_prompt)
            
            try:
                llm_result = json.loads(response)
                questions = []
                
                for q in llm_result.get('questions', []):
                    questions.append({
                        'question': q.get('question', ''),
                        'type': q.get('type', 'general'),
                        'source': 'llm',
                        'rationale': q.get('rationale', ''),
                        'suggested_answers': q.get('suggested_answers', [])
                    })
                
                return questions
            
            except json.JSONDecodeError:
                return []
        
        except Exception:
            return []
    
    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call Ollama API for LLM question generation"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_predict": 400
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            return ""
        except Exception:
            return ""
    
    def _combine_and_rank_questions(self, template_questions: List[Dict], 
                                  llm_questions: List[Dict]) -> List[Dict[str, Any]]:
        """Combine and rank questions by relevance and quality"""
        all_questions = template_questions + llm_questions
        
        # Score questions based on various factors
        for question in all_questions:
            score = 0
            
            # Base score by source
            if question['source'] == 'template':
                score += 0.7  # Templates are reliable
            elif question['source'] == 'llm':
                score += 0.8  # LLM questions are more contextual
            
            # Bonus for having suggested answers
            if question.get('suggested_answers'):
                score += 0.2
            
            # Bonus for clear rationale
            if question.get('rationale') and len(question['rationale']) > 10:
                score += 0.1
            
            # Penalty for very long questions
            if len(question.get('question', '')) > 100:
                score -= 0.1
            
            question['score'] = score
        
        # Sort by score
        return sorted(all_questions, key=lambda x: x.get('score', 0), reverse=True)
    
    def _select_best_questions(self, ranked_questions: List[Dict], 
                             clarification_needs: Dict) -> List[Dict[str, Any]]:
        """Select the best 2-3 questions to present to user"""
        if not ranked_questions:
            return self._generate_fallback_questions(clarification_needs)
        
        # Select top questions, ensuring diversity
        selected = []
        used_types = set()
        
        for question in ranked_questions:
            if len(selected) >= 3:
                break
            
            question_type = question.get('type', 'general')
            
            # Ensure diversity in question types
            if question_type not in used_types or len(selected) == 0:
                selected.append(question)
                used_types.add(question_type)
        
        # Ensure we have at least 2 questions
        if len(selected) < 2 and len(ranked_questions) > len(selected):
            for question in ranked_questions:
                if question not in selected and len(selected) < 3:
                    selected.append(question)
        
        return selected
    
    def _generate_fallback_questions(self, clarification_needs: Dict) -> List[Dict[str, Any]]:
        """Generate fallback questions when other methods fail"""
        return [
            {
                'question': "What specific aspect of your blood report would you like me to focus on?",
                'type': 'scope_clarification',
                'source': 'fallback',
                'rationale': 'Helps narrow down the user\'s area of interest',
                'suggested_answers': ["Abnormal values", "Overall health", "Specific parameters"]
            },
            {
                'question': "Would you prefer a quick summary or detailed explanation?",
                'type': 'detail_level',
                'source': 'fallback',
                'rationale': 'Determines appropriate level of detail for response',
                'suggested_answers': ["Quick summary", "Detailed explanation", "Technical details"]
            }
        ]


# Convenience function for easy integration
def generate_clarifying_questions(user_message: str, intent_analysis: Dict, 
                                user_context: Dict = None) -> Dict[str, Any]:
    """
    Generate clarifying questions for ambiguous user input
    
    Args:
        user_message: User's original message
        intent_analysis: Results from intent inference engine
        user_context: Available context about user and reports
        
    Returns:
        Generated clarifying questions with rationale
    """
    generator = ClarifyingQuestionGenerator()
    return generator.generate_clarifying_questions(user_message, intent_analysis, user_context)