"""
Abstract base class for LLM providers.

All providers (Groq, etc.) implement this interface.
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
    def supports_tools(self) -> bool:
        """Whether chat_with_tools() is implemented (needed by autonomous agents)."""
        return False

    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """
        One turn of a tool-calling conversation.

        `messages`/`tools` use the OpenAI chat format. Returns
        {"content": str | None, "tool_calls": [{"id", "name", "arguments": dict}]}.
        """
        raise NotImplementedError(f"{self.provider_name} does not support tool calling")

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured and ready to use."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'groq')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Currently configured model ID."""

    @property
    def display_name(self) -> str:
        """Human-readable identifier for logs and UI (e.g., 'groq/llama-3.1-8b')."""
        return f"{self.provider_name}/{self.model_name}"
