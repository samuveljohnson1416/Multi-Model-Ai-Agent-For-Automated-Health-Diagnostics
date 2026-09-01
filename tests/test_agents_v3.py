"""
v3.0 tests — LLM provider layer, agent framework, and the wired API.

No test doubles. Two kinds of tests:

  * Deterministic, offline: rule-based agent paths (provider = None), the
    real ProviderRegistry with unconfigured providers, and the real FastAPI
    app started with the API keys cleared.
  * Live: real Groq API calls, marked `requires_groq` and skipped when no
    Groq key is configured. Gemini is not exercised live (the project's
    current key is denied by Google).
"""

# pyrefly: ignore [missing-import]
import json
import pytest

from backend.config import get_settings
from backend.services.llm.groq_provider import GroqProvider
from backend.services.llm.gemini_provider import GeminiProvider
from backend.services.llm.provider_registry import ProviderRegistry

_SETTINGS = get_settings()
_HAS_GROQ = bool(_SETTINGS.groq_api_key)
_HAS_GEMINI = bool(_SETTINGS.gemini_api_key)

requires_groq = pytest.mark.skipif(not _HAS_GROQ, reason="Groq API key not configured")
requires_both = pytest.mark.skipif(
    not (_HAS_GROQ and _HAS_GEMINI), reason="Both Groq and Gemini keys required"
)

# A syntactically valid model id that Groq does not serve — used to force a
# real API error so the agent's rule-based fallback can be exercised.
_BAD_MODEL = "definitely-not-a-real-model-000"


def _real_groq(model: str | None = None) -> GroqProvider:
    return GroqProvider(
        api_key=_SETTINGS.groq_api_key,
        model=model or _SETTINGS.groq_model,
        temperature=_SETTINGS.groq_temperature,
        max_tokens=_SETTINGS.groq_max_tokens,
        timeout=_SETTINGS.groq_timeout,
    )


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
        parameters=parameters, abnormal_parameters=abnormal, raw_text="Hemoglobin 10.0 g/dL"
    )


# ── Provider registry (offline — construction makes no API calls) ──


class TestProviderRegistry:
    def test_registers_only_available(self):
        # Real GroqProvider with a key is available; real GeminiProvider with
        # no key has no client and is not available.
        reg = ProviderRegistry(
            groq_provider=GroqProvider(api_key="x-not-blank", model="m"),
            gemini_provider=GeminiProvider(api_key=""),
        )
        assert reg.list_available() == ["groq"]
        assert reg.has_providers is True

    def test_falls_back_when_preferred_absent(self):
        groq = GroqProvider(api_key="x-not-blank", model="m")
        reg = ProviderRegistry(groq_provider=groq)
        # "gemini" isn't registered → registry returns the one available provider
        assert reg.get_provider("gemini") is groq

    @requires_both
    def test_returns_preferred_when_present(self):
        reg = ProviderRegistry(
            groq_provider=_real_groq(),
            gemini_provider=GeminiProvider(
                api_key=_SETTINGS.gemini_api_key, model=_SETTINGS.gemini_model
            ),
        )
        assert reg.get_provider("gemini").provider_name == "gemini"
        assert reg.get_provider("groq").provider_name == "groq"

    def test_empty_registry(self):
        reg = ProviderRegistry()
        assert reg.has_providers is False
        assert reg.get_default() is None
        assert reg.get_provider("groq") is None


class TestLLMServiceFacade:
    def test_unavailable_returns_fallback_message(self):
        from backend.services.llm_service import LLMService
        svc = LLMService(ProviderRegistry())
        assert svc.available is False

    @pytest.mark.asyncio
    async def test_unavailable_generate_is_a_real_string(self):
        from backend.services.llm_service import LLMService
        svc = LLMService(ProviderRegistry())
        out = await svc.generate("hi")
        assert isinstance(out, str) and "not available" in out.lower()

    @requires_groq
    @pytest.mark.asyncio
    async def test_generate_hits_real_groq(self):
        from backend.services.llm_service import LLMService
        svc = LLMService(ProviderRegistry(groq_provider=_real_groq()))
        assert svc.available is True
        out = await svc.generate("Reply with exactly: PONG")
        assert isinstance(out, str) and out.strip() != ""


# ── Agent framework ─────────────────────────────────────────


class TestRuleBasedAgents:
    """provider = None → the agent's real deterministic path."""

    @pytest.mark.asyncio
    async def test_diagnosis_rule_based(self):
        from backend.agents.diagnosis_agent import DiagnosisAgent
        result = await DiagnosisAgent(None).execute(_context())
        assert result.status == "fallback"
        assert result.provider_used == "rule-based"
        assert "Hemoglobin" in result.content

    @pytest.mark.asyncio
    async def test_nutrition_rule_based(self):
        from backend.agents.nutrition_agent import NutritionAgent
        result = await NutritionAgent(None).execute(_context())
        assert result.status == "fallback"
        assert "recommendation" in result.content.lower()

    @pytest.mark.asyncio
    async def test_risk_rule_based_groups_by_organ_system(self):
        from backend.agents.risk_agent import RiskAgent
        result = await RiskAgent(None).execute(_context())
        assert result.status == "fallback"
        assert "Hematologic" in result.content


class TestLiveAgents:
    @requires_groq
    @pytest.mark.asyncio
    async def test_diagnosis_uses_real_groq(self):
        from backend.agents.diagnosis_agent import DiagnosisAgent
        result = await DiagnosisAgent(_real_groq()).execute(_context())
        assert result.status == "success"
        assert result.provider_used.startswith("groq/")
        assert result.content.strip() != ""

    @requires_groq
    @pytest.mark.asyncio
    async def test_agent_falls_back_on_real_api_error(self):
        # Real GroqProvider pointed at a model Groq doesn't serve → real 4xx →
        # BaseAgent catches it and runs the rule-based path.
        from backend.agents.diagnosis_agent import DiagnosisAgent
        result = await DiagnosisAgent(_real_groq(model=_BAD_MODEL)).execute(_context())
        assert result.status == "fallback"
        assert result.provider_used == "rule-based"
        assert result.content.strip() != ""


class TestCoordinatorAgent:
    @pytest.mark.asyncio
    async def test_orchestrate_all_rule_based(self):
        from backend.agents import (
            CoordinatorAgent, ExtractionAgent, DiagnosisAgent, RiskAgent, NutritionAgent,
        )
        coord = CoordinatorAgent(
            extraction_agent=ExtractionAgent(None),
            diagnosis_agent=DiagnosisAgent(None),
            risk_agent=RiskAgent(None),
            nutrition_agent=NutritionAgent(None),
        )
        out = await coord.orchestrate(
            parameters=_params(("Hemoglobin", 10.0, "LOW")),
            abnormal_parameters=_params(("Hemoglobin", 10.0, "LOW")),
            raw_text="Hemoglobin 10.0 g/dL",
        )
        assert len(out.agent_results) == 4
        assert {r.agent_name for r in out.agent_results} == {
            "Extraction Agent", "Diagnosis Agent", "Risk Agent", "Nutrition Agent",
        }
        assert out.executive_summary
        assert all(r.status in ("success", "fallback") for r in out.agent_results)

    @requires_groq
    @pytest.mark.asyncio
    async def test_orchestrate_partial_failure_with_real_groq(self):
        # Real calls: one good provider, one bad-model provider (real error →
        # fallback), one with no provider. The pipeline must still complete.
        from backend.agents import CoordinatorAgent, DiagnosisAgent, RiskAgent, NutritionAgent
        coord = CoordinatorAgent(
            diagnosis_agent=DiagnosisAgent(_real_groq(model=_BAD_MODEL)),
            risk_agent=RiskAgent(_real_groq()),
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
        assert statuses["Nutrition Agent"] == "fallback"


class TestConversationalAgent:
    @pytest.mark.asyncio
    async def test_rule_based_fallback_lists_abnormal(self):
        from backend.agents.conversational_agent import ConversationalAgent
        answer = await ConversationalAgent(None).ask(
            question="what is abnormal?",
            parameters=_params(("Hemoglobin", 10.0, "LOW"), ("WBC", 14000.0, "HIGH")),
        )
        assert "Hemoglobin" in answer

    @requires_groq
    @pytest.mark.asyncio
    async def test_uses_real_groq(self):
        from backend.agents.conversational_agent import ConversationalAgent
        answer = await ConversationalAgent(_real_groq()).ask(
            question="In one sentence, what is my hemoglobin status?",
            parameters=_params(("Hemoglobin", 10.0, "LOW")),
        )
        assert isinstance(answer, str) and answer.strip() != ""


# ── Wired API ───────────────────────────────────────────────


@pytest.fixture
def client_no_llm(monkeypatch):
    """Real FastAPI app with API keys cleared → every agent runs rule-based,
    no network. monkeypatch.setenv is pytest's env-var fixture (it sets real
    environment variables and restores them), not a code mock."""
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


@pytest.fixture
def client_live():
    """Real app with the real configured keys (used by live API tests)."""
    from fastapi.testclient import TestClient
    from backend import config

    config.get_settings.cache_clear()
    import backend.main as m
    with TestClient(m.create_app()) as c:
        yield c
    config.get_settings.cache_clear()


_SAMPLE_REPORT = json.dumps({"parameters": [
    {"name": "Hemoglobin", "value": 10.1, "unit": "g/dL"},
    {"name": "Glucose", "value": 145, "unit": "mg/dL"},
]}).encode()


class TestWiredAPIOffline:
    def test_health_ok(self, client_no_llm):
        r = client_no_llm.get("/api/health")
        assert r.status_code == 200
        assert r.json()["version"] == "3.0.0"

    def test_analyze_runs_agent_pipeline_rule_based(self, client_no_llm):
        r = client_no_llm.post(
            "/api/analyze",
            files={"file": ("r.json", _SAMPLE_REPORT, "application/json")},
            data={"user_id": "t"},
        )
        assert r.status_code == 200
        analysis = r.json()["analysis"]
        assert {p["name"] for p in analysis["parameters"]} >= {"Hemoglobin", "Glucose"}
        reports = analysis["agent_reports"]
        assert {x["agent_name"] for x in reports} >= {
            "Diagnosis Agent", "Risk Agent", "Nutrition Agent",
        }
        assert all(x["status"] == "fallback" for x in reports)

    def test_chat_404_for_missing_report(self, client_no_llm):
        r = client_no_llm.post(
            "/api/chat", json={"report_id": "missing", "message": "hello there"}
        )
        assert r.status_code == 404

    def test_analyze_then_chat(self, client_no_llm):
        rid = client_no_llm.post(
            "/api/analyze",
            files={"file": ("r.json", _SAMPLE_REPORT, "application/json")},
            data={"user_id": "t"},
        ).json()["report_id"]
        r2 = client_no_llm.post(
            "/api/chat", json={"report_id": rid, "message": "what is abnormal?"}
        )
        assert r2.status_code == 200
        assert r2.json()["message"]


class TestApiKeyGuard:
    """When API_KEY is set (as in a locked-down deployment), /api/* needs the
    header but the platform health check must still pass."""

    @pytest.fixture
    def client(self, monkeypatch):
        from fastapi.testclient import TestClient
        from backend import config
        for var in ("GROQ_API_KEY", "GEMINI_API_KEY", "NVIDIA_API_KEY",
                    "SUPABASE_URL", "SUPABASE_KEY"):
            monkeypatch.setenv(var, "")
        monkeypatch.setenv("API_KEY", "s3cr3t")
        config.get_settings.cache_clear()
        import backend.main as m
        with TestClient(m.create_app()) as c:
            yield c
        config.get_settings.cache_clear()

    def test_health_is_public(self, client):
        assert client.get("/api/health").status_code == 200

    def test_protected_route_rejects_missing_key(self, client):
        assert client.get("/api/reports?user_id=x").status_code == 401

    def test_protected_route_accepts_correct_key(self, client):
        r = client.get("/api/reports?user_id=x", headers={"X-API-Key": "s3cr3t"})
        assert r.status_code == 200


@requires_groq
class TestWiredAPILive:
    def test_analyze_produces_llm_agent_output(self, client_live):
        r = client_live.post(
            "/api/analyze",
            files={"file": ("r.json", _SAMPLE_REPORT, "application/json")},
            data={"user_id": "t", "age": "45", "gender": "male"},
        )
        assert r.status_code == 200
        analysis = r.json()["analysis"]
        reports = {x["agent_name"]: x for x in analysis["agent_reports"]}
        # Diagnosis + Risk are Groq-backed and should succeed with a real key.
        assert reports["Diagnosis Agent"]["status"] == "success"
        assert reports["Risk Agent"]["status"] == "success"
        assert analysis["executive_summary"]
        assert analysis["agents_used"]

    def test_chat_returns_llm_answer(self, client_live):
        rid = client_live.post(
            "/api/analyze",
            files={"file": ("r.json", _SAMPLE_REPORT, "application/json")},
            data={"user_id": "t"},
        ).json()["report_id"]
        r2 = client_live.post(
            "/api/chat", json={"report_id": rid, "message": "Summarize my results in one line."}
        )
        assert r2.status_code == 200
        assert r2.json()["message"].strip() != ""
