"""
Conversational Agent — context-aware Q&A powered by all agent reports.

Promoted from the simple ChatService to a full agent with access to
all specialist agents' outputs. This means when a user asks "what should
I eat?", the agent can reference the Nutrition Agent's detailed plan
instead of generating a generic response.

Preferred model: Groq Llama 3.1 (fast for interactive chat).
Fallback: Simple rule-based Q&A from the original ChatService.
"""

import logging
from typing import Optional, List, Dict

from ..services.llm.provider_base import LLMProvider
from ..models.blood_parameter import BloodParameter
from .agent_models import AgentResult

logger = logging.getLogger(__name__)


CONVERSATIONAL_SYSTEM_PROMPT = """You are a knowledgeable medical assistant AI helping users understand their blood test results.

You have access to the patient's blood report data AND detailed analysis from multiple specialist AI agents:
- Diagnosis Agent: clinical interpretation and pattern analysis
- Risk Agent: organ-system risk assessment
- Nutrition Agent: diet and lifestyle recommendations

Rules:
- Answer questions clearly and concisely
- Reference specific agent findings when relevant (e.g., "The Diagnosis Agent identified...")
- Explain medical terms in simple language
- When discussing abnormal values, explain what they might indicate
- Always remind the user to consult their healthcare provider
- If asked about something not in the report or agent analyses, say so clearly
- Be empathetic and supportive
- Never diagnose conditions — only suggest possibilities
- Keep responses focused and under 200 words unless the user asks for detail"""


class ConversationalAgent:
    """
    Context-aware chat agent with access to all specialist agent outputs.

    Unlike the other agents, this one doesn't extend BaseAgent because
    it has a fundamentally different interface (multi-turn chat vs single-shot).
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider
        self._agent_name = "Conversational Agent"

    @property
    def has_llm(self) -> bool:
        return self._provider is not None and self._provider.available

    async def ask(
        self,
        question: str,
        parameters: List[BloodParameter],
        agent_reports: Optional[List[AgentResult]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> str:
        """
        Answer a question about a blood report with full agent context.

        Args:
            question: User's question.
            parameters: Blood parameters from the analysis.
            agent_reports: Output from all specialist agents (diagnosis, risk, nutrition).
            chat_history: Previous messages in this conversation.
            recommendations: Rule-based recommendations from the analysis.

        Returns:
            AI-generated answer string.
        """
        if not self.has_llm:
            return self._rule_based_fallback(question, parameters)

        # Build comprehensive context from all agents
        context = self._build_full_context(parameters, agent_reports, recommendations)

        # Build message history
        messages = []

        # Inject full context as initial exchange
        messages.append({
            "role": "user",
            "content": (
                f"Here is the patient's complete blood report analysis:\n\n"
                f"{context}\n\n"
                f"I will now ask questions about this report and the analysis."
            ),
        })
        messages.append({
            "role": "assistant",
            "content": (
                "I've reviewed the complete blood report and all specialist agent analyses. "
                "I'm ready to answer your questions. What would you like to know?"
            ),
        })

        # Add chat history (keep last 10 messages)
        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current question
        messages.append({"role": "user", "content": question})

        try:
            return await self._provider.chat(
                messages=messages,
                system_prompt=CONVERSATIONAL_SYSTEM_PROMPT,
                temperature=0.2,
                max_tokens=512,
            )
        except Exception as e:
            logger.warning(f"ConversationalAgent LLM failed: {e}")
            return self._rule_based_fallback(question, parameters)

    def _build_full_context(
        self,
        parameters: List[BloodParameter],
        agent_reports: Optional[List[AgentResult]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> str:
        """Build comprehensive context including all agent outputs."""
        lines = ["## Blood Report Parameters\n"]

        # Parameter summary
        normal = []
        abnormal = []
        for p in parameters:
            line = f"- {p.name}: {p.value} {p.unit} [{p.status.value}]"
            if p.reference_range:
                line += f" (ref: {p.reference_range})"
            if p.status.value in ("LOW", "HIGH", "CRITICAL"):
                abnormal.append(line)
            else:
                normal.append(line)

        if abnormal:
            lines.append("### Abnormal Values")
            lines.extend(abnormal)
            lines.append("")

        if normal:
            lines.append("### Normal Values")
            lines.extend(normal)
            lines.append("")

        # Include agent analyses
        if agent_reports:
            lines.append("---\n## Specialist Agent Analyses\n")
            for report in agent_reports:
                if report.status != "error":
                    lines.append(f"### {report.agent_name} ({report.provider_used})")
                    lines.append(report.content)
                    lines.append("")

        # Include recommendations
        if recommendations:
            lines.append("### Recommendations")
            for r in recommendations:
                lines.append(f"- {r}")

        return "\n".join(lines)

    def _rule_based_fallback(
        self,
        question: str,
        parameters: List[BloodParameter],
    ) -> str:
        """Simple fallback when LLM is unavailable."""
        q = question.lower()
        abnormal = [p for p in parameters if p.status.value in ("LOW", "HIGH", "CRITICAL")]

        if "abnormal" in q or "wrong" in q or "problem" in q:
            if abnormal:
                items = [f"{p.name} ({p.status.value}: {p.value} {p.unit})" for p in abnormal[:5]]
                return (
                    "The following parameters are outside normal range:\n"
                    + "\n".join(f"• {i}" for i in items)
                    + "\n\nPlease consult your healthcare provider for interpretation."
                )
            return "All tested parameters are within normal ranges."

        if "summary" in q or "overall" in q:
            total = len(parameters)
            abn = len(abnormal)
            return (
                f"Your report has {total} parameters tested. "
                f"{total - abn} are normal and {abn} are outside the reference range. "
                f"Please consult your healthcare provider for a detailed review."
            )

        if "diet" in q or "eat" in q or "food" in q or "nutrition" in q:
            return (
                "For personalized dietary recommendations based on your blood report, "
                "please configure an LLM provider (Groq or Gemini API key). "
                "In the meantime, consult a nutritionist for tailored advice."
            )

        return (
            f"Your report contains {len(parameters)} parameters with "
            f"{len(abnormal)} abnormal values. For AI-powered insights, "
            f"please configure a Groq or Gemini API key. For medical interpretation, "
            f"please consult your healthcare provider."
        )

    def get_status(self) -> dict:
        """Agent status for health check."""
        return {
            "agent": self._agent_name,
            "available": self.has_llm,
            "provider": self._provider.display_name if self.has_llm else None,
        }
