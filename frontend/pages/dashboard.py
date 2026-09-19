"""Results — the analysed report."""

# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd

from session import init_session_state
from theme import apply_chrome, STATUS_STYLE, range_strips, risk_chip, rendered

apply_chrome()
init_session_state()

result = st.session_state.get("analysis_result")
if not result:
    st.title("Results")
    st.write("No report is open. Analyze a report to see its results here.")
    if st.button("Analyze a report", type="primary"):
        st.switch_page("pages/upload.py")
    st.stop()

parameters = result.get("parameters", [])
summary = result.get("summary", {})
risks = result.get("risks", {})
recommendations = result.get("recommendations", [])
diagnosis = result.get("diagnosis_insights") or result.get("llm_insights")
enhanced_risk = (result.get("enhanced_risk") or {}).get("content")
nutrition = result.get("nutrition_plan")

ABNORMAL = ("LOW", "HIGH", "CRITICAL", "BORDERLINE")
abnormal = [p for p in parameters if p.get("status") in ABNORMAL]
critical = [p for p in abnormal if p.get("status") == "CRITICAL"]

st.title(st.session_state.get("report_name") or "Results")

# ── Headline ─────────────────────────────────────────────────
total = summary.get("total_parameters", len(parameters))
n_abn = len(abnormal)
if n_abn == 0:
    headline = f"All {total} values are within their normal ranges."
else:
    headline = f"{n_abn} of {total} values fall outside the normal range."
    if critical:
        names = ", ".join(p["name"] for p in critical)
        headline += f" {len(critical)} of them {'is' if len(critical) == 1 else 'are'} well outside it: {names}."
st.subheader(headline)

level = (risks.get("risk_level") or "unknown").lower()
st.markdown(f"Overall assessment: {risk_chip(level)}", unsafe_allow_html=True)

framingham = risks.get("framingham_risk") or {}
if framingham.get("risk_percent") is not None:
    st.caption(
        f"Estimated 10-year risk of a heart-related event: "
        f"{framingham['risk_percent']}% (from age, sex, cholesterol and smoking status)."
    )

for w in result.get("warnings", []):
    st.warning(w)

st.divider()

# ── Values ───────────────────────────────────────────────────
_LABEL_STYLE = {lbl: (fg, bg) for (lbl, fg, bg) in STATUS_STYLE.values()}
_STATUS_ORDER = {"CRITICAL": 0, "HIGH": 1, "LOW": 2, "BORDERLINE": 3, "NORMAL": 5, "UNKNOWN": 4}


def _fmt(v):
    try:
        f = float(v)
        return f"{f:g}"
    except (TypeError, ValueError):
        return v


def _table(rows):
    rows = sorted(rows, key=lambda p: _STATUS_ORDER.get(p.get("status"), 9))
    df = pd.DataFrame(rows)
    cols = [c for c in ["name", "value", "unit", "status", "reference_range"] if c in df.columns]
    df = df[cols].rename(columns={
        "name": "Parameter", "value": "Value", "unit": "Unit",
        "status": "Status", "reference_range": "Reference range",
    })
    df["Value"] = df["Value"].map(_fmt)
    df["Status"] = df["Status"].map(lambda s: STATUS_STYLE.get(s, STATUS_STYLE["UNKNOWN"])[0])

    def _style(label):
        fg, bg = _LABEL_STYLE.get(label, ("#555", "#eee"))
        return f"background-color:{bg};color:{fg};font-weight:600"

    return df.style.map(_style, subset=["Status"])


if abnormal:
    st.markdown("#### Flagged values")

    st.markdown(range_strips(sorted(abnormal, key=lambda p: _STATUS_ORDER.get(p.get("status"), 9))),
                unsafe_allow_html=True)

    with st.expander(f"Show all {total} values"):
        st.dataframe(_table(parameters), use_container_width=True, hide_index=True)
else:
    st.dataframe(_table(parameters), use_container_width=True, hide_index=True)

st.divider()

# ── Interpretation ───────────────────────────────────────────
if diagnosis:
    st.markdown("#### What this means")
    st.markdown(rendered(diagnosis))

if enhanced_risk:
    with st.expander("Risk, by body system"):
        st.markdown(rendered(enhanced_risk))

if nutrition:
    with st.expander("Diet and lifestyle"):
        st.markdown(rendered(nutrition))

# ── Next steps ───────────────────────────────────────────────
# Drop the "Found N abnormal…" line — the headline already says it.
next_steps = [r for r in recommendations if not r.lower().startswith("found ")]
if next_steps:
    st.markdown("#### Suggested next steps")
    st.markdown("\n".join(f"- {r}" for r in next_steps))

c1, c2 = st.columns(2)
if c1.button("Ask a question about this report", use_container_width=True):
    st.switch_page("pages/chat.py")
if c2.button("Analyze another report", use_container_width=True):
    st.switch_page("pages/upload.py")

st.divider()
st.caption(result.get(
    "disclaimer",
    "Automated analysis for information only. Always confirm results and "
    "next steps with a healthcare provider.",
))
