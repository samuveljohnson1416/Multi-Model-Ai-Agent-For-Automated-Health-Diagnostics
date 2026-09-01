"""
Agent Insights Page — per-agent reasoning from the multi-agent analysis.

Shows the raw output of each specialist agent (Extraction, Diagnosis,
Risk, Nutrition) plus which provider/model produced it and how long it took.
"""

# pyrefly: ignore [missing-import]
import streamlit as st

from session import init_session_state

init_session_state()

st.header("🧠 Agent Insights")

result = st.session_state.get("analysis_result")
if not result:
    st.info("No analysis loaded. Upload and analyze a report first.")
    st.stop()

agent_reports = result.get("agent_reports", [])
agents_used = result.get("agents_used", [])
executive_summary = result.get("executive_summary")

if not agent_reports:
    st.warning(
        "This report has no multi-agent analysis. It may have been produced "
        "before the agent pipeline was enabled, or no LLM provider was configured."
    )
    st.stop()

# ── Overview ──────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.metric("Agents run", len(agent_reports))
with col2:
    llm_count = sum(1 for r in agent_reports if r.get("status") == "success")
    st.metric("LLM-powered", f"{llm_count}/{len(agent_reports)}")

if agents_used:
    st.caption("Models used: " + ", ".join(agents_used))

if executive_summary:
    st.markdown("### Executive Summary")
    st.markdown(executive_summary)

st.divider()

# ── Per-agent detail ──────────────────────────────────────────
_STATUS_BADGE = {
    "success": "🟢 LLM",
    "fallback": "🟡 rule-based",
    "error": "🔴 error",
}

for report in agent_reports:
    name = report.get("agent_name", "Agent")
    status = report.get("status", "unknown")
    provider = report.get("provider_used", "unknown")
    elapsed = report.get("execution_time_ms", 0)

    with st.expander(f"{_STATUS_BADGE.get(status, status)} — {name}", expanded=(status == "success")):
        st.caption(f"Provider: `{provider}` · {elapsed} ms")
        if report.get("error_message"):
            st.error(report["error_message"])
        content = report.get("content", "")
        if content:
            st.markdown(content)
        structured = report.get("structured_data")
        if structured:
            st.json(structured)

st.divider()
st.caption(result.get("disclaimer", "For informational purposes only. Consult a healthcare provider."))
