"""
LLM service — backward-compatible facade over the ProviderRegistry.

Preserves the original generate() / chat() / available API so that
ChatService and other existing callers continue to work unchanged.
Internally delegates to whichever provider the registry offers.
"""

import logging
from typing import Optional, List, Dict

from .llm.provider_base import LLMProvider
from .llm.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)


class LLMService:
    """
    Backward-compatible LLM interface.

    Wraps the ProviderRegistry so existing code (ChatService, routes)
    can keep calling llm_service.generate() without knowing about
    multiple providers.
    """

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry
        self._default: Optional[LLMProvider] = registry.get_default()

        if self._default:
            logger.info(
                f"LLMService ready: default provider = {self._default.display_name}"
            )
        else:
            logger.warning("LLMService: no LLM providers available")

    @property
    def available(self) -> bool:
        return self._default is not None and self._default.available

    @property
    def model_name(self) -> str:
        if self._default:
            return self._default.display_name
        return "none"

    @property
    def registry(self) -> ProviderRegistry:
        """Expose registry for agents that need specific providers."""
        return self._registry

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a completion using the default provider.

        Returns a fallback message if no provider is available.
        """
        if not self.available:
            return self._unavailable_fallback(prompt)

        try:
            return await self._default.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning(f"LLM generate failed: {e}")
            return self._error_fallback(str(e))

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Multi-turn chat using the default provider.

        Returns a fallback message if no provider is available.
        """
        if not self.available:
            return self._unavailable_fallback(
                messages[-1].get("content", "") if messages else ""
            )

        try:
            return await self._default.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            logger.warning(f"LLM chat failed: {e}")
            return self._error_fallback(str(e))

    def _unavailable_fallback(self, prompt: str) -> str:
        """Return a meaningful message when no LLM is configured."""
        return (
            "AI insights are not available (no LLM provider configured). "
            "Your blood report has been analyzed using rule-based validation. "
            "Set up a Groq API key (GROQ_API_KEY) or Google Gemini API key "
            "(GEMINI_API_KEY) for AI-powered insights."
        )

    def _error_fallback(self, error: str) -> str:
        """Return a message when the LLM call fails."""
        return (
            "AI service temporarily unavailable. "
            "Your report data is still available for review."
        )

    def get_status(self) -> dict:
        """Provider status for health check endpoint."""
        return {
            "default_provider": self._default.display_name if self._default else None,
            "available": self.available,
            **self._registry.get_status(),
        }
