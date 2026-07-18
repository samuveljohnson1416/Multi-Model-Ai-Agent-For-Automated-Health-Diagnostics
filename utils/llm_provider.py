"""
Unified LLM Provider - EXPLANATIONS ONLY
=========================================

CRITICAL: This provider is used ONLY for generating explanation text.
NO medical decisions, parameter classifications, or risk scoring is performed by LLMs.

All deterministic medical reasoning happens in:
- src/core/medical_logic.py (parameter classification, pattern detection, risk scoring)
- src/phase2/phase2_orchestrator.py (orchestration and decision logic)
- src/core/interpreter.py (result interpretation and synthesis)

LLM Role: Generate human-readable explanations for already-made rule-based decisions.

Supports:
- Local Ollama server
- Hugging Face Inference API
- Automatic fallback between providers
"""

import os
import requests
import logging
from typing import Optional, Dict, Any
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProviderType(Enum):
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    NONE = "none"


class LLMProvider:
    """
    Unified LLM Provider for EXPLANATIONS ONLY
    
    ⚠️ CRITICAL CONSTRAINT:
    This provider generates explanatory text ONLY.
    It does NOT perform:
    - Parameter classification (use medical_logic.py)
    - Risk scoring (use medical_logic.py)
    - Medical decision-making (use phase2_orchestrator.py)
    
    Supported providers:
    - Local Ollama server
    - Hugging Face Inference API
    - Automatic fallback between providers
    """
    
    def __init__(self):
        # Load configuration from environment
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral:instruct")
        
        self.hf_token = os.getenv("HF_API_TOKEN", "")
        self.hf_model_id = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{self.hf_model_id}"
        
        self.priority = os.getenv("LLM_PROVIDER_PRIORITY", "ollama_first")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        self.debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # Track active provider
        self._active_provider: LLMProviderType = LLMProviderType.NONE
        self._ollama_available: Optional[bool] = None
        self._hf_available: Optional[bool] = None
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama server is running and accessible"""
        if self._ollama_available is not None:
            return self._ollama_available
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            self._ollama_available = response.status_code == 200
            if self._ollama_available:
                logger.info("✅ Ollama server is available")
            return self._ollama_available
        except Exception as e:
            if self.debug:
                logger.debug(f"Ollama check failed: {e}")
            self._ollama_available = False
            return False
    
    def _check_hf_available(self) -> bool:
        """Check if Hugging Face API is configured and accessible"""
        if self._hf_available is not None:
            return self._hf_available
        
        if not self.hf_token:
            logger.warning("⚠️ HF_API_TOKEN not set - Hugging Face API unavailable")
            self._hf_available = False
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            response = requests.get(
                f"https://huggingface.co/api/models/{self.hf_model_id}",
                headers=headers,
                timeout=10
            )
            self._hf_available = response.status_code == 200
            if self._hf_available:
                logger.info("✅ Hugging Face API is available")
            return self._hf_available
        except Exception as e:
            if self.debug:
                logger.debug(f"HF API check failed: {e}")
            self._hf_available = False
            return False
    
    def get_active_provider(self) -> LLMProviderType:
        """Determine which provider to use based on priority and availability"""
        if self.priority == "ollama_only":
            return LLMProviderType.OLLAMA if self._check_ollama_available() else LLMProviderType.NONE
        
        elif self.priority == "hf_only":
            return LLMProviderType.HUGGINGFACE if self._check_hf_available() else LLMProviderType.NONE
        
        elif self.priority == "hf_first":
            if self._check_hf_available():
                return LLMProviderType.HUGGINGFACE
            elif self._check_ollama_available():
                return LLMProviderType.OLLAMA
            return LLMProviderType.NONE
        
        else:  # ollama_first (default)
            if self._check_ollama_available():
                return LLMProviderType.OLLAMA
            elif self._check_hf_available():
                return LLMProviderType.HUGGINGFACE
            return LLMProviderType.NONE
    
    def _call_ollama(self, prompt: str, system_prompt: str = "", 
                     temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Call local Ollama API"""
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                raise Exception(f"Ollama API returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            raise
    
    def _call_huggingface(self, prompt: str, system_prompt: str = "",
                          temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """Call Hugging Face Inference API"""
        try:
            # Format prompt for instruction-tuned models
            if system_prompt:
                full_prompt = f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
            else:
                full_prompt = f"<s>[INST] {prompt} [/INST]"
            
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "top_p": 0.9,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                self.hf_api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return str(result)
            elif response.status_code == 503:
                # Model is loading
                logger.warning("HF model is loading, retrying...")
                raise Exception("Model is loading, please retry")
            else:
                raise Exception(f"HF API returned status {response.status_code}: {response.text}")
                
        except Exception as e:
            logger.error(f"Hugging Face call failed: {e}")
            raise
    
    def generate(self, prompt: str, system_prompt: str = "",
                 temperature: float = 0.1, max_tokens: int = 1000) -> str:
        """
        Generate EXPLANATION TEXT using the best available LLM provider.
        
        ⚠️ CRITICAL: This method is for TEXT GENERATION ONLY.
        It does NOT make medical decisions.
        
        All medical logic is rule-based and deterministic:
        - Parameter classification: medical_logic.py
        - Risk scoring: medical_logic.py
        - Pattern detection: medical_logic.py
        - Decision synthesis: phase2_orchestrator.py
        
        This method only wraps already-made decisions in human-readable text.
        
        Args:
            prompt: Text to generate explanation for (must contain pre-made decision)
            system_prompt: System context for the LLM
            temperature: Low (0.1) for consistency, high (0.7+) for creativity
            max_tokens: Maximum length of generated text
            
        Returns:
            Generated explanation text (NOT a medical decision)
        """
        provider = self.get_active_provider()
        
        if provider == LLMProviderType.NONE:
            return "Error: No LLM provider available. Please configure Ollama or Hugging Face API."
        
        # Try primary provider
        try:
            if provider == LLMProviderType.OLLAMA:
                self._active_provider = LLMProviderType.OLLAMA
                return self._call_ollama(prompt, system_prompt, temperature, max_tokens)
            else:
                self._active_provider = LLMProviderType.HUGGINGFACE
                return self._call_huggingface(prompt, system_prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"Primary provider ({provider.value}) failed: {e}")
        
        # Try fallback provider
        fallback = None
        if provider == LLMProviderType.OLLAMA and self._check_hf_available():
            fallback = LLMProviderType.HUGGINGFACE
        elif provider == LLMProviderType.HUGGINGFACE and self._check_ollama_available():
            fallback = LLMProviderType.OLLAMA
        
        if fallback:
            try:
                logger.info(f"Falling back to {fallback.value}")
                if fallback == LLMProviderType.OLLAMA:
                    self._active_provider = LLMProviderType.OLLAMA
                    return self._call_ollama(prompt, system_prompt, temperature, max_tokens)
                else:
                    self._active_provider = LLMProviderType.HUGGINGFACE
                    return self._call_huggingface(prompt, system_prompt, temperature, max_tokens)
            except Exception as e:
                logger.error(f"Fallback provider ({fallback.value}) also failed: {e}")
        
        return f"Error: All LLM providers failed. Last error: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current provider status"""
        return {
            "ollama_available": self._check_ollama_available(),
            "ollama_url": self.ollama_url,
            "ollama_model": self.ollama_model,
            "hf_available": self._check_hf_available(),
            "hf_model": self.hf_model_id,
            "hf_token_set": bool(self.hf_token),
            "priority": self.priority,
            "active_provider": self._active_provider.value if self._active_provider else "none",
            "recommended_provider": self.get_active_provider().value
        }
    
    def reset_cache(self):
        """Reset availability cache to force re-check"""
        self._ollama_available = None
        self._hf_available = None
        self._active_provider = LLMProviderType.NONE


# Global instance
_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get or create global LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = LLMProvider()
    return _llm_provider


def generate_text(prompt: str, system_prompt: str = "",
                  temperature: float = 0.1, max_tokens: int = 1000) -> str:
    """Convenience function for text generation"""
    provider = get_llm_provider()
    return provider.generate(prompt, system_prompt, temperature, max_tokens)


def get_llm_status() -> Dict[str, Any]:
    """Get LLM provider status"""
    provider = get_llm_provider()
    return provider.get_status()
