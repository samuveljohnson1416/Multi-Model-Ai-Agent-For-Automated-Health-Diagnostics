"""
Agent review — internal diagnostic view.

Not linked from the navigation. Reach it at /agent-review.
Shows how the multi-agent pipeline handled the open report: the
orchestration order, what each agent produced, which provider answered,
how long it took, and which agents fell back or failed.

This is a developer aid, not an access-controlled page.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

import api_client
from session import init_session_state
from theme import apply_chrome, rendered

apply_chrome()
init_session_state()

st.title("Agent review")
st.caption("Internal view of the multi-agent pipeline. Not shown in the menu.")

# ── How the pipeline is wired ────────────────────────────────
with st.expander("How the agents are wired", expanded=False):
    st.markdown(
        """
**Orchestration** (`backend/agents/coordinator_agent.py`)

1. **Extraction agent** runs first, on its own — the others read its view of the
   parameters, so it can't run in parallel with them.
2. **Diagnosis, Risk and Nutrition agents** run together
   (`asyncio.gather(..., return_exceptions=True)`) so one failure can't cancel
   the others.
3. The coordinator **merges** the three results into a `CoordinatorResult` and
   builds a plain-language summary from the validated numbers (not from model text).

**How they talk to each other**

- Every agent receives the same `AgentContext` (parameters, abnormal subset, raw
  OCR text, patient context, rule-based risk + recommendations).
- Every agent returns the same `AgentResult`
  (`status` = success / fallback / error, `provider_used`, `content`,
  `execution_time_ms`, `error_message`).
- Agents never call each other. Only the coordinator sees all results.

**Providers** — each agent asks the `ProviderRegistry` for a preferred provider
(`groq` or `gemini`); if that one isn't configured it uses whatever is, and if a
call fails the agent runs its own rule-based fallback.
        """
    )

result = st.session_state.get("analysis_result")

# Reaching this page by typing the URL starts a fresh session with no report.
# Offer the recent runs the backend still has in memory.
if not result:
    recent = api_client.get_recent_reports()
    if recent:
        st.markdown("#### Pick a run to inspect")
        labels = {f"{r['name']}  ·  {r['at']}": r["id"] for r in recent}
        choice = st.selectbox("Recent analyses", list(labels), label_visibility="collapsed")
        if st.button("Load", type="primary"):
            full = api_client.get_report(labels[choice])
            if full:
                st.session_state.analysis_result = full.get("analysis")
                st.session_state.report_id = labels[choice]
                st.session_state.report_name = choice.split("  ·  ")[0]
                st.rerun()
            else:
                st.error("Couldn't load that run.")
    else:
        st.info("No analyses in memory yet. Run one from the New analysis page.")
        if st.button("Go to New analysis"):
            st.switch_page("pages/upload.py")
    st.stop()

reports = result.get("agent_reports", [])
agents_used = result.get("agents_used", [])
exec_summary = result.get("executive_summary")

# ── Run summary ─────────────────────────────────────────────
st.markdown(f"#### Last run — {st.session_state.get('report_name', 'report')}")

by_status = {"success": 0, "fallback": 0, "error": 0}
for r in reports:
    by_status[r.get("status", "error")] = by_status.get(r.get("status", "error"), 0) + 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("Agents", len(reports))
c2.metric("LLM answered", by_status["success"])
c3.metric("Fell back to rules", by_status["fallback"])
c4.metric("Errored", by_status["error"])

if agents_used:
    st.caption("Models used: " + ", ".join(agents_used))
if exec_summary:
    st.caption(f"Merged summary: {exec_summary}")

st.divider()

# ── Per-agent detail ────────────────────────────────────────
_ORDER = {"Extraction Agent": 0, "Diagnosis Agent": 1, "Risk Agent": 2, "Nutrition Agent": 3}
_BADGE = {
    "success": (":green[LLM]", "answered by the model"),
    "fallback": (":orange[fallback]", "model unavailable or failed — used rule-based logic"),
    "error": (":red[error]", "agent raised and produced nothing usable"),
}

for r in sorted(reports, key=lambda x: _ORDER.get(x.get("agent_name"), 9)):
    name = r.get("agent_name", "Agent")
    status = r.get("status", "error")
    badge, meaning = _BADGE.get(status, (status, ""))
    provider = r.get("provider_used", "—")
    ms = r.get("execution_time_ms", 0)

    with st.container(border=True):
        st.markdown(f"**{name}**  ·  {badge}  ·  `{provider}`  ·  {ms} ms")
        st.caption(meaning)

        if r.get("error_message"):
            st.code(r["error_message"], language="text")

        content = r.get("content", "")
        if content:
            with st.expander("Output"):
                st.markdown(rendered(content))

        structured = r.get("structured_data")
        if structured:
            with st.expander("Structured data"):
                st.json(structured)

st.divider()
st.caption(
    "Timing note: extraction is sequential; diagnosis / risk / nutrition overlap, "
    "so wall-clock time ≈ extraction + the slowest of the other three."
)
