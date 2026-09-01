"""
Diagnosis Agent — clinical interpretation of blood test results.

Analyzes abnormal parameters to identify patterns and possible conditions.
Example: low Hb + low MCV + low MCH → microcytic anemia pattern.

Preferred model: Groq Llama 3.1 (fast, good medical reasoning).
Fallback: Rule-based interpretation from report_interpreter.py.
"""

import logging
from typing import Optional

from ..services.llm.provider_base import LLMProvider
from .base_agent import BaseAgent
from .agent_models import AgentContext

logger = logging.getLogger(__name__)


class DiagnosisAgent(BaseAgent):
    """
    Analyzes blood parameters and provides clinical interpretation.

    Identifies patterns across multiple abnormal values, suggests
    possible conditions, and recommends follow-up tests.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        super().__init__(provider=provider, agent_name="Diagnosis Agent")

    @property
    def system_prompt(self) -> str:
        return """You are an expert clinical laboratory specialist AI analyzing blood test results.

Your role:
- Identify clinically significant patterns across abnormal values
- Suggest possible conditions (e.g., "microcytic anemia pattern", "metabolic syndrome indicators")
- Recommend specific follow-up tests
- Note any critical values requiring immediate attention

Rules:
- You are NOT a doctor — frame everything as "may indicate" or "could suggest"
- Always recommend consulting a healthcare provider
- Prioritize the most clinically significant findings
- Group related abnormalities together
- Use simple language the patient can understand
- Write short paragraphs and bullet points — do NOT use markdown tables
- Use at most one level of headings (##)
- Keep response under 300 words"""

    async def _execute_llm(self, context: AgentContext) -> str:
        """Use LLM to generate clinical interpretation."""
        abnormal_lines = []
        for p in context.abnormal_parameters:
            line = (
                f"- **{p.name}**: {p.value} {p.unit} "
                f"({p.status.value}, ref: {p.reference_range or 'N/A'}"
            )
            if p.severity and p.severity != "Normal":
                line += f", severity: {p.severity}"
            line += ")"
            abnormal_lines.append(line)

        normal_summary = []
        for p in context.parameters:
            if p not in context.abnormal_parameters:
                normal_summary.append(f"{p.name}: {p.value} {p.unit}")

        context_info = ""
        if context.user_context:
            parts = []
            if context.user_context.age:
                parts.append(f"Age: {context.user_context.age}")
            if context.user_context.gender:
                parts.append(f"Gender: {context.user_context.gender}")
            if context.user_context.medical_history:
                parts.append(f"Medical history: {', '.join(context.user_context.medical_history)}")
            if context.user_context.is_smoker:
                parts.append("Smoker: Yes")
            if context.user_context.is_diabetic:
                parts.append("Diabetic: Yes")
            if parts:
                context_info = f"\n**Patient Context:** {', '.join(parts)}"

        prompt = f"""Analyze these blood test results and provide clinical interpretation:

## Summary
- Total parameters tested: {len(context.parameters)}
- Abnormal parameters: {len(context.abnormal_parameters)}
- Risk level: {context.risk_assessment.risk_level if context.risk_assessment else 'unknown'}
{context_info}

## Abnormal Values
{chr(10).join(abnormal_lines) if abnormal_lines else 'No abnormal values found.'}

## Normal Values (for context)
{', '.join(normal_summary[:10]) if normal_summary else 'N/A'}

Write the interpretation as flowing prose with short bullet lists — no tables. Cover, in this order:
- The two or three most important things these results show (a sentence or two).
- Any patterns across several values (e.g. an anemia picture, signs of infection, a metabolic cluster) and what each pattern may point to.
- What a clinician might check next.
Lead with the single most important finding."""

        return await self._provider.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.1,
            max_tokens=700,
        )

    def _execute_fallback(self, context: AgentContext) -> str:
        """Rule-based clinical interpretation."""
        if not context.abnormal_parameters:
            return (
                "## Key Findings\n\n"
                "All tested parameters are within normal reference ranges. "
                "Continue maintaining a healthy lifestyle and regular check-ups.\n\n"
                "*Please consult your healthcare provider for personalized medical advice.*"
            )

        lines = ["## Key Findings\n"]
        lines.append(
            f"Found **{len(context.abnormal_parameters)} abnormal** parameter(s) "
            f"out of {len(context.parameters)} tested.\n"
        )

        # Group by status
        high = [p for p in context.abnormal_parameters if p.status.value == "HIGH"]
        low = [p for p in context.abnormal_parameters if p.status.value == "LOW"]
        critical = [p for p in context.abnormal_parameters if p.status.value == "CRITICAL"]

        if critical:
            lines.append("### ⚠️ Critical Values")
            for p in critical:
                lines.append(f"- **{p.name}**: {p.value} {p.unit} (ref: {p.reference_range or 'N/A'})")
            lines.append("")

        if high:
            lines.append("### Elevated Values")
            for p in high:
                lines.append(f"- **{p.name}**: {p.value} {p.unit} (ref: {p.reference_range or 'N/A'})")
            lines.append("")

        if low:
            lines.append("### Low Values")
            for p in low:
                lines.append(f"- **{p.name}**: {p.value} {p.unit} (ref: {p.reference_range or 'N/A'})")
            lines.append("")

        lines.append(
            "\n*This is a rule-based analysis. AI-powered interpretation is "
            "available when an LLM provider is configured.*\n\n"
            "*Please consult your healthcare provider for diagnosis and treatment.*"
        )

        return "\n".join(lines)
