"""
Pydantic models for inter-agent communication.

AgentContext: shared input that all agents receive.
AgentResult: standardized output that every agent produces.
CoordinatorResult: merged output from all agents.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, Field

from ..models.blood_parameter import BloodParameter
from ..models.report import UserContext, RiskAssessment


class AgentContext(BaseModel):
    """
    Input context shared across all specialist agents.

    Built by the CoordinatorAgent from the extraction/parsing pipeline output.
    Each agent reads what it needs and ignores the rest.
    """
    parameters: List[BloodParameter] = Field(
        description="Validated blood parameters from the pipeline"
    )
    abnormal_parameters: List[BloodParameter] = Field(
        default_factory=list,
        description="Subset of parameters with abnormal status"
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Raw OCR-extracted text (used by ExtractionAgent)"
    )
    user_context: Optional[UserContext] = Field(
        default=None,
        description="Patient demographics and medical history"
    )
    risk_assessment: Optional[RiskAssessment] = Field(
        default=None,
        description="Rule-based risk scores from domain layer"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameter summary (counts, percentages)"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Rule-based recommendations from interpreter"
    )


class AgentResult(BaseModel):
    """
    Standard output from any specialist agent.

    Every agent returns this exact schema, making it easy to
    collect, merge, and display results uniformly.
    """
    agent_name: str = Field(
        description="Human-readable agent identifier (e.g., 'Diagnosis Agent')"
    )
    status: Literal["success", "fallback", "error"] = Field(
        description="Whether the agent used LLM, fell back to rules, or failed"
    )
    provider_used: str = Field(
        default="rule-based",
        description="LLM provider/model used (e.g., 'groq/llama-3.1-8b-instant')"
    )
    content: str = Field(
        description="The agent's analysis text (markdown formatted)"
    )
    structured_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional machine-readable structured output"
    )
    execution_time_ms: int = Field(
        default=0,
        description="How long this agent took to execute"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if status is 'error'"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this agent completed"
    )


class CoordinatorResult(BaseModel):
    """
    Merged output from the CoordinatorAgent after all specialist agents complete.

    Contains both individual agent results and the merged executive summary.
    """
    agent_results: List[AgentResult] = Field(
        default_factory=list,
        description="Individual output from each specialist agent"
    )
    diagnosis_insights: Optional[str] = Field(
        default=None,
        description="Clinical interpretation from DiagnosisAgent"
    )
    enhanced_risk: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Enhanced risk profile from RiskAgent"
    )
    nutrition_plan: Optional[str] = Field(
        default=None,
        description="Diet/lifestyle plan from NutritionAgent"
    )
    executive_summary: Optional[str] = Field(
        default=None,
        description="Unified summary merging all agent insights"
    )
    agents_used: List[str] = Field(
        default_factory=list,
        description="List of provider/model identifiers used"
    )
    total_execution_time_ms: int = Field(
        default=0,
        description="Wall-clock time for the entire multi-agent phase"
    )
