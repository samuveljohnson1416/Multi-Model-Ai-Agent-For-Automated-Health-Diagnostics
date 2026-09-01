"""
Google Gemini LLM provider — wraps the google-genai SDK.

Uses Gemini 2.0 Flash (free tier: 15 req/min, 1,500 req/day).
Best for: long-context tasks (extraction, nutrition plans).
"""

import logging
from typing import Optional, List, Dict

from .provider_base import LLMProvider

logger = logging.getLogger(__name__)

# Lazy import — only loaded when a Gemini key is available
_genai = None


def _lazy_import_genai():
    """Lazy-import google.genai to avoid startup cost when not configured."""
    global _genai
    if _genai is None:
        try:
            from google import genai
            _genai = genai
        except ImportError:
            logger.error(
                "google-genai package not installed. "
                "Install with: pip install google-genai"
            )
    return _genai


class GeminiProvider(LLMProvider):
    """
    Google Gemini API provider.

    Free tier: 15 req/min, 1,500 req/day (no billing required).
    Uses the google-genai SDK (lightweight, official Google AI client).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._client = None

        if api_key:
            genai = _lazy_import_genai()
            if genai:
                try:
                    self._client = genai.Client(api_key=api_key)
                    logger.info(f"GeminiProvider initialized: model={model}")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GeminiProvider: no API key provided")

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def provider_name(self) -> str:
        return "gemini"

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
        """Generate a single-turn completion via Gemini."""
        if not self.available:
            raise RuntimeError("GeminiProvider is not available (no API key)")

        genai = _lazy_import_genai()

        config = genai.types.GenerateContentConfig(
            temperature=temperature or self._temperature,
            max_output_tokens=max_tokens or self._max_tokens,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Multi-turn chat completion via Gemini.

        Converts the OpenAI-style messages format to Gemini's contents format.
        """
        if not self.available:
            raise RuntimeError("GeminiProvider is not available (no API key)")

        genai = _lazy_import_genai()

        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = msg["role"]
            # Gemini uses "user" and "model" (not "assistant")
            if role == "assistant":
                role = "model"
            elif role == "system":
                # System messages are handled via config, skip here
                continue
            contents.append(
                genai.types.Content(
                    role=role,
                    parts=[genai.types.Part(text=msg["content"])],
                )
            )

        # Extract system prompt from messages if not explicitly provided
        msg_system = next(
            (m["content"] for m in messages if m["role"] == "system"),
            None,
        )
        effective_system = system_prompt or msg_system

        config = genai.types.GenerateContentConfig(
            temperature=temperature or self._temperature,
            max_output_tokens=max_tokens or self._max_tokens,
        )
        if effective_system:
            config.system_instruction = effective_system

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    def get_status(self) -> dict:
        """Provider status for health check endpoint."""
        return {
            "provider": self.provider_name,
            "available": self.available,
            "model": self._model if self.available else None,
        }
