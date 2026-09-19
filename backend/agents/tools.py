"""
Read-only tools and the tool-calling loop for autonomous agents.

The pipeline's deterministic results (parsed values, LOW/HIGH status, risk scores)
are exposed as tools. An agent decides which to call, in what order, and when it
has enough to answer. Tools never modify data, so the model can interpret the
results but cannot change them.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from ..domain.reference_ranges import get_reference_range, normalize_parameter_name
from ..services.llm.provider_base import LLMProvider
from .agent_models import AgentContext

logger = logging.getLogger(__name__)

MAX_STEPS = 6  # ponytail: hard cap on tool rounds; raise only if answers get cut short


def _schema(name: str, description: str, properties: Dict[str, Any] = None, required: List[str] = None) -> Dict:
    properties, required = properties or {}, required or []
    # Models routinely send null for optional args; Groq rejects that (400) unless the schema allows it.
    properties = {
        k: v if k in required else {**v, "type": [v["type"], "null"]} for k, v in properties.items()
    }
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def build_tools(ctx: AgentContext) -> Dict[str, Tuple[Dict, Callable[..., Any]]]:
    """Map tool name -> (schema, function), all bound to this request's context."""

    def _row(p) -> Dict:
        return {
            "name": p.name, "value": p.value, "unit": p.unit, "status": p.status.value,
            "reference_range": p.reference_range, "severity": p.severity,
        }

    def list_parameters(abnormal_only: bool = False):
        params = ctx.abnormal_parameters if abnormal_only else ctx.parameters
        return [_row(p) for p in params]

    def get_parameter(name: str):
        canonical = normalize_parameter_name(name)
        for p in ctx.parameters:
            if p.name == canonical or p.name.lower() == name.lower():
                return _row(p)
        return {"error": f"'{name}' was not measured in this report"}

    def lookup_reference_range(name: str, age: int = None, gender: str = None):
        uc = ctx.user_context
        age = age if age is not None else (uc.age if uc else None)
        gender = gender or (uc.gender if uc else None)
        ref = get_reference_range(name, age=age, gender=gender)
        return ref or {"error": f"no built-in reference range for '{name}'"}

    def get_patient_context():
        return ctx.user_context.model_dump(exclude_none=True) if ctx.user_context else {}

    def get_risk_scores():
        return ctx.risk_assessment.model_dump(mode="json") if ctx.risk_assessment else {}

    def search_report_text(query: str):
        lines = (ctx.raw_text or "").splitlines()
        hits = [l.strip() for l in lines if query.lower() in l.lower()]
        return hits[:10] or {"error": f"'{query}' not found in the report text"}

    tools = [
        (_schema("list_parameters", "List measured blood parameters with value, unit, status and reference range.",
                 {"abnormal_only": {"type": "boolean", "description": "Only return abnormal ones"}}),
         list_parameters),
        (_schema("get_parameter", "Get one parameter by name (e.g. 'WBC', 'Hemoglobin').",
                 {"name": {"type": "string"}}, ["name"]),
         get_parameter),
        (_schema("lookup_reference_range", "Standard reference range for a parameter, adjusted for the patient's age/gender.",
                 {"name": {"type": "string"}, "age": {"type": "integer"}, "gender": {"type": "string"}}, ["name"]),
         lookup_reference_range),
        (_schema("get_patient_context", "Patient age, gender, medical history, smoker/diabetic flags."),
         get_patient_context),
        (_schema("get_risk_scores", "Rule-based risk assessment computed for this report."),
         get_risk_scores),
        (_schema("search_report_text", "Search the original report text for a word (lab comments, flags, notes).",
                 {"query": {"type": "string"}}, ["query"]),
         search_report_text),
    ]
    return {s["function"]["name"]: (s, fn) for s, fn in tools}


async def run_tool_loop(
    provider: LLMProvider,
    system_prompt: str,
    task: str,
    tools: Dict[str, Tuple[Dict, Callable[..., Any]]],
    max_steps: int = MAX_STEPS,
    max_tokens: int = 1500,
) -> Tuple[str, List[str]]:
    """
    Let the model call tools until it answers. Returns (final_text, steps).

    Raises on provider errors or an empty answer, so the caller's rule-based
    fallback takes over.
    """
    schemas = [s for s, _ in tools.values()]
    messages: List[Dict] = [{"role": "user", "content": task}]
    steps: List[str] = []

    for _ in range(max_steps):
        reply = await provider.chat_with_tools(
            messages, schemas, system_prompt=system_prompt, temperature=0.1, max_tokens=max_tokens
        )
        if not reply["tool_calls"]:
            break

        messages.append({
            "role": "assistant",
            "content": reply["content"] or "",
            "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}}
                for c in reply["tool_calls"]
            ],
        })
        for call in reply["tool_calls"]:
            name, args = call["name"], call["arguments"]
            steps.append(f"{name}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
            try:
                if name not in tools:
                    raise KeyError(f"unknown tool '{name}'")
                result = tools[name][1](**args)
            except Exception as e:  # bad args / unknown tool: tell the model, let it recover
                result = {"error": str(e)}
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
    else:
        # Step cap hit while the model still wanted tools: force a final answer.
        messages.append({"role": "user", "content": "Step limit reached. Write your final answer now using what you have."})
        reply = await provider.chat_with_tools(
            messages, None, system_prompt=system_prompt, temperature=0.1, max_tokens=max_tokens
        )

    if not reply["content"]:
        raise ValueError("agent produced no final answer")
    logger.info("Tool loop finished after %d tool call(s): %s", len(steps), steps)
    return reply["content"], steps
