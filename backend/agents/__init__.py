"""
Agent subpackage — multi-agent framework for health diagnostics.

Six specialized agents orchestrated by the CoordinatorAgent:
  - ExtractionAgent: LLM-enhanced parameter extraction from OCR text
  - DiagnosisAgent: Clinical interpretation of abnormal values
  - RiskAgent: Enhanced risk assessment with organ-system breakdown
  - NutritionAgent: Personalized diet/lifestyle recommendations
  - ConversationalAgent: Context-aware Q&A with access to all agent reports
  - CoordinatorAgent: Master orchestrator that delegates and merges
"""

from .base_agent import BaseAgent
from .agent_models import AgentContext, AgentResult, CoordinatorResult
from .extraction_agent import ExtractionAgent
from .diagnosis_agent import DiagnosisAgent
from .risk_agent import RiskAgent
from .nutrition_agent import NutritionAgent
from .conversational_agent import ConversationalAgent
from .coordinator_agent import CoordinatorAgent

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentResult",
    "CoordinatorResult",
    "ExtractionAgent",
    "DiagnosisAgent",
    "RiskAgent",
    "NutritionAgent",
    "ConversationalAgent",
    "CoordinatorAgent",
]
