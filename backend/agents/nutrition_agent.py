"""
Nutrition Agent — personalized diet and lifestyle recommendations.

Generates targeted nutritional advice based on abnormal blood values
and patient demographics. Recommends specific foods to include/avoid,
supplements to consider, and lifestyle changes.

Preferred model: Gemini Flash (long context for detailed plans).
Fallback: Generic recommendations from report_interpreter.py.
"""

import logging
from typing import Optional

from ..services.llm.provider_base import LLMProvider
from .base_agent import BaseAgent
from .agent_models import AgentContext

logger = logging.getLogger(__name__)


class NutritionAgent(BaseAgent):
    """
    Generates personalized nutrition and lifestyle recommendations
    based on blood test results.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        super().__init__(provider=provider, agent_name="Nutrition Agent")

    @property
    def system_prompt(self) -> str:
        return """You are a clinical nutrition specialist AI.

Your role is to provide personalized diet and lifestyle recommendations based on blood test results.

Rules:
- Base recommendations on the specific abnormal values found
- Suggest specific foods that may help normalize abnormal values
- Mention foods/habits to avoid based on the results
- Include relevant vitamins/supplements to discuss with a doctor
- Provide lifestyle recommendations (exercise, sleep, stress management)
- Be specific — name actual foods, not just food groups
- Organize by: Foods to Include, Foods to Avoid, Supplements, Lifestyle
- Keep response under 300 words
- Write short bullet points — do NOT use markdown tables
- Use at most one level of headings (##)
- Always note that dietary changes should be discussed with a healthcare provider"""

    async def _execute_llm(self, context: AgentContext) -> str:
        """Use LLM for personalized nutrition advice."""
        abnormal_lines = []
        for p in context.abnormal_parameters:
            abnormal_lines.append(
                f"- {p.name}: {p.value} {p.unit} ({p.status.value})"
            )

        context_info = ""
        if context.user_context:
            parts = []
            if context.user_context.age:
                parts.append(f"Age: {context.user_context.age}")
            if context.user_context.gender:
                parts.append(f"Gender: {context.user_context.gender}")
            if context.user_context.lifestyle:
                parts.append(f"Lifestyle: {context.user_context.lifestyle}")
            if context.user_context.is_diabetic:
                parts.append("Diabetic: Yes")
            if parts:
                context_info = f"\n**Patient:** {', '.join(parts)}"

        if not abnormal_lines:
            prompt = f"""All blood parameters are within normal ranges.{context_info}

Provide general wellness nutrition and lifestyle recommendations for maintaining good health. Focus on preventive nutrition."""
        else:
            prompt = f"""Based on these abnormal blood test results, provide personalized nutrition and lifestyle recommendations:

## Abnormal Values
{chr(10).join(abnormal_lines)}
{context_info}

Use these four short sections, each a bullet list (no tables, no emoji):
Foods to include, Foods to limit, Supplements to discuss with a doctor,
Lifestyle changes. Name specific foods. End with one line noting that any
changes should be discussed with a healthcare provider."""

        return await self._provider.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.2,  # Slightly higher for creative recommendations
            max_tokens=700,
        )

    def _execute_fallback(self, context: AgentContext) -> str:
        """Rule-based nutrition recommendations."""
        lines = ["## Nutrition & Lifestyle Recommendations\n"]

        if not context.abnormal_parameters:
            lines.append(
                "All parameters are within normal ranges. "
                "Maintain a balanced diet and regular exercise routine.\n"
            )
            lines.append("### General Tips")
            lines.append("- Eat a variety of fruits and vegetables daily")
            lines.append("- Choose whole grains over refined carbohydrates")
            lines.append("- Stay hydrated (8 glasses of water daily)")
            lines.append("- Exercise at least 150 minutes per week")
            lines.append("- Get 7-9 hours of sleep")
            return "\n".join(lines)

        # Map abnormal parameters to basic dietary advice
        advice_map = {
            "Hemoglobin": {
                "LOW": "Iron-rich foods: spinach, lentils, red meat, fortified cereals",
                "HIGH": "Stay hydrated; reduce iron-rich foods if excessive",
            },
            "Cholesterol": {
                "HIGH": "Reduce saturated fats; increase fiber (oats, beans); eat fatty fish",
            },
            "HDL": {
                "LOW": "Increase olive oil, avocados, nuts; exercise regularly",
            },
            "LDL": {
                "HIGH": "Reduce processed foods; eat more soluble fiber; add plant sterols",
            },
            "Triglycerides": {
                "HIGH": "Limit sugar and refined carbs; reduce alcohol; eat omega-3 rich fish",
            },
            "Glucose": {
                "HIGH": "Reduce simple sugars; eat complex carbs; increase protein intake",
            },
            "Creatinine": {
                "HIGH": "Stay well hydrated; moderate protein intake; reduce red meat",
            },
            "Vitamin_D": {
                "LOW": "Sun exposure (15-20 min); fortified milk; fatty fish; supplements",
            },
            "Vitamin_B12": {
                "LOW": "Eggs, dairy, fortified cereals; B12 supplements if vegetarian",
            },
            "Iron": {
                "LOW": "Red meat, spinach, lentils; pair with vitamin C for absorption",
            },
            "Ferritin": {
                "LOW": "Iron-rich foods with vitamin C; avoid tea/coffee with meals",
            },
        }

        lines.append("### Targeted Recommendations\n")
        matched = False

        for p in context.abnormal_parameters:
            if p.name in advice_map and p.status.value in advice_map[p.name]:
                matched = True
                lines.append(f"**{p.name}** ({p.status.value}: {p.value} {p.unit}):")
                lines.append(f"- {advice_map[p.name][p.status.value]}")
                lines.append("")

        if not matched:
            lines.append("Consult a nutritionist for personalized dietary advice based on your results.")

        lines.append(
            "\n*Rule-based recommendations. Configure an LLM provider for "
            "personalized AI-generated nutrition plans.*\n\n"
            "*Always discuss dietary changes with your healthcare provider.*"
        )

        return "\n".join(lines)
