"""
Blood Report Q&A Assistant
Uses Mistral LLM with strict medical prompting for constrained Q&A
"""

import json
import requests
from typing import Dict, List, Any, Optional


class BloodReportQAAssistant:
    """
    Medical Report Question-Answering Assistant using Mistral LLM.
    Sends questions with report data to LLM using strict medical prompt.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.analysis_data = None
        self.ollama_url = ollama_url
        self.model_name = "mistral:instruct"
        
        # Strict medical prompt template
        self.system_prompt = """You are a Medical Report Question–Answering Assistant.
You are NOT a general chatbot.
You exist ONLY to answer questions about a single uploaded medical report.
The user has already uploaded a blood report.
The extracted and validated report data provided to you is COMPLETE, AUTHORITATIVE, and the ONLY source of truth.

--------------------------------------------------
STRICT SCOPE RULES (NON-NEGOTIABLE)
--------------------------------------------------
1. You MUST answer ONLY questions that are directly related to:
   - Parameters in the uploaded report
   - Their values, units, reference ranges, and status
   - Patterns or summaries derived from the report
   - Recommendations explicitly linked to report findings

2. You MUST NOT:
   - Answer general medical questions
   - Use external medical knowledge
   - Diagnose diseases
   - Suggest medications or treatments
   - Guess or infer missing information
   - Hallucinate values, conditions, or causes

--------------------------------------------------
UNRELATED OR OUT-OF-SCOPE QUESTIONS
--------------------------------------------------
If the user asks ANY question that cannot be answered using the provided report data, respond EXACTLY with:
"I can only answer questions related to the uploaded medical report."

--------------------------------------------------
MISSING INFORMATION HANDLING
--------------------------------------------------
If the user asks about something that is medical but NOT present in the report, respond with:
"The requested information is not available in the uploaded report."

--------------------------------------------------
HOW YOU MUST ANSWER
--------------------------------------------------
- Base every answer ONLY on the provided report data
- Keep answers clear, factual, and simple
- Use non-alarming, informational language
- If helpful, quote relevant parameter names and values
- Keep responses concise and readable

--------------------------------------------------
OUTPUT STYLE
--------------------------------------------------
- Plain text response
- No markdown
- No emojis
- No extra commentary
- No medical diagnosis

--------------------------------------------------
FINAL SAFETY RULE
--------------------------------------------------
If you are unsure whether a question is allowed, ASSUME IT IS NOT and politely refuse.
"""
    
    def load_analysis_data(self, analysis_result: Dict[str, Any]) -> None:
        """Load blood report analysis data for Q&A"""
        self.analysis_data = analysis_result
    
    def answer_question(self, question: str) -> str:
        """
        Answer a question using Mistral LLM with strict medical prompting
        """
        if not self.analysis_data:
            return "No blood report analysis data is currently loaded."
        
        # Check if Ollama is available
        if not self._is_ollama_available():
            return "AI service is not available. Please ensure Ollama is running with Mistral model."
        
        # Extract report data for the prompt
        report_data = self._extract_report_data()
        if not report_data:
            return "No report data available for analysis."
        
        # Create the full prompt
        full_prompt = self._create_prompt(report_data, question)
        
        # Send to Mistral LLM
        try:
            response = self._query_mistral(full_prompt)
            return response
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any("mistral" in model.get("name", "").lower() for model in models)
            return False
        except Exception:
            return False
    
    def _extract_report_data(self) -> str:
        """Extract and format report data for the prompt"""
        try:
            # Get parameter data from analysis
            parameters = []
            
            if 'phase2_full_result' in self.analysis_data:
                param_interp = self.analysis_data['phase2_full_result'].get('parameter_interpretation', {})
                interpretations = param_interp.get('interpretations', [])
                
                for interp in interpretations:
                    param_data = {
                        'test_name': interp.get('test_name', 'Unknown'),
                        'value': interp.get('value', 'Unknown'),
                        'unit': interp.get('unit', ''),
                        'reference_range': interp.get('reference_range', 'Unknown'),
                        'classification': interp.get('classification', 'Unknown')
                    }
                    parameters.append(param_data)
            
            # Format as structured text
            if parameters:
                report_text = "BLOOD REPORT PARAMETERS:\n"
                for param in parameters:
                    unit_text = f" {param['unit']}" if param['unit'] else ""
                    report_text += f"- {param['test_name']}: {param['value']}{unit_text} "
                    report_text += f"(Reference: {param['reference_range']}, Status: {param['classification']})\n"
                
                # Add summary
                total_params = len(parameters)
                normal_count = sum(1 for p in parameters if p['classification'] == 'Normal')
                high_count = sum(1 for p in parameters if p['classification'] == 'High')
                low_count = sum(1 for p in parameters if p['classification'] == 'Low')
                
                report_text += f"\nSUMMARY:\n"
                report_text += f"- Total Parameters: {total_params}\n"
                report_text += f"- Normal: {normal_count}\n"
                report_text += f"- High: {high_count}\n"
                report_text += f"- Low: {low_count}\n"
                
                return report_text
            else:
                return "No parameter data available in the report."
                
        except Exception as e:
            return f"Error extracting report data: {str(e)}"
    
    def _create_prompt(self, report_data: str, question: str) -> str:
        """Create the full prompt for Mistral LLM"""
        prompt = f"""{self.system_prompt}

--------------------------------------------------
BEGIN
--------------------------------------------------
REFERENCE MEDICAL REPORT DATA:
{report_data}

USER QUESTION:
{question}

RESPONSE:"""
        
        return prompt
    
    def _query_mistral(self, prompt: str) -> str:
        """Send prompt to Mistral LLM via Ollama"""
        try:
            # Store the prompt for debugging
            self._last_prompt = prompt
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent, factual responses
                    "top_p": 0.9,
                    "max_tokens": 500,   # Limit response length
                    "stop": ["USER QUESTION:", "REFERENCE MEDICAL REPORT DATA:"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                # Clean up the response
                if answer:
                    # Remove any system prompt leakage
                    if "RESPONSE:" in answer:
                        answer = answer.split("RESPONSE:")[-1].strip()
                    
                    return answer
                else:
                    return "No response generated from the AI model."
            else:
                return f"Error from AI service: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "AI service timeout. Please try again."
        except Exception as e:
            return f"Error communicating with AI service: {str(e)}"
    
    def get_available_topics(self) -> List[str]:
        """Get list of topics that can be answered based on loaded analysis"""
        if not self.analysis_data:
            return ["No analysis data loaded"]
        
        try:
            # Extract parameter names from analysis
            parameters = []
            if 'phase2_full_result' in self.analysis_data:
                param_interp = self.analysis_data['phase2_full_result'].get('parameter_interpretation', {})
                interpretations = param_interp.get('interpretations', [])
                parameters = [interp.get('test_name', 'Unknown') for interp in interpretations]
            
            if parameters:
                topics = [
                    "Individual parameter values and status",
                    "Parameters above or below normal ranges", 
                    "Overall report summary",
                    f"Available parameters: {', '.join(parameters[:5])}"
                ]
                if len(parameters) > 5:
                    topics[-1] += f" and {len(parameters) - 5} others"
                return topics
            else:
                return ["No parameter data available"]
                
        except Exception:
            return ["Error loading analysis data"]
    
    def get_last_prompt(self) -> str:
        """Get the last prompt sent to the LLM (for debugging)"""
        # This would be set by _query_mistral if we want to track it
        return getattr(self, '_last_prompt', "No prompt available")


# Convenience function for integration
def create_qa_assistant(analysis_result: Dict[str, Any]) -> BloodReportQAAssistant:
    """Create and load a Q&A assistant with analysis data"""
    assistant = BloodReportQAAssistant()
    assistant.load_analysis_data(analysis_result)
    return assistant