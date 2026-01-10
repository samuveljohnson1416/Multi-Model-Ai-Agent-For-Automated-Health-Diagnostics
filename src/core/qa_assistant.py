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
        # Try smaller/faster model first, fallback to full model
        self.model_name = "mistral:7b-instruct"  # Try specific tag
        self.fallback_model = "mistral:instruct"
        self._response_cache = {}  # Enhanced response caching
        self._model_warmed_up = False  # Track model warm-up status
        
        # Ultra-streamlined prompt for maximum speed
        self.system_prompt = """Medical AI for blood reports. Answer using ONLY report data.

Rules: Reason from findings → discuss risks/recommendations → add safety note if needed.
Format: Direct answer → Brief reason → Practical advice
Safety: "Based on report, not diagnosis. Consult doctor."
"""
    
    def load_analysis_data(self, analysis_result: Dict[str, Any]) -> None:
        """Load blood report analysis data for Q&A"""
        self.analysis_data = analysis_result
        # Warm up the model when data is loaded
        self._warm_up_model()
    
    def _warm_up_model(self) -> None:
        """Warm up the Mistral model for faster subsequent responses"""
        if self._model_warmed_up or not self._is_ollama_available():
            return
        
        try:
            # Send a simple warm-up query
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
            pass  # Warm-up is optional
    
    def answer_question(self, question: str, use_streaming: bool = False) -> str:
        """
        Answer a question using Mistral LLM with aggressive speed optimizations
        Target: 3-8 seconds response time
        """
        if not self.analysis_data:
            return "No blood report analysis data is currently loaded."
        
        # Preprocess question for better performance
        processed_question = self._preprocess_question(question)
        
        # Enhanced caching with question similarity
        cache_key = self._get_cache_key(processed_question)
        if cache_key in self._response_cache:
            return self._response_cache[cache_key]
        
        # Check if Ollama is available
        if not self._is_ollama_available():
            return "AI service is not available. Please ensure Ollama is running with Mistral model."
        
        # Extract report data for the prompt
        report_data = self._extract_report_data_optimized()
        if not report_data:
            return "No report data available for analysis."
        
        # Create the streamlined prompt
        full_prompt = self._create_optimized_prompt(report_data, processed_question)
        
        # Send to Mistral LLM with speed optimizations
        try:
            response = self._query_mistral_fast(full_prompt)
            
            # Cache the response for future speed (use original question for cache key)
            original_cache_key = self._get_cache_key(question)
            self._response_cache[cache_key] = response
            self._response_cache[original_cache_key] = response  # Cache both versions
            
            # Limit cache size to prevent memory issues
            if len(self._response_cache) > 100:
                # Remove oldest entries
                oldest_keys = list(self._response_cache.keys())[:20]
                for key in oldest_keys:
                    del self._response_cache[key]
            
            return response
        except Exception as e:
            return f"Error processing question: {str(e)}"
    
    def _get_cache_key(self, question: str) -> str:
        """Generate cache key with aggressive question normalization for better cache hits"""
        # Aggressive normalization for better cache hits
        normalized = question.lower().strip()
        
        # Remove common question words and variations
        remove_words = ["what is", "tell me about", "can you", "please", "?", ".", "my", "the"]
        for word in remove_words:
            normalized = normalized.replace(word, "")
        
        # Normalize medical terms
        medical_normalizations = {
            "hemoglobin": "hb",
            "cholesterol": "chol",
            "blood sugar": "glucose",
            "white blood cells": "wbc",
            "red blood cells": "rbc"
        }
        
        for full_term, short_term in medical_normalizations.items():
            normalized = normalized.replace(full_term, short_term)
        
        # Remove extra spaces
        normalized = " ".join(normalized.split())
        
        return f"{normalized}_{hash(str(self.analysis_data))}"
    
    def _preprocess_question(self, question: str) -> str:
        """Preprocess question to make it more direct and faster to process"""
        # Make questions more direct for faster processing
        question = question.strip()
        
        # Convert complex questions to simpler forms
        simplifications = {
            "what are the health risks": "risks",
            "what foods should i eat": "food recommendations", 
            "are there any abnormal": "abnormal values",
            "tell me about my": "",
            "what is my": "",
            "can you explain": "explain"
        }
        
        question_lower = question.lower()
        for complex_phrase, simple_phrase in simplifications.items():
            if complex_phrase in question_lower:
                question = question_lower.replace(complex_phrase, simple_phrase).strip()
                break
        
        return question
    
    def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available with fast model detection"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "").lower() for model in models]
                
                # Check for preferred fast model first
                if any(self.model_name.lower() in name for name in model_names):
                    return True
                # Fallback to any mistral model
                elif any("mistral" in name for name in model_names):
                    # Update to use available model
                    for name in model_names:
                        if "mistral" in name:
                            self.model_name = models[model_names.index(name)].get("name", self.fallback_model)
                            break
                    return True
                return False
            return False
        except Exception:
            return False
    
    def _extract_report_data_optimized(self) -> str:
        """Extract and format report data optimized for faster processing"""
        try:
            # Get parameter data from analysis
            parameters = []
            
            if 'phase2_full_result' in self.analysis_data:
                param_interp = self.analysis_data['phase2_full_result'].get('parameter_interpretation', {})
                interpretations = param_interp.get('interpretations', [])
                
                for interp in interpretations:
                    # Streamlined parameter data
                    param_data = {
                        'name': interp.get('test_name', 'Unknown'),
                        'value': interp.get('value', 'Unknown'),
                        'unit': interp.get('unit', ''),
                        'range': interp.get('reference_range', 'Unknown'),
                        'status': interp.get('classification', 'Unknown')
                    }
                    parameters.append(param_data)
            
            # Compact format for faster processing
            if parameters:
                # Prioritize abnormal values for faster relevance
                abnormal_params = [p for p in parameters if p['status'] != 'Normal']
                normal_params = [p for p in parameters if p['status'] == 'Normal']
                
                report_text = "REPORT:\n"
                
                # Show abnormal first (more relevant for questions)
                if abnormal_params:
                    report_text += "ABNORMAL:\n"
                    for p in abnormal_params[:8]:  # Limit for speed
                        unit = f" {p['unit']}" if p['unit'] else ""
                        report_text += f"{p['name']}: {p['value']}{unit} ({p['status']}, Normal: {p['range']})\n"
                
                # Show some normal values
                if normal_params:
                    report_text += "NORMAL:\n"
                    for p in normal_params[:5]:  # Fewer normal values
                        unit = f" {p['unit']}" if p['unit'] else ""
                        report_text += f"{p['name']}: {p['value']}{unit}\n"
                
                # Quick summary
                total = len(parameters)
                abnormal_count = len(abnormal_params)
                report_text += f"\nSUMMARY: {abnormal_count}/{total} abnormal\n"
                
                return report_text
            else:
                return "No parameter data available."
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _create_optimized_prompt(self, report_data: str, question: str) -> str:
        """Create streamlined prompt for faster LLM processing"""
        # Compact prompt format
        prompt = f"""{self.system_prompt}

DATA:
{report_data}

Q: {question}
A:"""
        
        return prompt
    
    def _query_mistral_fast(self, prompt: str) -> str:
        """Ultra-optimized Mistral query for maximum speed"""
        try:
            # Store the prompt for debugging
            self._last_prompt = prompt
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,      # Very low for speed and consistency
                    "top_p": 0.7,            # More focused
                    "max_tokens": 250,       # Shorter responses for speed
                    "num_predict": 250,      # Match max_tokens
                    "num_ctx": 512,          # Very small context window for speed
                    "repeat_penalty": 1.0,   # No penalty for speed
                    "top_k": 10,             # Very limited vocabulary for speed
                    "num_thread": 4,         # Use multiple threads
                    "stop": ["Q:", "DATA:", "A:", "\n\nQ:", "\n\nDATA:", "Question:", "Answer:"]
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=10  # Aggressive timeout for speed
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                
                # Clean up the response
                if answer:
                    # Remove any prompt leakage
                    for stop_word in ["A:", "Answer:", "DATA:", "Q:"]:
                        if stop_word in answer:
                            answer = answer.split(stop_word)[-1].strip()
                    
                    # Ensure reasonable length for speed
                    if len(answer) > 800:
                        answer = answer[:800] + "..."
                    
                    return answer if answer else "Response generated but empty."
                else:
                    return "No response generated from the AI model."
            else:
                return f"Error from AI service: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "AI service timeout. The model may be busy - please try again."
        except Exception as e:
            return f"Error communicating with AI service: {str(e)}"
    
    def get_available_topics(self) -> List[str]:
        """Get list of topics that can be answered based on loaded analysis"""
        if not self.analysis_data:
            return ["No analysis data loaded"]
        
        try:
            # Extract parameter names from analysis
            parameters = []
            abnormal_params = []
            
            if 'phase2_full_result' in self.analysis_data:
                param_interp = self.analysis_data['phase2_full_result'].get('parameter_interpretation', {})
                interpretations = param_interp.get('interpretations', [])
                
                for interp in interpretations:
                    param_name = interp.get('test_name', 'Unknown')
                    classification = interp.get('classification', 'Unknown')
                    parameters.append(param_name)
                    if classification != 'Normal':
                        abnormal_params.append(f"{param_name} ({classification})")
            
            if parameters:
                topics = [
                    "Overall health summary and patterns",
                    "Abnormal values and their implications",
                    "Diet and lifestyle recommendations",
                    "Risk factors and health concerns"
                ]
                
                if abnormal_params:
                    topics.append(f"Specific abnormal findings: {', '.join(abnormal_params[:3])}")
                    if len(abnormal_params) > 3:
                        topics[-1] += f" and {len(abnormal_params) - 3} others"
                
                return topics
            else:
                return ["No parameter data available"]
                
        except Exception:
            return ["Error loading analysis data"]
    
    def get_last_prompt(self) -> str:
        """Get the last prompt sent to the LLM (for debugging)"""
        return getattr(self, '_last_prompt', "No prompt available")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "cache_size": len(self._response_cache),
            "model_warmed_up": self._model_warmed_up,
            "ollama_available": self._is_ollama_available(),
            "estimated_response_time": "3-8 seconds (optimized)"
        }
    
    def clear_cache(self) -> None:
        """Clear response cache to free memory"""
        self._response_cache.clear()
    
    def answer_question_with_progress(self, question: str, progress_callback=None) -> str:
        """
        Answer question with progress updates for better user experience
        """
        if progress_callback:
            progress_callback("🔍 Analyzing question...")
        
        if not self.analysis_data:
            return "No blood report analysis data is currently loaded."
        
        # Preprocess question
        processed_question = self._preprocess_question(question)
        
        # Check cache first
        cache_key = self._get_cache_key(processed_question)
        if cache_key in self._response_cache:
            if progress_callback:
                progress_callback("✅ Found cached response")
            return self._response_cache[cache_key]
        
        if progress_callback:
            progress_callback("🤖 Connecting to AI service...")
        
        if not self._is_ollama_available():
            return "AI service is not available. Please ensure Ollama is running with Mistral model."
        
        if progress_callback:
            progress_callback("📊 Processing report data...")
        
        # Extract and process data
        report_data = self._extract_report_data_optimized()
        if not report_data:
            return "No report data available for analysis."
        
        if progress_callback:
            progress_callback("🧠 Generating AI response...")
        
        # Generate response
        try:
            full_prompt = self._create_optimized_prompt(report_data, processed_question)
            response = self._query_mistral_fast(full_prompt)
            
            # Cache the response (both processed and original question)
            original_cache_key = self._get_cache_key(question)
            self._response_cache[cache_key] = response
            self._response_cache[original_cache_key] = response
            
            if progress_callback:
                progress_callback("✅ Response ready!")
            
            return response
        except Exception as e:
            return f"Error processing question: {str(e)}"


# Convenience function for integration
def create_qa_assistant(analysis_result: Dict[str, Any]) -> BloodReportQAAssistant:
    """Create and load a Q&A assistant with analysis data"""
    assistant = BloodReportQAAssistant()
    assistant.load_analysis_data(analysis_result)
    return assistant