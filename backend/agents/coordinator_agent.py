"""
Coordinator Agent — master orchestrator for the multi-agent pipeline.

Responsibilities:
  1. Build the shared AgentContext from extraction/parsing results
  2. Run the ExtractionAgent first (others depend on its output)
  3. Dispatch Diagnosis, Risk, Nutrition agents IN PARALLEL (asyncio.gather)
  4. Collect all AgentResults and merge into a CoordinatorResult
  5. Handle partial failures gracefully (one agent failing doesn't crash others)
"""

import asyncio
import time
import logging
from typing import Optional, List

from ..models.blood_parameter import BloodParameter
from ..models.report import UserContext, RiskAssessment
from .agent_models import AgentContext, AgentResult, CoordinatorResult
from .extraction_agent import ExtractionAgent
from .diagnosis_agent import DiagnosisAgent
from .risk_agent import RiskAgent
from .nutrition_agent import NutritionAgent

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """
    Master orchestrator that delegates work to specialist agents.

    Execution flow:
      Phase 1 (sequential): ExtractionAgent refines parameters
      Phase 2 (parallel):   DiagnosisAgent + RiskAgent + NutritionAgent
      Phase 3 (merge):      Combine all results into CoordinatorResult
    """

    def __init__(
        self,
        extraction_agent: Optional[ExtractionAgent] = None,
        diagnosis_agent: Optional[DiagnosisAgent] = None,
        risk_agent: Optional[RiskAgent] = None,
        nutrition_agent: Optional[NutritionAgent] = None,
    ):
        self._extraction = extraction_agent
        self._diagnosis = diagnosis_agent
        self._risk = risk_agent
        self._nutrition = nutrition_agent

        active = [
            a.agent_name for a in [extraction_agent, diagnosis_agent, risk_agent, nutrition_agent]
            if a is not None
        ]
        logger.info(f"CoordinatorAgent initialized with {len(active)} agents: {active}")

    async def orchestrate(
        self,
        parameters: List[BloodParameter],
        abnormal_parameters: List[BloodParameter],
        raw_text: str,
        user_context: Optional[UserContext] = None,
        risk_assessment: Optional[RiskAssessment] = None,
        summary: Optional[dict] = None,
        recommendations: Optional[List[str]] = None,
    ) -> CoordinatorResult:
        """
        Run the full multi-agent analysis pipeline.

        Args:
            parameters: Validated blood parameters from the pipeline.
            abnormal_parameters: Subset with abnormal status.
            raw_text: Raw OCR-extracted text.
            user_context: Optional patient demographics.
            risk_assessment: Rule-based risk scores.
            summary: Parameter summary from interpreter.
            recommendations: Rule-based recommendations.

        Returns:
            CoordinatorResult with all agent outputs merged.
        """
        wall_start = time.perf_counter()
        all_results: List[AgentResult] = []
        agents_used: List[str] = []

        # Build shared context
        context = AgentContext(
            parameters=parameters,
            abnormal_parameters=abnormal_parameters,
            raw_text=raw_text,
            user_context=user_context,
            risk_assessment=risk_assessment,
            summary=summary or {},
            recommendations=recommendations or [],
        )

        # ── Phase 1: Extraction (sequential — others depend on it) ────
        if self._extraction:
            logger.info("Coordinator Phase 1: Running ExtractionAgent")
            extraction_result = await self._extraction.execute(context)
            all_results.append(extraction_result)
            if extraction_result.provider_used != "rule-based":
                agents_used.append(extraction_result.provider_used)
            logger.info(
                f"ExtractionAgent: {extraction_result.status} "
                f"({extraction_result.execution_time_ms}ms)"
            )

        # ── Phase 2: Analysis agents (parallel via asyncio.gather) ────
        logger.info("Coordinator Phase 2: Running analysis agents in parallel")

        parallel_tasks = []
        agent_names = []

        if self._diagnosis:
            parallel_tasks.append(self._diagnosis.execute(context))
            agent_names.append("DiagnosisAgent")

        if self._risk:
            parallel_tasks.append(self._risk.execute(context))
            agent_names.append("RiskAgent")

        if self._nutrition:
            parallel_tasks.append(self._nutrition.execute(context))
            agent_names.append("NutritionAgent")

        if parallel_tasks:
            # return_exceptions=True ensures one failure doesn't cancel others
            results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"{agent_names[i]} threw exception: {result}")
                    all_results.append(AgentResult(
                        agent_name=agent_names[i],
                        status="error",
                        content=f"Agent failed: {str(result)}",
                        error_message=str(result),
                    ))
                elif isinstance(result, AgentResult):
                    all_results.append(result)
                    if result.provider_used != "rule-based":
                        agents_used.append(result.provider_used)
                    logger.info(
                        f"{result.agent_name}: {result.status} "
                        f"({result.execution_time_ms}ms via {result.provider_used})"
                    )

        # ── Phase 3: Merge results ────────────────────────────────────
        total_ms = int((time.perf_counter() - wall_start) * 1000)
        logger.info(
            f"Coordinator complete: {len(all_results)} agents, "
            f"{total_ms}ms total wall-clock"
        )

        return self._merge_results(all_results, agents_used, total_ms)

    def _merge_results(
        self,
        results: List[AgentResult],
        agents_used: List[str],
        total_ms: int,
    ) -> CoordinatorResult:
        """Merge individual agent results into a unified output."""
        diagnosis_insights = None
        enhanced_risk = None
        nutrition_plan = None

        for r in results:
            if r.agent_name == "Diagnosis Agent" and r.status != "error":
                diagnosis_insights = r.content
            elif r.agent_name == "Risk Agent" and r.status != "error":
                enhanced_risk = {
                    "content": r.content,
                    "structured": r.structured_data,
                }
            elif r.agent_name == "Nutrition Agent" and r.status != "error":
                nutrition_plan = r.content

        # Build executive summary from successful agents
        executive_summary = self._build_executive_summary(results)

        return CoordinatorResult(
            agent_results=results,
            diagnosis_insights=diagnosis_insights,
            enhanced_risk=enhanced_risk,
            nutrition_plan=nutrition_plan,
            executive_summary=executive_summary,
            agents_used=list(set(agents_used)),
            total_execution_time_ms=total_ms,
        )

    def _build_executive_summary(self, results: List[AgentResult]) -> str:
        """Build a brief unified summary from all agent outputs."""
        successful = [r for r in results if r.status in ("success", "fallback")]

        if not successful:
            return "Multi-agent analysis could not be completed. Please review the individual parameter results."

        summary_parts = []
        for r in successful:
            if r.agent_name == "Extraction Agent":
                continue  # Skip extraction from summary
            # Take first 2 sentences from each agent's content
            sentences = r.content.split(". ")[:2]
            brief = ". ".join(sentences)
            if not brief.endswith("."):
                brief += "."
            summary_parts.append(f"**{r.agent_name}:** {brief}")

        if summary_parts:
            return "\n\n".join(summary_parts)

        return "Analysis complete. Please review the detailed agent reports below."
