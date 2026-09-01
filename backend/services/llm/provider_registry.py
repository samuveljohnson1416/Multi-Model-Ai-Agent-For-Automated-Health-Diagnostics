"""
Provider registry — auto-discovers available LLM providers and manages fallback.

Central hub that agents use to get their preferred provider.
If the preferred provider is unavailable, falls back to any available one.
"""

import logging
from typing import Optional, Dict, List

from .provider_base import LLMProvider
from .groq_provider import GroqProvider
from .gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Discovers which providers have valid API keys and exposes them by name.

    Usage:
        registry = ProviderRegistry(settings)
        provider = registry.get_provider("groq")          # specific
        provider = registry.get_provider("groq", "gemini") # with fallback
        provider = registry.get_default()                   # any available
    """

    def __init__(
        self,
        groq_provider: Optional[GroqProvider] = None,
        gemini_provider: Optional[GeminiProvider] = None,
    ):
        self._providers: Dict[str, LLMProvider] = {}

        if groq_provider and groq_provider.available:
            self._providers["groq"] = groq_provider
        if gemini_provider and gemini_provider.available:
            self._providers["gemini"] = gemini_provider

        available = list(self._providers.keys())
        logger.info(f"ProviderRegistry initialized: {len(available)} providers available: {available}")

        if not available:
            logger.warning(
                "No LLM providers available! "
                "Set GROQ_API_KEY or GEMINI_API_KEY for AI-powered features."
            )

    @property
    def has_providers(self) -> bool:
        """Whether any LLM provider is available."""
        return len(self._providers) > 0

    def list_available(self) -> List[str]:
        """List names of all available providers."""
        return list(self._providers.keys())

    def get_provider(self, *preferred: str) -> Optional[LLMProvider]:
        """
        Get a provider by preference order.

        Args:
            *preferred: Provider names in order of preference.
                        Falls back to any available provider if none match.

        Returns:
            An LLMProvider instance, or None if nothing is available.

        Example:
            registry.get_provider("gemini", "groq")  # prefer Gemini, fall back to Groq
        """
        # Try preferred providers in order
        for name in preferred:
            if name in self._providers:
                return self._providers[name]

        # Fall back to any available provider
        if self._providers:
            fallback_name = next(iter(self._providers))
            logger.debug(
                f"Preferred providers {list(preferred)} not available, "
                f"falling back to '{fallback_name}'"
            )
            return self._providers[fallback_name]

        return None

    def get_default(self) -> Optional[LLMProvider]:
        """Get the default (first available) provider."""
        if self._providers:
            return next(iter(self._providers.values()))
        return None

    def get_groq(self) -> Optional[GroqProvider]:
        """Get the Groq provider specifically (for model switching via with_model)."""
        provider = self._providers.get("groq")
        if isinstance(provider, GroqProvider):
            return provider
        return None

    def get_status(self) -> dict:
        """Full provider status for health check."""
        return {
            "total_available": len(self._providers),
            "providers": {
                name: provider.get_status()
                for name, provider in self._providers.items()
            },
        }
