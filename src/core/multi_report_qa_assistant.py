"""
Multi-Report Q&A Assistant
Enhanced Q&A system for handling multiple blood reports with session-based chat memory
"""

import json
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .qa_assistant import BloodReportQAAssistant


class MultiReportQAAssistant:
    """
    Enhanced Q&A Assistant for multiple blood reports with comparative analysis
    and session-based chat memory
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "mistral:7b-instruct"
        self.fallback_model = "mistral:instruct"
        
        # Multi-report data storage
        self.reports_data = {}  # report_id -> analysis_data
        self.comparison_data = None
        self.session_memory = []  # Chat history for context
        self._response_cache = {}
        self._model_warmed_up = False
        
        # Enhanced system prompt for multi-report scenarios
        self.system_prompt = """Medical AI for multiple blood reports. Answer using ONLY report data.

Multi-Report Rules:
- Reference specific reports when asked (Report_1, Report_2, etc.)
- Compare values across reports when relevant
- Identify trends and changes between reports
- Maintain context from previous questions in session

Format: Direct answer → Brief reason → Practical advice
Safety: "Based on reports, not diagnosis. Consult doctor."
"""
    
    def load_multi_report_data(self, reports_data: Dict[str, Any], comparison_data: Optional[Dict[str, Any]] = None) -> None:
        """Load multiple report analysis data for Q&A"""
        self.reports_data = reports_data
        self.comparison_data = comparison_data
        self.session_memory = []  # Reset session memory for new data
        self._warm_up_model()
    
    def _warm_up_model(self) -> None:
        """Warm up the Mistral model for faster subsequent responses"""
        if self._model_warmed_up or not self._is_ollama_available():
            return
        
        try:
            warm_up_payload = {
                "model": self.model_name,
                "prompt": "Hello",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 10,
                    "num_predict": 10,
                    "num_ctx": 512
                }
            }
            
            requests.post(
                f"{self.ollama_url}/api/generate",
                json=warm_up_payload,
                timeout=10
            )
            self._model_warmed_up = True
        except Exception:
            pass
    
    def answer_question(self, question: str, use_streaming: bool = False) -> str:
        """
        Answer a question about multiple reports with session context
        """
        if not self.reports_data:
            return "No blood report analysis data is currently loaded."
        
        # Add question to session memory
        self.session_memory.append({
            'type': 'question',
            'content': question,
            'timestamp': datetime.now().isoformat()
        })
        
        # Preprocess question for multi-report context
        processed_question = self._preprocess_multi_report_question(question)
        
        # Enhanced caching with session context
        cache_key = self._get_multi_report_cache_key(processed_question)
        if cache_key in self._response_cache:
            response = self._response_cache[cache_key]
            self._add_response_to_memory(response)
            return response
        
        # Check if Ollama is available
        if not self._is_ollama_available():
            return "AI service is not available. Please ensure Ollama is running with Mistral model."
        
        # Determine which reports are relevant to the question
        relevant_reports = self._identify_relevant_reports(processed_question)
        
        # Extract report data for the prompt
        report_data = self._extract_multi_report_data(relevant_reports, processed_question)
        if not report_data:
            return "No relevant report data available for analysis."
        
        # Create the multi-report prompt with session context
        full_prompt = self._create_multi_report_prompt(report_data, processed_question)
        
        # Send to Mistral LLM
        try:
            response = self._query_mistral_multi_report(full_prompt)
            
            # Cache the response
            self._response_cache[cache_key] = response
            
            # Add response to session memory
            self._add_response_to_memory(response)
            
            # Limit cache size
            if len(self._response_cache) > 100:
                oldest_keys = list(self._response_cache.keys())[:20]
                for key in oldest_keys:
                    del self._response_cache[key]
            
            return response
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    def _preprocess_multi_report_question(self, question: str) -> str:
        """Preprocess question to handle multi-report references"""
        question = question.strip()
        question_lower = question.lower()
        
        # Detect multi-report keywords
        multi_report_keywords = {
            "compare": "comparison",
            "difference": "comparison", 
            "between reports": "comparison",
            "first report": "Report_1",
            "second report": "Report_2",
            "latest report": "latest",
            "previous report": "previous",
            "trend": "trend_analysis",
            "change": "trend_analysis",
            "improvement": "trend_analysis",
            "worse": "trend_analysis"
        }
        
        # Add context markers for better processing
        for keyword, context in multi_report_keywords.items():
            if keyword in question_lower:
                question = f"[{context}] {question}"
                break
        
        return question
    
    def _identify_relevant_reports(self, question: str) -> List[str]:
        """Identify which reports are relevant to the question"""
        question_lower = question.lower()
        
        # Check for specific report references
        if "report_1" in question_lower or "first report" in question_lower:
            return ["Report_1"]
        elif "report_2" in question_lower or "second report" in question_lower:
            return ["Report_2"]
        elif "latest" in question_lower:
            # Return the highest numbered report
            report_ids = sorted(self.reports_data.keys())
            return [report_ids[-1]] if report_ids else []
        elif "previous" in question_lower:
            # Return all but the latest
            report_ids = sorted(self.reports_data.keys())
            return report_ids[:-1] if len(report_ids) > 1 else []
        elif any(keyword in question_lower for keyword in ["compare", "difference", "trend", "change"]):
            # Return all reports for comparison
            return list(self.reports_data.keys())
        else:
            # Default: return all reports
            return list(self.reports_data.keys())
    
    def _extract_multi_report_data(self, relevant_reports: List[str], question: str) -> str:
        """Extract and format data from multiple reports"""
        try:
            report_sections = []
            
            for report_id in relevant_reports:
                if report_id not in self.reports_data:
                    continue
                
                analysis_data = self.reports_data[report_id]
                
                # Extract parameters for this report
                parameters = []
                if 'phase2_result' in analysis_data and analysis_data['phase2_result']:
                    phase2_data = analysis_data['phase2_result']
                    if 'phase2_full_result' in phase2_data:
                        param_interp = phase2_data['phase2_full_result'].get('parameter_interpretation', {})
                        interpretations = param_interp.get('interpretations', [])
                        
                        for interp in interpretations:
                            param_data = {
                                'name': interp.get('test_name', 'Unknown'),
                                'value': interp.get('value', 'Unknown'),
                                'unit': interp.get('unit', ''),
                                'range': interp.get('reference_range', 'Unknown'),
                                'status': interp.get('classification', 'Unknown')
                            }
                            parameters.append(param_data)
                
                if parameters:
                    # Create report section
                    report_text = f"\n{report_id}:\n"
                    
                    # Prioritize abnormal values
                    abnormal_params = [p for p in parameters if p['status'] != 'Normal']
                    normal_params = [p for p in parameters if p['status'] == 'Normal']
                    
                    if abnormal_params:
                        report_text += "ABNORMAL:\n"
                        for p in abnormal_params[:6]:
                            unit = f" {p['unit']}" if p['unit'] else ""
                            report_text += f"  {p['name']}: {p['value']}{unit} ({p['status']}, Normal: {p['range']})\n"
                    
                    if normal_params and len(abnormal_params) < 4:  # Show normal if few abnormal
                        report_text += "NORMAL:\n"
                        for p in normal_params[:4]:
                            unit = f" {p['unit']}" if p['unit'] else ""
                            report_text += f"  {p['name']}: {p['value']}{unit}\n"
                    
                    # Add metadata if available
                    metadata = analysis_data.get('metadata', {})
                    if metadata.get('test_date'):
                        report_text += f"Date: {metadata['test_date']}\n"
                    
                    report_sections.append(report_text)
            
            # Add comparison data if available and relevant
            comparison_text = ""
            if self.comparison_data and len(relevant_reports) > 1:
                comparison_text = self._format_comparison_data(question)
            
            # Combine all sections
            full_data = "REPORTS:\n" + "\n".join(report_sections)
            if comparison_text:
                full_data += f"\n\nCOMPARISONS:\n{comparison_text}"
            
            return full_data
            
        except Exception as e:
            return f"Error extracting report data: {str(e)}"
    
    def _format_comparison_data(self, question: str) -> str:
        """Format comparison data for inclusion in prompt"""
        if not self.comparison_data:
            return ""
        
        try:
            comparison_text = ""
            
            # Add parameter comparisons
            param_comparisons = self.comparison_data.get('parameter_comparisons', {})
            if param_comparisons:
                comparison_text += "PARAMETER CHANGES:\n"
                
                # Show top 5 most significant changes
                for param_name, comparison in list(param_comparisons.items())[:5]:
                    changes = comparison.get('changes', [])
                    if changes:
                        latest_change = changes[-1]  # Most recent change
                        change_type = latest_change.get('change_type', 'stable')
                        percent_change = latest_change.get('percent_change', 0)
                        
                        if abs(percent_change) > 5:  # Only significant changes
                            comparison_text += f"  {param_name}: {change_type} ({percent_change:+.1f}%)\n"
            
            # Add trend analysis
            trend_analysis = self.comparison_data.get('trend_analysis', {})
            if trend_analysis:
                trends = trend_analysis.get('trends', {})
                improving = trends.get('improving', [])
                worsening = trends.get('worsening', [])
                
                if improving or worsening:
                    comparison_text += "TRENDS:\n"
                    if improving:
                        comparison_text += f"  Improving: {', '.join(improving[:3])}\n"
                    if worsening:
                        comparison_text += f"  Worsening: {', '.join(worsening[:3])}\n"
            
            return comparison_text
            
        except Exception:
            return ""
    
    def _create_multi_report_prompt(self, report_data: str, question: str) -> str:
        """Create prompt for multi-report analysis"""
        # Include recent session context for better continuity
        context = ""
        if len(self.session_memory) > 1:
            recent_context = self.session_memory[-3:]  # Last 3 interactions
            context_items = []
            for item in recent_context:
                if item['type'] == 'question':
                    context_items.append(f"Q: {item['content']}")
                elif item['type'] == 'response':
                    # Truncate long responses for context
                    response = item['content'][:100] + "..." if len(item['content']) > 100 else item['content']
                    context_items.append(f"A: {response}")
            
            if context_items:
                context = f"\nRECENT CONTEXT:\n" + "\n".join(context_items[-4:]) + "\n"
        
        prompt = f"""{self.system_prompt}

DATA:
{report_data}{context}

Q: {question}
A:"""
        
        return prompt
    
    def _query_mistral_multi_report(self, prompt: str) -> str:
        """Query Mistral with multi-report optimizations"""
        try:
            self._last_prompt = prompt
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,      # Slightly higher for multi-report reasoning
                    "top_p": 0.8,
                    "max_tokens": 350,       # Longer for multi-report responses
                    "num_predict": 350,
                    "num_ctx": 1024,         # Larger context for multiple reports
                    "repeat_penalty": 1.0,
                    "top_k": 15,
                    "num_thread": 4,
                    "stop": ["Q:", "DATA:", "A:", "\n\nQ:", "\n\nDATA:", "Question:", "Answer:"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=15  # Longer timeout for multi-report processing
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                if answer:
                    # Clean up the response
                    for stop_word in ["A:", "Answer:", "DATA:", "Q:"]:
                        if stop_word in answer:
                            answer = answer.split(stop_word)[-1].strip()
                    
                    # Ensure reasonable length
                    if len(answer) > 1000:
                        answer = answer[:1000] + "..."
                    
                    return answer if answer else "Response generated but empty."
                else:
                    return "No response generated from the AI model."
            else:
                return f"Error from AI service: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "AI service timeout. Multi-report analysis may take longer - please try again."
        except Exception as e:
            return f"Error communicating with AI service: {str(e)}"
    
    def _add_response_to_memory(self, response: str) -> None:
        """Add response to session memory"""
        self.session_memory.append({
            'type': 'response',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limit memory size
        if len(self.session_memory) > 20:
            self.session_memory = self.session_memory[-20:]
    
    def _get_multi_report_cache_key(self, question: str) -> str:
        """Generate cache key for multi-report questions"""
        # Include report count and comparison availability in cache key
        report_count = len(self.reports_data)
        has_comparison = self.comparison_data is not None
        
        # Normalize question
        normalized = question.lower().strip()
        for word in ["what is", "tell me about", "can you", "please", "?", "."]:
            normalized = normalized.replace(word, "")
        normalized = " ".join(normalized.split())
        
        # Create unique key including multi-report context
        reports_hash = hash(str(sorted(self.reports_data.keys())))
        comparison_hash = hash(str(self.comparison_data)) if self.comparison_data else 0
        
        return f"multi_{normalized}_{report_count}_{has_comparison}_{reports_hash}_{comparison_hash}"
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "").lower() for model in models]
                
                if any(self.model_name.lower() in name for name in model_names):
                    return True
                elif any("mistral" in name for name in model_names):
                    for name in model_names:
                        if "mistral" in name:
                            self.model_name = models[model_names.index(name)].get("name", self.fallback_model)
                            break
                    return True
                return False
            return False
        except Exception:
            return False
    
    def get_available_topics(self) -> List[str]:
        """Get list of topics available for multi-report analysis"""
        if not self.reports_data:
            return ["No analysis data loaded"]
        
        topics = [
            "Overall health summary across all reports",
            "Comparison between reports",
            "Trends and changes over time",
            "Abnormal values in any report"
        ]
        
        # Add report-specific topics
        for report_id in sorted(self.reports_data.keys()):
            topics.append(f"Specific analysis of {report_id}")
        
        # Add comparison topics if multiple reports
        if len(self.reports_data) > 1:
            topics.extend([
                "Parameter improvements or deterioration",
                "Risk factor changes",
                "Lifestyle recommendation updates"
            ])
        
        return topics
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        return {
            "reports_loaded": len(self.reports_data),
            "report_ids": list(self.reports_data.keys()),
            "comparison_available": self.comparison_data is not None,
            "questions_asked": len([item for item in self.session_memory if item['type'] == 'question']),
            "session_length": len(self.session_memory),
            "cache_size": len(self._response_cache)
        }
    
    def clear_session(self) -> None:
        """Clear session memory and cache"""
        self.session_memory = []
        self._response_cache = {}
    
    def get_last_prompt(self) -> str:
        """Get the last prompt sent to the LLM (for debugging)"""
        return getattr(self, '_last_prompt', "No prompt available")


# Convenience function for creating multi-report assistant
def create_multi_report_qa_assistant(reports_data: Dict[str, Any], comparison_data: Optional[Dict[str, Any]] = None) -> MultiReportQAAssistant:
    """Create and load a multi-report Q&A assistant with analysis data"""
    assistant = MultiReportQAAssistant()
    assistant.load_multi_report_data(reports_data, comparison_data)
    return assistant