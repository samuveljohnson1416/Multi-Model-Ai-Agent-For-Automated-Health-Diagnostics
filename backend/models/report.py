"""
Report models — request/response schemas for analysis endpoints.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .blood_parameter import BloodParameter


class UserContext(BaseModel):
    """Optional user demographic context for personalized analysis."""
    age: Optional[int] = Field(default=None, ge=0, le=150)
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    medical_history: Optional[List[str]] = Field(default=None)
    lifestyle: Optional[str] = Field(default=None)
    is_smoker: Optional[bool] = Field(default=None)
    is_diabetic: Optional[bool] = Field(default=None)


class RiskAssessment(BaseModel):
    """Health risk assessment result."""
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str = Field(pattern="^(low|medium|high|critical|unknown)$")
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    framingham_risk: Optional[Dict[str, Any]] = Field(default=None)


class AnalysisResult(BaseModel):
    """Complete analysis output from the pipeline."""
    parameters: List[BloodParameter]
    summary: Dict[str, Any] = Field(default_factory=dict)
    abnormal_parameters: List[BloodParameter] = Field(default_factory=list)
    risks: RiskAssessment = Field(default_factory=lambda: RiskAssessment(
        risk_score=0, risk_level="unknown"
    ))
    recommendations: List[str] = Field(default_factory=list)
    llm_insights: Optional[str] = Field(
        default=None,
        description="LLM-generated clinical insights"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warnings during processing (e.g. OCR fallbacks)"
    )
    disclaimer: str = Field(
        default=(
            "This analysis is for informational purposes only and does not constitute "
            "medical advice. Always consult with a qualified healthcare provider."
        )
    )


class ReportCreate(BaseModel):
    """Internal model for storing a report to the database."""
    user_id: Optional[str] = None
    file_name: str
    file_type: str
    analysis: AnalysisResult
    user_context: Optional[UserContext] = None


class ReportResponse(BaseModel):
    """API response for a single report."""
    report_id: str
    created_at: datetime
    file_name: str
    file_type: str
    analysis: AnalysisResult
    user_context: Optional[UserContext] = None


class ReportSummary(BaseModel):
    """Lightweight report listing (for history page)."""
    report_id: str
    created_at: datetime
    file_name: str
    total_parameters: int
    abnormal_count: int
    risk_level: str
