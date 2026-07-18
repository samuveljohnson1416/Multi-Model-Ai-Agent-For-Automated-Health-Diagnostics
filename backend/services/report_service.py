"""
Report Service
==============
Generates comprehensive PDF-ready text reports by delegating to
core.comprehensive_report_generator.ComprehensiveReportGenerator.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_report(
    validated_data: dict,
    analysis_result: dict,
    contextual_analysis: Optional[dict],
    user_context: Optional[dict],
    filename: str = "report",
    format_type: str = "text",
) -> dict:
    """
    Generate a comprehensive text/JSON report for a blood analysis.

    Returns:
        {"report": str, "success": bool, "error": str|None}
    """
    try:
        from core.comprehensive_report_generator import create_comprehensive_report_generator

        generator = create_comprehensive_report_generator()
        report_text = generator.generate_comprehensive_report(
            validated_data=validated_data,
            ai_analysis=analysis_result,
            contextual_analysis=contextual_analysis or {},
            user_context=user_context or {},
            filename=filename,
            format_type=format_type,
        )
        return {"report": report_text, "success": True, "error": None}

    except Exception as exc:
        logger.exception("Report generation failed")
        return {"report": "", "success": False, "error": str(exc)}
