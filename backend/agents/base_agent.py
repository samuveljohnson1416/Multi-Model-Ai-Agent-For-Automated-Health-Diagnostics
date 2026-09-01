"""
Abstract base agent — all specialist agents inherit from this.

Provides:
  - LLM provider injection
  - Standard execute() contract
  - Timing and error handling boilerplate
  - System prompt abstraction
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..services.llm.provider_base import LLMProvider
from .agent_models import AgentContext, AgentResult

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all specialist agents.

    Each agent:
      1. Receives a shared AgentContext
      2. Uses its LLM provider to analyze the data
      3. Returns an AgentResult with status, content, and timing

    If the LLM is unavailable or fails, the agent falls back to
    its rule-based implementation (each subclass defines its own fallback).
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        agent_name: str = "BaseAgent",
    ):
        self._provider = provider
        self._agent_name = agent_name

    @property
    def agent_name(self) -> str:
        return self._agent_name

    @property
    def has_llm(self) -> bool:
        """Whether this agent has a working LLM provider."""
        return self._provider is not None and self._provider.available

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt that defines this agent's role and behavior."""

    @abstractmethod
    async def _execute_llm(self, context: AgentContext) -> str:
        """
        Execute the agent's task using the LLM.

        Subclasses build a prompt from context and call self._provider.generate().
        Returns the LLM's response text.
        """

    @abstractmethod
    def _execute_fallback(self, context: AgentContext) -> str:
        """
        Execute the agent's task using rule-based logic.

        Called when the LLM is unavailable or fails.
        Returns a text response based on deterministic rules.
        """

    async def execute(self, context: AgentContext) -> AgentResult:
        """
        Run this agent: try LLM first, fall back to rules if needed.

        This is the only public method. It handles timing, error catching,
        and status reporting.
        """
        start = time.perf_counter()

        # Try LLM-powered execution
        if self.has_llm:
            try:
                content = await self._execute_llm(context)
                elapsed_ms = int((time.perf_counter() - start) * 1000)

                logger.info(
                    f"{self._agent_name} completed via {self._provider.display_name} "
                    f"in {elapsed_ms}ms"
                )

                return AgentResult(
                    agent_name=self._agent_name,
                    status="success",
                    provider_used=self._provider.display_name,
                    content=content,
                    execution_time_ms=elapsed_ms,
                )

            except Exception as e:
                logger.warning(
                    f"{self._agent_name} LLM failed ({e}), falling back to rules"
                )

        # Fall back to rule-based execution
        try:
            content = self._execute_fallback(context)
            elapsed_ms = int((time.perf_counter() - start) * 1000)

            logger.info(f"{self._agent_name} completed via rule-based in {elapsed_ms}ms")

            return AgentResult(
                agent_name=self._agent_name,
                status="fallback",
                provider_used="rule-based",
                content=content,
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"{self._agent_name} failed entirely: {e}")

            return AgentResult(
                agent_name=self._agent_name,
                status="error",
                provider_used="none",
                content=f"Agent failed: {str(e)}",
                execution_time_ms=elapsed_ms,
                error_message=str(e),
            )
