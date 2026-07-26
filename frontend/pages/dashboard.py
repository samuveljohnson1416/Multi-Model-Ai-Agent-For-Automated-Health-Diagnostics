"""
Dashboard Page — analysis results visualization.
"""


# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go


st.header("📊 Analysis Dashboard")

# ── Check for data ────────────────────────────────────────────
if "analysis_result" not in st.session_state or not st.session_state["analysis_result"]:
    st.info("No analysis loaded. Please upload a report first.")
    st.stop()

result = st.session_state["analysis_result"]
parameters = result.get("parameters", [])
summary = result.get("summary", {})
risks = result.get("risks", {})
recommendations = result.get("recommendations", [])
llm_insights = result.get("llm_insights")

# ── Summary Metrics ───────────────────────────────────────────
st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Parameters", summary.get("total_parameters", len(parameters)))
with col2:
    st.metric("Normal", summary.get("normal", 0), delta_color="normal")
with col3:
    abnormal = summary.get("abnormal_count", 0)
    st.metric("Abnormal", abnormal, delta=-abnormal if abnormal else None, delta_color="inverse")
with col4:
    risk_level = risks.get("risk_level", "unknown").upper()
    st.metric("Risk Level", risk_level)

# ── Parameters Table ──────────────────────────────────────────
st.subheader("Blood Parameters")

if parameters:
    df = pd.DataFrame(parameters)
    display_cols = ["name", "value", "unit", "status", "reference_range", "severity"]
    available_cols = [c for c in display_cols if c in df.columns]
    df_display = df[available_cols].copy()

    # Color-code status
    def color_status(val):
        colors = {
            "LOW": "background-color: #FFE0B2",
            "HIGH": "background-color: #FFCDD2",
            "NORMAL": "background-color: #C8E6C9",
            "CRITICAL": "background-color: #EF5350; color: white",
            "UNKNOWN": "background-color: #E0E0E0",
        }
        return colors.get(val, "")

    if "status" in df_display.columns:
        styled = df_display.style.map(color_status, subset=["status"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    else:
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# ── Status Distribution Chart ─────────────────────────────────
    st.subheader("Parameter Distribution")
    col1, col2 = st.columns(2)

    with col1:
        if "status" in df.columns:
            status_counts = df["status"].value_counts()
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                color=status_counts.index,
                color_discrete_map={
                    "NORMAL": "#4CAF50",
                    "LOW": "#FF9800",
                    "HIGH": "#F44336",
                    "CRITICAL": "#B71C1C",
                    "UNKNOWN": "#9E9E9E",
                },
                title="Status Distribution",
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Bar chart of abnormal parameters
        abnormal_params = [p for p in parameters if p.get("status") in ("LOW", "HIGH", "CRITICAL")]
        if abnormal_params:
            abn_df = pd.DataFrame(abnormal_params)
            fig = px.bar(
                abn_df,
                x="name",
                y="deviation_percent",
                color="status",
                color_discrete_map={"LOW": "#FF9800", "HIGH": "#F44336", "CRITICAL": "#B71C1C"},
                title="Abnormal Parameters — Deviation %",
                labels={"deviation_percent": "Deviation (%)", "name": "Parameter"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("All parameters are within normal ranges! 🎉")

# ── Risk Assessment ───────────────────────────────────────────
if risks and risks.get("risk_factors"):
    st.subheader("Risk Assessment")

    risk_score = risks.get("risk_score", 0)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score * 100,
        title={"text": "Overall Risk Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#1976D2"},
            "steps": [
                {"range": [0, 20], "color": "#C8E6C9"},
                {"range": [20, 50], "color": "#FFF9C4"},
                {"range": [50, 80], "color": "#FFE0B2"},
                {"range": [80, 100], "color": "#FFCDD2"},
            ],
        },
    ))
    fig.update_layout(height=300)
    st.plotly_chart(fig, use_container_width=True)

    # Framingham risk
    framingham = risks.get("framingham_risk")
    if framingham and "risk_percent" in framingham:
        st.info(f"**Framingham 10-Year CVD Risk:** {framingham['risk_percent']}% ({framingham.get('risk_category', 'N/A')})")

# ── Warnings ──────────────────────────────────────────────────
warnings = result.get("warnings", [])
if warnings:
    for warning in warnings:
        st.warning(warning)

# ── LLM Insights ──────────────────────────────────────────────
if llm_insights:
    st.subheader("🤖 AI Insights")
    st.markdown(llm_insights)

# ── Recommendations ───────────────────────────────────────────
if recommendations:
    st.subheader("📋 Recommendations")
    for rec in recommendations:
        st.markdown(f"- {rec}")

# ── Disclaimer ────────────────────────────────────────────────
st.divider()
st.caption(result.get("disclaimer", "This is for informational purposes only."))
