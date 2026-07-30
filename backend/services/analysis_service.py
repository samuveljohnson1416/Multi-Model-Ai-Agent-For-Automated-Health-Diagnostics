"""
Analysis service — the single orchestrator for the full pipeline.

Replaces orchestrator.py + phase1 + phase2 with one clean async pipeline:
  OCR → Parse → Validate → Risk Calc → LLM Insights → Return
"""

import logging
from typing import Optional

from ..models.report import AnalysisResult, RiskAssessment, UserContext
from ..models.blood_parameter import BloodParameter, ParameterStatus
from ..domain.risk_calculator import calculate_basic_risk, calculate_framingham_risk, calculate_lipid_ratios
from ..domain.report_interpreter import interpret_parameters
from .ocr_service import OCRService
from .parser_service import ParserService
from .validator_service import ValidatorService
from .llm_service import LLMService

logger = logging.getLogger(__name__)

# ── Enable DEBUG logging for extraction/parsing checkpoints ──────────────────
# These are noisy and only emit when the corresponding loggers are at DEBUG.
# Flip to logging.INFO to silence them in production without removing the code.
logging.getLogger("backend.services.ocr_service").setLevel(logging.DEBUG)
logging.getLogger("backend.services.parser_service").setLevel(logging.DEBUG)


# System prompt for clinical insights
CLINICAL_SYSTEM_PROMPT = """You are a medical laboratory assistant AI. You analyze blood test results
and provide clear, helpful insights. You are NOT a doctor and always recommend
consulting a healthcare provider for medical decisions.

Guidelines:
- Be concise and use simple language
- Highlight the most clinically significant findings first
- Mention possible conditions associated with abnormal values
- Suggest relevant follow-up tests when appropriate
- Always include a disclaimer that this is not medical advice
- Format your response with clear sections using markdown"""


class AnalysisService:
    """
    Orchestrates the complete blood report analysis pipeline.
    One class, one method, one clean flow.
    """

    def __init__(
        self,
        ocr_service: OCRService,
        parser_service: ParserService,
        validator_service: ValidatorService,
        llm_service: LLMService,
    ):
        self.ocr = ocr_service
        self.parser = parser_service
        self.validator = validator_service
        self.llm = llm_service

    async def analyze(
        self,
        file_bytes: bytes,
        file_type: str,
        user_context: Optional[UserContext] = None,
    ) -> AnalysisResult:
        """
        Run the full analysis pipeline.

        Steps:
          1. Extract text from document (OCR/direct)
          2. Parse text into raw parameters
          3. Validate against reference ranges
          4. Calculate risk scores
          5. Generate LLM insights (if available)

        Args:
            file_bytes: Raw file content
            file_type: File extension (pdf, png, jpg, json, csv, txt)
            user_context: Optional patient demographics for personalization

        Returns:
            Complete AnalysisResult

        Raises:
            ValueError: If extraction or parsing fails completely
        """
        age = user_context.age if user_context else None
        gender = user_context.gender if user_context else None

        # ── Step 1: Extract text ─────────────────────────────
        logger.info(f"Step 1: Extracting text from {file_type} file")
        extraction = await self.ocr.extract_text(file_bytes, file_type)
        logger.info(f"Extracted {len(extraction.text)} chars via {extraction.source}")
        
        warnings = []
        if self.ocr._nvidia_api_key and extraction.source == "tesseract":
            warnings.append("NVIDIA OCR API failed or was unavailable, falling back to local Tesseract OCR.")

        # ── Step 2: Parse parameters ──────────────────────────
        logger.info("Step 2: Parsing blood parameters")

        # ── [RAW TEXT DUMP] Full extraction output before any parsing ──
        # This is the definitive boundary between extraction and parsing.
        # If a value appears here but not in parsed params, it died in parsing.
        # If it's absent here, it was lost in extraction (pdfplumber / OCR).
        logger.debug(
            "[RAW TEXT DUMP] %d chars via '%s'. Full text below:\n%s",
            len(extraction.text),
            extraction.source,
            extraction.text,
        )

        raw_params = self.parser.parse(extraction.text)

        if not raw_params:
            raise ValueError(
                "No blood parameters could be extracted from this document. "
                "Please ensure it contains a blood test report with numeric values."
            )

        logger.info(f"Parsed {len(raw_params)} parameters: {list(raw_params.keys())}")

        # ── Step 3: Validate parameters ───────────────────────
        logger.info("Step 3: Validating against reference ranges")
        parameters = self.validator.validate(raw_params, age=age, gender=gender)

        if not parameters:
            raise ValueError("Parameter validation failed — no valid parameters found.")

        # ── Step 4: Interpret & calculate risks ───────────────
        logger.info("Step 4: Computing risk scores")
        interpretation = interpret_parameters(parameters)
        abnormal = interpretation["abnormal_parameters"]

        # Basic risk score
        param_dict = {p.name: {"status": p.status.value, "value": p.value} for p in parameters}
        basic_risk = calculate_basic_risk(param_dict)

        # Framingham risk (if we have the data)
        framingham = None
        if age and gender:
            cholesterol_param = next((p for p in parameters if p.name == "Cholesterol"), None)
            hdl_param = next((p for p in parameters if p.name == "HDL"), None)
            is_smoker = user_context.is_smoker if user_context else False

            if cholesterol_param or hdl_param:
                framingham = calculate_framingham_risk(
                    age=age,
                    gender=gender,
                    total_cholesterol=cholesterol_param.value if cholesterol_param else None,
                    hdl=hdl_param.value if hdl_param else None,
                    is_smoker=is_smoker or False,
                )

        # Lipid ratios
        lipid_params = {p.name: p.value for p in parameters}
        lipid_ratios = calculate_lipid_ratios(
            total_cholesterol=lipid_params.get("Cholesterol"),
            hdl=lipid_params.get("HDL"),
            ldl=lipid_params.get("LDL"),
            triglycerides=lipid_params.get("Triglycerides"),
        )

        risk = RiskAssessment(
            risk_score=basic_risk["risk_score"],
            risk_level=basic_risk["risk_level"],
            risk_factors=basic_risk["risk_factors"],
            framingham_risk=framingham,
        )

        # ── Step 5: LLM insights (non-blocking) ──────────────
        logger.info("Step 5: Generating LLM insights")
        llm_insights = None
        if self.llm.available and abnormal:
            try:
                llm_insights = await self._generate_insights(
                    parameters, abnormal, risk, user_context
                )
            except Exception as e:
                logger.warning(f"LLM insights failed (non-critical): {e}")

        # ── Build result ──────────────────────────────────────
        summary = interpretation["summary"]
        if lipid_ratios:
            summary["lipid_ratios"] = lipid_ratios

        recommendations = interpretation["recommendations"]

        return AnalysisResult(
            parameters=parameters,
            summary=summary,
            abnormal_parameters=abnormal,
            risks=risk,
            recommendations=recommendations,
            llm_insights=llm_insights,
            warnings=warnings,
        )

    async def _generate_insights(
        self,
        all_params: list[BloodParameter],
        abnormal: list[BloodParameter],
        risk: RiskAssessment,
        user_context: Optional[UserContext],
    ) -> str:
        """Generate LLM-powered clinical insights."""
        # Build a concise prompt with the key findings
        abnormal_lines = []
        for p in abnormal:
            abnormal_lines.append(
                f"- {p.name}: {p.value} {p.unit} ({p.status.value}, "
                f"ref: {p.reference_range or 'N/A'}, severity: {p.severity or 'N/A'})"
            )

        context_str = ""
        if user_context:
            parts = []
            if user_context.age:
                parts.append(f"Age: {user_context.age}")
            if user_context.gender:
                parts.append(f"Gender: {user_context.gender}")
            if user_context.medical_history:
                parts.append(f"Medical history: {', '.join(user_context.medical_history)}")
            if parts:
                context_str = f"\nPatient context: {', '.join(parts)}"

        prompt = f"""Analyze these blood test results and provide clinical insights:

Total parameters tested: {len(all_params)}
Abnormal findings:
{chr(10).join(abnormal_lines)}

Overall risk level: {risk.risk_level} (score: {risk.risk_score})
{context_str}

Provide:
1. Key findings summary (2-3 sentences)
2. Possible clinical significance of the abnormal values
3. Recommended follow-up tests
4. General lifestyle recommendations

Keep the response concise (under 300 words)."""

        return await self.llm.generate(
            prompt=prompt,
            system_prompt=CLINICAL_SYSTEM_PROMPT,
            temperature=0.1,
        )
