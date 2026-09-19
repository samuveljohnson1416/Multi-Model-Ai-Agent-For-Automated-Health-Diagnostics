"""Autonomous Diagnosis agent: tool loop behaviour, with a scripted fake provider (no network)."""
import asyncio

from backend.agents.agent_models import AgentContext
from backend.agents.diagnosis_agent import DiagnosisAgent
from backend.services.llm.provider_base import LLMProvider
from backend.services.validator_service import ValidatorService

RAW = {
    "WBC": {"value": 16500.0, "unit": "/cumm", "reference_range": "4000 - 11000"},
    "Neutrophils": {"value": 85.0, "unit": "%", "reference_range": "50 - 62"},
    "Hemoglobin": {"value": 13.8, "unit": "g/dL", "reference_range": "13.0 - 17.0"},
}


def _ctx():
    params = ValidatorService().validate(RAW)
    return AgentContext(
        parameters=params,
        abnormal_parameters=[p for p in params if p.status.value != "NORMAL"],
        raw_text="WBC 16500 High\nInterpretation: correlate clinically",
    )


class Scripted(LLMProvider):
    """Replays scripted replies; records the messages it was sent."""
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    supports_tools = True
    available = True
    provider_name, model_name = "fake", "scripted"

    async def generate(self, *a, **k): raise AssertionError("single-shot path must not be used")
    async def chat(self, *a, **k): raise AssertionError

    async def chat_with_tools(self, messages, tools=None, **k):
        self.seen.append((list(messages), tools))
        return self.replies.pop(0)


def call(tool, **args):
    return {"content": None, "tool_calls": [{"id": f"c-{tool}", "name": tool, "arguments": args}]}


def final(text):
    return {"content": text, "tool_calls": []}


def run(provider):
    return asyncio.run(DiagnosisAgent(provider).execute(_ctx()))


def test_agent_calls_tools_then_answers():
    p = Scripted([call("list_parameters", abnormal_only=True), call("get_parameter", name="WBC"), final("Infection pattern.")])
    r = run(p)
    assert r.status == "success" and r.content == "Infection pattern."
    assert [s.split("(")[0] for s in r.structured_data["tool_calls"]] == ["list_parameters", "get_parameter"]
    # tool results were fed back to the model
    tool_msgs = [m for m in p.seen[-1][0] if m["role"] == "tool"]
    assert "16500" in tool_msgs[1]["content"]


def test_bad_tool_call_is_reported_back_not_fatal():
    p = Scripted([call("nope"), call("get_parameter", name="Ferritin"), final("ok")])
    r = run(p)
    assert r.status == "success"
    tool_msgs = [m["content"] for m in p.seen[-1][0] if m["role"] == "tool"]
    assert "unknown tool" in tool_msgs[0] and "not measured" in tool_msgs[1]


def test_step_cap_forces_final_answer():
    from backend.agents.tools import MAX_STEPS
    p = Scripted([call("list_parameters")] * MAX_STEPS + [final("forced answer")])
    r = run(p)
    assert r.status == "success" and r.content == "forced answer"
    assert p.seen[-1][1] is None  # last request offered no tools


def test_provider_failure_falls_back_to_rules():
    class Boom(Scripted):
        async def chat_with_tools(self, *a, **k): raise RuntimeError("404 model_not_found")
    r = run(Boom([]))
    assert r.status == "fallback" and "Key Findings" in r.content


def test_slow_model_is_cut_off_and_falls_back(monkeypatch):
    import backend.agents.base_agent as base_agent

    class Slow(Scripted):
        async def chat_with_tools(self, *a, **k):
            await asyncio.sleep(5)

    monkeypatch.setattr(base_agent, "AGENT_TIMEOUT_S", 0.2)
    r = run(Slow([]))
    assert r.status == "fallback" and "Key Findings" in r.content
