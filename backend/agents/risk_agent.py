"""
Risk Agent — enhanced risk assessment with organ-system breakdown.

Goes beyond the basic risk score by:
  - Grouping abnormalities by organ system (cardiac, hepatic, renal, etc.)
  - Integrating Framingham risk with blood parameter patterns
  - Identifying metabolic syndrome indicators
  - Providing a structured risk profile

Preferred model: Groq Mixtral (strong reasoning, structured output).
Fallback: Returns rule-based risk scores from risk_calculator.py.
"""

import logging
from typing import Optional

from ..services.llm.provider_base import LLMProvider
from .base_agent import BaseAgent
from .agent_models import AgentContext

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Comprehensive risk assessment agent.

    Analyzes blood parameters through an organ-system lens and provides
    a structured risk profile beyond simple abnormal counting.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        super().__init__(provider=provider, agent_name="Risk Agent")

    @property
    def system_prompt(self) -> str:
        return """You are a clinical risk assessment specialist AI.

Your role is to analyze blood test results and provide a comprehensive risk assessment organized by organ system.

Rules:
- Assess risk for each relevant organ system: Cardiovascular, Hepatic (Liver), Renal (Kidney), Hematologic (Blood), Metabolic, Thyroid, Immune
- For each system, rate risk as: Low / Moderate / High / Critical
- Explain which specific parameters drive each risk rating
- Identify metabolic syndrome indicators if present
- Note any concerning trends or combinations
- Keep response under 400 words
- Use clear markdown formatting
- Always recommend professional medical evaluation"""

    async def _execute_llm(self, context: AgentContext) -> str:
        """Use LLM for enhanced risk assessment."""
        param_lines = []
        for p in context.parameters:
            status_icon = "✅" if p.status.value == "NORMAL" else "⚠️"
            param_lines.append(
                f"- {status_icon} {p.name}: {p.value} {p.unit} [{p.status.value}]"
                + (f" (ref: {p.reference_range})" if p.reference_range else "")
            )

        risk_info = ""
        if context.risk_assessment:
            risk_info = (
                f"\n**Existing Risk Score:** {context.risk_assessment.risk_score:.2f} "
                f"({context.risk_assessment.risk_level})"
            )
            if context.risk_assessment.framingham_risk:
                fr = context.risk_assessment.framingham_risk
                risk_info += f"\n**Framingham 10-year CVD Risk:** {fr.get('risk_percent', 'N/A')}%"

        context_info = ""
        if context.user_context:
            parts = []
            if context.user_context.age:
                parts.append(f"Age: {context.user_context.age}")
            if context.user_context.gender:
                parts.append(f"Gender: {context.user_context.gender}")
            if context.user_context.is_smoker:
                parts.append("Smoker: Yes")
            if context.user_context.is_diabetic:
                parts.append("Diabetic: Yes")
            if parts:
                context_info = f"\n**Patient:** {', '.join(parts)}"

        prompt = f"""Provide a comprehensive risk assessment for these blood test results:

## All Parameters
{chr(10).join(param_lines)}
{risk_info}
{context_info}

Analyze risk by organ system:
1. **Cardiovascular Risk** — cholesterol, triglycerides, HDL/LDL ratios
2. **Hepatic Risk** — ALT, AST, ALP, bilirubin, albumin
3. **Renal Risk** — creatinine, BUN, uric acid
4. **Hematologic Risk** — Hb, RBC, WBC, platelets, indices
5. **Metabolic Risk** — glucose, HbA1c, metabolic syndrome screening
6. **Overall Assessment** — combined risk rating with key actionable points

For each system, provide: risk level, driving parameters, and brief explanation."""

        return await self._provider.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.1,
            max_tokens=1024,
        )

    def _execute_fallback(self, context: AgentContext) -> str:
        """Rule-based organ-system risk grouping."""
        lines = ["## Organ-System Risk Assessment\n"]

        # Group parameters by organ system
        organ_groups = {
            "Cardiovascular": ["Cholesterol", "HDL", "LDL", "Triglycerides", "VLDL"],
            "Hepatic": ["ALT", "AST", "ALP", "GGT", "Bilirubin_Total", "Bilirubin_Direct", "Albumin", "Total_Protein"],
            "Renal": ["Creatinine", "BUN", "Urea", "Uric_Acid"],
            "Hematologic": ["Hemoglobin", "RBC", "WBC", "Platelet", "PCV", "MCV", "MCH", "MCHC", "RDW"],
            "Metabolic": ["Glucose", "HbA1c"],
            "Thyroid": ["TSH", "T3", "T4"],
        }

        param_map = {p.name: p for p in context.parameters}

        for system, param_names in organ_groups.items():
            system_params = [param_map[n] for n in param_names if n in param_map]
            if not system_params:
                continue

            abnormal_in_system = [p for p in system_params if p.status.value != "NORMAL"]

            if not abnormal_in_system:
                risk_level = "Low"
                icon = "🟢"
            elif any(p.status.value == "CRITICAL" for p in abnormal_in_system):
                risk_level = "Critical"
                icon = "🔴"
            elif len(abnormal_in_system) >= 2:
                risk_level = "High"
                icon = "🟠"
            else:
                risk_level = "Moderate"
                icon = "🟡"

            lines.append(f"### {icon} {system} — {risk_level}")
            for p in system_params:
                status_mark = "✅" if p.status.value == "NORMAL" else "⚠️"
                lines.append(f"- {status_mark} {p.name}: {p.value} {p.unit} [{p.status.value}]")
            lines.append("")

        # Overall
        if context.risk_assessment:
            lines.append(f"### Overall Risk Score: {context.risk_assessment.risk_score:.2f} ({context.risk_assessment.risk_level})")

        lines.append(
            "\n*Rule-based assessment. Configure an LLM provider for AI-enhanced risk analysis.*\n\n"
            "*Consult your healthcare provider for professional risk evaluation.*"
        )

        return "\n".join(lines)
