"""
v3.0 tests — LLM provider layer, agent framework, and the wired API.

No network: a FakeProvider stands in for real LLM providers, and the
API fixture clears all API keys so every agent runs its rule-based path.
"""

# pyrefly: ignore [missing-import]
import json
import pytest


# ── Fake provider ────────────────────────────────────────────


class _FakeProvider:
    """Minimal LLMProvider stand-in — no network."""

    def __init__(self, name="fake", available=True, reply="LLM_REPLY", raises=False):
        self._name = name
        self._available = available
        self._reply = reply
        self._raises = raises
        self.calls = 0

    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None):
        self.calls += 1
        if self._raises:
            raise RuntimeError("boom")
        return self._reply

    async def chat(self, messages, system_prompt=None, temperature=None, max_tokens=None):
        self.calls += 1
        if self._raises:
            raise RuntimeError("boom")
        return self._reply

    @property
    def available(self):
        return self._available

    @property
    def provider_name(self):
        return self._name

    @property
    def model_name(self):
        return "fake-1"

    @property
    def display_name(self):
        return f"{self._name}/fake-1"

    def get_status(self):
        return {"provider": self._name, "available": self._available, "model": "fake-1"}


def _params(*specs):
    from backend.models.blood_parameter import BloodParameter, ParameterStatus
    return [
        BloodParameter(name=n, value=v, unit="g/dL", status=ParameterStatus(s))
        for n, v, s in specs
    ]


def _context(parameters=None):
    from backend.agents.agent_models import AgentContext
    parameters = parameters or _params(("Hemoglobin", 10.0, "LOW"))
    abnormal = [p for p in parameters if p.status.value != "NORMAL"]
    return AgentContext(
        parameters=parameters, abnormal_parameters=abnormal, raw_text="Hemoglobin 10.0"
    )


# ── Provider registry ───────────────────────────────────────


class TestProviderRegistry:
    def test_registers_only_available(self):
        from backend.services.llm.provider_registry import ProviderRegistry
        reg = ProviderRegistry(
            groq_provider=_FakeProvider("groq", available=True),
            gemini_provider=_FakeProvider("gemini", available=False),
        )
        assert reg.list_available() == ["groq"]
        assert reg.has_providers is True

    def test_get_provider_preference_and_fallback(self):
        from backend.services.llm.provider_registry import ProviderRegistry
        reg = ProviderRegistry(
            groq_provider=_FakeProvider("groq"),
            gemini_provider=_FakeProvider("gemini"),
        )
        assert reg.get_provider("gemini").provider_name == "gemini"
        assert reg.get_provider("nope").provider_name in ("groq", "gemini")

    def test_empty_registry(self):
        from backend.services.llm.provider_registry import ProviderRegistry
        reg = ProviderRegistry()
        assert reg.has_providers is False
        assert reg.get_default() is None
        assert reg.get_provider("groq") is None


class TestLLMServiceFacade:
    @pytest.mark.asyncio
    async def test_generate_uses_default_provider(self):
        from backend.services.llm_service import LLMService
        from backend.services.llm.provider_registry import ProviderRegistry
        svc = LLMService(ProviderRegistry(groq_provider=_FakeProvider("groq", reply="HELLO")))
        assert svc.available is True
        assert await svc.generate("hi") == "HELLO"

    @pytest.mark.asyncio
    async def test_unavailable_returns_fallback_message(self):
        from backend.services.llm_service import LLMService
        from backend.services.llm.provider_registry import ProviderRegistry
        svc = LLMService(ProviderRegistry())
        assert svc.available is False
        assert "not available" in (await svc.generate("hi")).lower()


# ── Agent framework ─────────────────────────────────────────


class TestBaseAgentExecution:
    @pytest.mark.asyncio
    async def test_uses_llm_when_available(self):
        from backend.agents.diagnosis_agent import DiagnosisAgent
        result = await DiagnosisAgent(_FakeProvider("groq", reply="## Findings\nok")).execute(_context())
        assert result.status == "success"
        assert result.provider_used == "groq/fake-1"
        assert "Findings" in result.content

    @pytest.mark.asyncio
    async def test_falls_back_on_llm_error(self):
        from backend.agents.diagnosis_agent import DiagnosisAgent
        result = await DiagnosisAgent(_FakeProvider("groq", raises=True)).execute(_context())
        assert result.status == "fallback"
        assert result.provider_used == "rule-based"
        assert result.content

    @pytest.mark.asyncio
    async def test_rule_based_when_no_provider(self):
        from backend.agents.nutrition_agent import NutritionAgent
        result = await NutritionAgent(None).execute(_context())
        assert result.status == "fallback"
        assert "recommendation" in result.content.lower()


class TestCoordinatorAgent:
    @pytest.mark.asyncio
    async def test_orchestrate_merges_all_agents(self):
        from backend.agents import (
            CoordinatorAgent, ExtractionAgent, DiagnosisAgent, RiskAgent, NutritionAgent,
        )
        coord = CoordinatorAgent(
            extraction_agent=ExtractionAgent(_FakeProvider("gemini", reply='{"Hemoglobin": {"value": 10.0, "unit": "g/dL"}}')),
            diagnosis_agent=DiagnosisAgent(_FakeProvider("groq", reply="## Diagnosis\npattern")),
            risk_agent=RiskAgent(_FakeProvider("groq", reply="## Risk\nmoderate")),
            nutrition_agent=NutritionAgent(_FakeProvider("gemini", reply="## Nutrition\ngreens")),
        )
        out = await coord.orchestrate(
            parameters=_params(("Hemoglobin", 10.0, "LOW")),
            abnormal_parameters=_params(("Hemoglobin", 10.0, "LOW")),
            raw_text="Hemoglobin 10.0",
        )
        assert len(out.agent_results) == 4
        assert out.diagnosis_insights is not None
        assert out.nutrition_plan is not None
        assert out.executive_summary

    @pytest.mark.asyncio
    async def test_partial_failure_does_not_crash(self):
        from backend.agents import CoordinatorAgent, DiagnosisAgent, RiskAgent, NutritionAgent
        coord = CoordinatorAgent(
            diagnosis_agent=DiagnosisAgent(_FakeProvider("groq", raises=True)),
            risk_agent=RiskAgent(_FakeProvider("groq", reply="## Risk\nok")),
            nutrition_agent=NutritionAgent(None),
        )
        out = await coord.orchestrate(
            parameters=_params(("Hemoglobin", 10.0, "LOW")),
            abnormal_parameters=_params(("Hemoglobin", 10.0, "LOW")),
            raw_text="x",
        )
        statuses = {r.agent_name: r.status for r in out.agent_results}
        assert statuses["Risk Agent"] == "success"
        assert statuses["Diagnosis Agent"] == "fallback"


class TestConversationalAgent:
    @pytest.mark.asyncio
    async def test_rule_based_fallback_lists_abnormal(self):
        from backend.agents.conversational_agent import ConversationalAgent
        answer = await ConversationalAgent(None).ask(
            question="what is abnormal?",
            parameters=_params(("Hemoglobin", 10.0, "LOW"), ("WBC", 14000.0, "HIGH")),
        )
        assert "Hemoglobin" in answer

    @pytest.mark.asyncio
    async def test_uses_llm(self):
        from backend.agents.conversational_agent import ConversationalAgent
        answer = await ConversationalAgent(_FakeProvider("groq", reply="per the Diagnosis Agent")).ask(
            question="summarize",
            parameters=_params(("Hemoglobin", 10.0, "LOW")),
        )
        assert "Diagnosis Agent" in answer


# ── Wired API (no LLM keys → rule-based agents, no network) ──


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient
    from backend import config

    for var in ("GROQ_API_KEY", "GEMINI_API_KEY", "NVIDIA_API_KEY",
                "SUPABASE_URL", "SUPABASE_KEY", "API_KEY"):
        monkeypatch.setenv(var, "")
    config.get_settings.cache_clear()

    import backend.main as m
    with TestClient(m.create_app()) as c:
        yield c
    config.get_settings.cache_clear()


class TestWiredAPI:
    def test_health_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["version"] == "3.0.0"

    def test_analyze_runs_agent_pipeline(self, client):
        payload = json.dumps({"parameters": [
            {"name": "Hemoglobin", "value": 10.1, "unit": "g/dL"},
            {"name": "Glucose", "value": 145, "unit": "mg/dL"},
        ]}).encode()
        r = client.post(
            "/api/analyze",
            files={"file": ("r.json", payload, "application/json")},
            data={"user_id": "t"},
        )
        assert r.status_code == 200
        analysis = r.json()["analysis"]
        assert {p["name"] for p in analysis["parameters"]} >= {"Hemoglobin", "Glucose"}
        reports = analysis["agent_reports"]
        assert {x["agent_name"] for x in reports} >= {"Diagnosis Agent", "Risk Agent", "Nutrition Agent"}
        assert all(x["status"] == "fallback" for x in reports)

    def test_chat_404_for_missing_report(self, client):
        r = client.post("/api/chat", json={"report_id": "missing", "message": "hello there"})
        assert r.status_code == 404

    def test_analyze_then_chat(self, client):
        payload = json.dumps({"parameters": [
            {"name": "Hemoglobin", "value": 10.1, "unit": "g/dL"},
        ]}).encode()
        rid = client.post(
            "/api/analyze",
            files={"file": ("r.json", payload, "application/json")},
            data={"user_id": "t"},
        ).json()["report_id"]
        r2 = client.post("/api/chat", json={"report_id": rid, "message": "what is abnormal?"})
        assert r2.status_code == 200
        assert r2.json()["message"]
