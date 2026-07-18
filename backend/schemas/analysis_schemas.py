"""
Pydantic request/response schemas for the analysis endpoint.
"""

from pydantic import BaseModel
from typing import Optional, List, Any


class UserContext(BaseModel):
    """Optional demographic and lifestyle context for contextual analysis."""

    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[List[str]] = []
    lifestyle: Optional[dict] = {}


class AnalysisRequest(BaseModel):
    """Request body for the /api/analyze endpoint."""

    validated_data: dict
    phase1_csv: Optional[str] = None
    user_context: Optional[UserContext] = None
    filename: Optional[str] = "report"
    run_phase2: Optional[bool] = True
    run_contextual: Optional[bool] = True


class ParameterClassification(BaseModel):
    value: Any
    status: str
    reference_range: Optional[str] = None


class RiskScore(BaseModel):
    score: float
    level: str
    details: Optional[dict] = {}


class AnalysisResponse(BaseModel):
    """Response returned after multi-model analysis."""

    # Model 1 — parameter classification
    total_parameters: int = 0
    abnormal_parameters: int = 0
    normal_parameters: int = 0
    classifications: Optional[dict] = {}
    severity_analysis: Optional[dict] = {}

    # Model 2 — pattern recognition
    patterns_detected: Optional[List[dict]] = []
    pattern_count: int = 0
    pattern_names: Optional[List[str]] = []

    # Model 3 — risk scores
    overall_risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    requires_attention: Optional[bool] = False
    anemia_risk: Optional[dict] = {}
    infection_risk: Optional[dict] = {}
    bleeding_risk: Optional[dict] = {}
    cardiovascular_risk: Optional[dict] = {}
    renal_risk: Optional[dict] = {}

    # Recommendations
    recommendations: Optional[List[dict]] = []

    # Phase-2 LLM insights
    phase2_result: Optional[dict] = None

    # Contextual analysis
    contextual_analysis: Optional[dict] = None

    # Meta
    decision_method: str = "RULE-BASED"
    error: Optional[str] = None
    success: bool = True
