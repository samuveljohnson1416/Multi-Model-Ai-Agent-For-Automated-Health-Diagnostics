"""
Chat service — Groq-powered Q&A about blood reports.

Replaces the 691-line enhanced_ai_agent.py that hardcoded diet/exercise
recommendations as string templates. This version sends the report context
to Groq and lets the LLM generate personalized answers.
"""

import logging
from typing import List, Dict, Optional

from .llm_service import LLMService
from ..models.blood_parameter import BloodParameter

logger = logging.getLogger(__name__)


CHAT_SYSTEM_PROMPT = """You are a knowledgeable medical assistant AI helping users understand
their blood test results. You have access to the patient's blood report data.

Rules:
- Answer questions clearly and concisely
- Explain medical terms in simple language
- When discussing abnormal values, explain what they might indicate
- Always remind the user to consult their healthcare provider
- If asked about something not in the report, say so clearly
- Be empathetic and supportive
- Never diagnose conditions — only suggest possibilities
- Keep responses focused and under 200 words unless the user asks for detail"""


class ChatService:
    """
    Chat Q&A service powered by Groq LLM.
    Takes report context + user question → returns natural language answer.
    """

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def ask(
        self,
        question: str,
        parameters: List[BloodParameter],
        chat_history: Optional[List[Dict[str, str]]] = None,
        recommendations: Optional[List[str]] = None,
    ) -> str:
        """
        Answer a question about a blood report.

        Args:
            question: User's question
            parameters: List of BloodParameter from the analysis
            chat_history: Previous messages in the conversation
            recommendations: Recommendations from the analysis

        Returns:
            AI-generated answer string.
        """
        if not self.llm.available:
            return self._rule_based_fallback(question, parameters)

        # Build report context for the LLM
        context = self._build_report_context(parameters, recommendations)

        # Build message history
        messages = []

        # Add report context as first user message
        messages.append({
            "role": "user",
            "content": f"Here is the patient's blood report data:\n\n{context}\n\nI will now ask questions about this report.",
        })
        messages.append({
            "role": "assistant",
            "content": "I've reviewed the blood report data. I'm ready to answer your questions about the results. What would you like to know?",
        })

        # Add chat history
        if chat_history:
            for msg in chat_history[-10:]:  # Keep last 10 messages for context
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # Add current question
        messages.append({"role": "user", "content": question})

        return await self.llm.chat(
            messages=messages,
            system_prompt=CHAT_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=512,
        )

    def _build_report_context(
        self,
        parameters: List[BloodParameter],
        recommendations: Optional[List[str]] = None,
    ) -> str:
        """Build a concise text summary of the report for the LLM."""
        lines = ["## Blood Report Parameters\n"]

        normal = []
        abnormal = []

        for p in parameters:
            line = f"- {p.name}: {p.value} {p.unit} [{p.status.value}]"
            if p.reference_range:
                line += f" (ref: {p.reference_range})"
            if p.severity and p.severity != "Normal":
                line += f" — {p.severity}"

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
                return f"The following parameters are outside normal range:\n" + "\n".join(f"• {i}" for i in items) + "\n\nPlease consult your healthcare provider for interpretation."
            return "All tested parameters are within normal ranges."

        if "summary" in q or "overall" in q:
            total = len(parameters)
            abn = len(abnormal)
            return f"Your report has {total} parameters tested. {total - abn} are normal and {abn} are outside the reference range. Please consult your healthcare provider for a detailed review."

        return (
            f"Your report contains {len(parameters)} parameters with "
            f"{len(abnormal)} abnormal values. For AI-powered insights, "
            f"please configure a Groq API key. For medical interpretation, "
            f"please consult your healthcare provider."
        )
