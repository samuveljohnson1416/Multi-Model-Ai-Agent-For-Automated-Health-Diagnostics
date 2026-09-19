"""
Groq LLM provider — wraps the Groq SDK for fast inference.

Supports multiple models: Llama 3.1, Mixtral, Gemma.
Extracted from the original llm_service.py single-provider implementation.
"""

import asyncio
import json
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
        model: str = "openai/gpt-oss-20b",  # matches config.py; older llama-3.x defaults were retired (404)
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
                    # The SDK default (2) sleeps through each rate-limit window; failing fast lets
                    # the agent fall back to rules instead of stalling the request.
                    max_retries=1,
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
    def supports_tools(self) -> bool:
        return True

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
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
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

    async def chat_with_tools(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """One turn of a tool-calling conversation (OpenAI-style tools)."""
        if not self.available:
            raise RuntimeError("GroqProvider is not available (no API key)")

        full = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + messages
        kwargs = {"tools": tools, "tool_choice": "auto"} if tools else {}
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self._model,
                messages=full,
                temperature=self._temperature if temperature is None else temperature,
                max_tokens=max_tokens or self._max_tokens,
                **kwargs,
            )
        except (RateLimitError, APIConnectionError, APIError) as e:
            logger.error(f"Groq tool-call error (model={self._model}): {e}")
            raise

        msg = response.choices[0].message
        calls = []
        for tc in msg.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            calls.append({"id": tc.id, "name": tc.function.name, "arguments": args})
        return {"content": (msg.content or "").strip() or None, "tool_calls": calls}

    def get_status(self) -> dict:
        """Provider status for health check endpoint."""
        return {
            "provider": self.provider_name,
            "available": self.available,
            "model": self._model if self.available else None,
        }
