"""
Blood parameter models — the core data unit of the system.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ParameterStatus(str, Enum):
    """Status of a blood parameter relative to its reference range."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    BORDERLINE = "BORDERLINE"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class BloodParameter(BaseModel):
    """
    A single blood test parameter with its value, unit, status, and reference range.
    This is the atomic data unit — every part of the system speaks this schema.
    """
    name: str = Field(description="Standardized parameter name (e.g. 'Hemoglobin')")
    value: float = Field(description="Numeric test value")
    unit: str = Field(default="N/A", description="Unit of measurement (e.g. 'g/dL')")
    status: ParameterStatus = Field(default=ParameterStatus.UNKNOWN)
    reference_range: Optional[str] = Field(
        default=None,
        description="Display string for reference range (e.g. '12.0 - 16.0 g/dL')"
    )
    reference_min: Optional[float] = Field(default=None)
    reference_max: Optional[float] = Field(default=None)
    deviation_percent: Optional[float] = Field(
        default=None,
        description="How far outside the reference range (0 = within range)"
    )
    severity: Optional[str] = Field(
        default=None,
        description="Mild / Moderate / Severe based on deviation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Hemoglobin",
                "value": 11.2,
                "unit": "g/dL",
                "status": "LOW",
                "reference_range": "12.0 - 16.0 g/dL",
                "reference_min": 12.0,
                "reference_max": 16.0,
                "deviation_percent": 6.67,
                "severity": "Mild",
            }
        }
    }
