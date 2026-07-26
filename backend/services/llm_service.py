"""
Groq LLM service — single provider, no fallback spaghetti.

Replaces the old multi-provider llm_provider.py that juggled
Ollama, HuggingFace, and fallback chains.
"""

import logging
from typing import Optional, List, Dict

from groq import Groq, APIError, APIConnectionError, RateLimitError

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Groq API wrapper for LLM inference.
    Clean single-provider interface with proper error handling.
    """

    def __init__(self):
        settings = get_settings()
        self._client: Optional[Groq] = None
        self._model = settings.groq_model
        self._temperature = settings.groq_temperature
        self._max_tokens = settings.groq_max_tokens
        self._timeout = settings.groq_timeout

        if settings.has_groq:
            try:
                self._client = Groq(
                    api_key=settings.groq_api_key,
                    timeout=self._timeout,
                )
                logger.info(f"Groq LLM initialized: model={self._model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("GROQ_API_KEY not set — LLM features disabled")

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def model_name(self) -> str:
        return self._model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion from a single prompt.

        Args:
            prompt: User message / prompt
            system_prompt: Optional system message for role context
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text, or a fallback message if LLM is unavailable.
        """
        if not self.available:
            return self._unavailable_fallback(prompt)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self._call(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Multi-turn chat completion.

        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."}
            system_prompt: Optional system message prepended to conversation
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Assistant's response text.
        """
        if not self.available:
            return self._unavailable_fallback(messages[-1].get("content", ""))

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        return await self._call(
            full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _call(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Internal: make the Groq API call with error handling."""
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature or self._temperature,
                max_tokens=max_tokens or self._max_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            logger.warning("Groq rate limit hit — returning fallback")
            return (
                "I'm temporarily rate-limited. Please try again in a few seconds. "
                "Your report data is still available for review."
            )
        except APIConnectionError as e:
            logger.error(f"Groq connection error: {e}")
            return "Unable to reach the AI service. Please check your connection."
        except APIError as e:
            logger.error(f"Groq API error: {e}")
            return f"AI service error: {e.message}"
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            return "An unexpected error occurred with the AI service."

    def _unavailable_fallback(self, prompt: str) -> str:
        """Return a meaningful message when LLM is not configured."""
        return (
            "AI insights are not available (GROQ_API_KEY not configured). "
            "Your blood report has been analyzed using rule-based validation. "
            "Set up a Groq API key at https://console.groq.com for AI-powered insights."
        )

    def get_status(self) -> dict:
        """Get provider status for health check."""
        return {
            "name": "groq",
            "available": self.available,
            "model": self._model if self.available else None,
        }
