"""
Abstract base class for LLM providers.

All providers (Groq, Gemini, etc.) implement this interface.
The ProviderRegistry and agents depend only on this abstraction.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict


class LLMProvider(ABC):
    """
    Contract that every LLM provider must satisfy.

    Design rationale:
      - `generate()` for single-turn completions (agents use this)
      - `chat()` for multi-turn conversations (conversational agent uses this)
      - Properties for introspection (logging, health checks, UI display)
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a single-turn completion.

        Args:
            prompt: User message / task prompt.
            system_prompt: Optional system-level instruction.
            temperature: Sampling temperature override.
            max_tokens: Max output tokens override.

        Returns:
            Generated text response.

        Raises:
            Exception: On unrecoverable API errors.
        """

    @abstractmethod
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
            messages: List of {"role": "user"|"assistant", "content": "..."}.
            system_prompt: Optional system message prepended to conversation.
            temperature: Sampling temperature override.
            max_tokens: Max output tokens override.

        Returns:
            Assistant's response text.
        """

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured and ready to use."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'groq', 'gemini')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Currently configured model ID."""

    @property
    def display_name(self) -> str:
        """Human-readable identifier for logs and UI (e.g., 'groq/llama-3.1-8b')."""
        return f"{self.provider_name}/{self.model_name}"
