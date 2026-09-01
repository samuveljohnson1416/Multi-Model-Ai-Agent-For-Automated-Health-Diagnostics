"""
Groq LLM provider — wraps the Groq SDK for fast inference.

Supports multiple models: Llama 3.1, Mixtral, Gemma.
Extracted from the original llm_service.py single-provider implementation.
"""

import logging
from typing import Optional, List, Dict

from groq import Groq, APIError, APIConnectionError, RateLimitError

from .provider_base import LLMProvider

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Groq API provider for LLM inference.

    Free tier: 30 req/min, 14,400 req/day.
    Supports model switching (e.g., Llama for diagnosis, Mixtral for risk).
    """

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.1,
        max_tokens: int = 1024,
        timeout: int = 30,
    ):
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client: Optional[Groq] = None

        if api_key:
            try:
                self._client = Groq(
                    api_key=api_key,
                    timeout=timeout,
                )
                logger.info(f"GroqProvider initialized: model={model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("GroqProvider: no API key provided")

    @property
    def available(self) -> bool:
        return self._client is not None

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model

    def with_model(self, model: str) -> "GroqProvider":
        """
        Create a new GroqProvider instance with a different model.

        Shares the same API key and settings but targets a different model.
        Useful for assigning different Groq models to different agents.
        """
        return GroqProvider(
            api_key=self._api_key,
            model=model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            timeout=self._timeout,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a single-turn completion via Groq."""
        if not self.available:
            raise RuntimeError("GroqProvider is not available (no API key)")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        return await self._call(messages, temperature=temperature, max_tokens=max_tokens)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Multi-turn chat completion via Groq."""
        if not self.available:
            raise RuntimeError("GroqProvider is not available (no API key)")

        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        return await self._call(full_messages, temperature=temperature, max_tokens=max_tokens)

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
            logger.warning(f"Groq rate limit hit (model={self._model})")
            raise
        except APIConnectionError as e:
            logger.error(f"Groq connection error: {e}")
            raise
        except APIError as e:
            logger.error(f"Groq API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected Groq error: {e}")
            raise

    def get_status(self) -> dict:
        """Provider status for health check endpoint."""
        return {
            "provider": self.provider_name,
            "available": self.available,
            "model": self._model if self.available else None,
        }
