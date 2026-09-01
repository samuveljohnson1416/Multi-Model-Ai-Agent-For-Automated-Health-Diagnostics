"""
Extraction Agent — LLM-enhanced parameter extraction from OCR text.

Works as a post-processor after OCR + regex parsing:
  1. Receives the raw OCR text AND the regex-parsed parameters
  2. Uses an LLM to find parameters the regex missed
  3. Corrects OCR errors (e.g., "Hemog1obin" → "Hemoglobin")
  4. Returns a refined, more complete parameter list

Preferred model: Gemini Flash (good at structured extraction from messy text).
Fallback: Returns the regex-parsed parameters unchanged.
"""

import json
import logging
from typing import Optional, Dict

from ..services.llm.provider_base import LLMProvider
from .base_agent import BaseAgent
from .agent_models import AgentContext

logger = logging.getLogger(__name__)


class ExtractionAgent(BaseAgent):
    """
    Uses an LLM to enhance/validate regex-parsed blood parameters.

    The LLM receives the raw OCR text and the regex results, then
    fills gaps and corrects errors. This dramatically improves accuracy
    on messy OCR output where Tesseract produces garbled text.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        super().__init__(provider=provider, agent_name="Extraction Agent")

    @property
    def system_prompt(self) -> str:
        return """You are a medical laboratory data extraction specialist.
Your task is to extract blood test parameters from OCR text that may contain errors.

Rules:
- Extract ONLY parameters that are clearly present in the text
- Fix obvious OCR errors (e.g., "1l.2" → "11.2", "Hemog1obin" → "Hemoglobin")
- Return results as a JSON object with parameter names as keys
- Each parameter should have: value (number), unit (string)
- Use standard parameter names: Hemoglobin, RBC, WBC, Platelet, PCV, MCV, MCH, MCHC, etc.
- Do NOT hallucinate or invent values that are not in the text
- If a value is ambiguous or unclear, skip it

Respond with ONLY a JSON object, no markdown, no explanation."""

    async def _execute_llm(self, context: AgentContext) -> str:
        """Use LLM to re-extract parameters from raw OCR text."""
        if not context.raw_text:
            return "No raw text available for extraction enhancement."

        # Build the existing params summary for the LLM to compare against
        existing_params = {}
        for p in context.parameters:
            existing_params[p.name] = {"value": p.value, "unit": p.unit}

        prompt = f"""I have OCR-extracted text from a blood test report. A regex parser found some parameters, but may have missed others or parsed incorrectly.

## Regex-parsed parameters (already found):
{json.dumps(existing_params, indent=2)}

## Raw OCR text:
{context.raw_text[:4000]}

Please extract ALL blood test parameters from the raw text. Include the ones already found (verify their values) and add any that the regex missed. Fix any obvious OCR errors.

Return ONLY a JSON object like:
{{"Hemoglobin": {{"value": 11.2, "unit": "g/dL"}}, "WBC": {{"value": 5400, "unit": "/cumm"}}}}"""

        response = await self._provider.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.0,  # Zero temperature for extraction accuracy
            max_tokens=2048,
        )

        # Try to parse the LLM response as JSON for validation
        try:
            extracted = self._parse_llm_response(response)
            if extracted:
                return json.dumps({
                    "extracted_parameters": extracted,
                    "original_count": len(existing_params),
                    "enhanced_count": len(extracted),
                    "new_parameters": [
                        k for k in extracted if k not in existing_params
                    ],
                })
        except Exception as e:
            logger.warning(f"ExtractionAgent: could not parse LLM response: {e}")

        return response

    def _parse_llm_response(self, response: str) -> Optional[Dict]:
        """Try to extract JSON from the LLM response."""
        # Strip markdown code blocks if present
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (``` markers)
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                # Validate structure: each value should have "value" key
                valid = {}
                for name, info in data.items():
                    if isinstance(info, dict) and "value" in info:
                        try:
                            valid[name] = {
                                "value": float(info["value"]),
                                "unit": str(info.get("unit", "N/A")),
                            }
                        except (ValueError, TypeError):
                            continue
                return valid if valid else None
        except json.JSONDecodeError:
            pass

        return None

    def _execute_fallback(self, context: AgentContext) -> str:
        """Fallback: return existing parameters unchanged."""
        count = len(context.parameters)
        return (
            f"Extraction enhancement unavailable (no LLM). "
            f"Using {count} regex-parsed parameters as-is."
        )
