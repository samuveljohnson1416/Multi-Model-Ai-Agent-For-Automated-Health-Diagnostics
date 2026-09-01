"""
Shared look-and-feel helpers.

Keeps the pages visually consistent and strips the default Streamlit
chrome (hamburger menu, "Deploy" button, footer) so the app reads as a
finished product rather than a dev preview.
"""

import re

# pyrefly: ignore [missing-import]
import streamlit as st

# Status → (label, text colour, background) for the parameter table and chips.
STATUS_STYLE = {
    "LOW":      ("Low",      "#8a5a00", "#fff3e0"),
    "HIGH":     ("High",     "#9a2222", "#fdecea"),
    "CRITICAL": ("Critical", "#ffffff", "#c62828"),
    "NORMAL":   ("Normal",   "#1b5e20", "#e8f5e9"),
    "BORDERLINE": ("Borderline", "#8a5a00", "#fff3e0"),
    "UNKNOWN":  ("Not rated", "#555555", "#eeeeee"),
}

RISK_LABEL = {
    "low": "Low",
    "medium": "Moderate",
    "high": "High",
    "critical": "Needs attention",
    "unknown": "Not rated",
}

_CSS = """
<style>
/* Strip dev-preview chrome */
#MainMenu, header [data-testid="stToolbar"], footer {visibility: hidden;}
[data-testid="stDecoration"] {display: none;}

/* Calmer, tighter layout */
.block-container {padding-top: 2.5rem; padding-bottom: 4rem; max-width: 60rem;}
h1 {font-weight: 650; letter-spacing: -0.01em;}
h2 {font-weight: 600; margin-top: 1.4rem;}
h3 {font-weight: 600; font-size: 1.05rem;}

/* Section rhythm */
[data-testid="stVerticalBlock"] {gap: 0.9rem;}

/* Chips */
.chip {display:inline-block; padding:2px 10px; border-radius:999px;
       font-size:0.8rem; font-weight:600; line-height:1.6;}

/* Quieter buttons */
.stButton button {border-radius: 8px; font-weight: 550;}
</style>
"""


def apply_chrome() -> None:
    """Inject the shared stylesheet. Call once per page, after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def chip(text: str, fg: str, bg: str) -> str:
    return f'<span class="chip" style="color:{fg};background:{bg}">{text}</span>'


def status_chip(status: str) -> str:
    label, fg, bg = STATUS_STYLE.get(status, STATUS_STYLE["UNKNOWN"])
    return chip(label, fg, bg)


def risk_label(level: str) -> str:
    return RISK_LABEL.get((level or "unknown").lower(), "Not rated")


_HEADING = re.compile(r"^(#{1,6})(\s+\S)", re.MULTILINE)


def rendered(markdown_text: str, shift: int = 3) -> str:
    """
    Prepare model-generated markdown for embedding inside a page section:
    push every heading down `shift` levels (so an LLM's `#`/`##` become
    small sub-headings, not page titles), capped at h6.
    """
    if not markdown_text:
        return ""

    def _demote(m: "re.Match") -> str:
        level = min(len(m.group(1)) + shift, 6)
        return "#" * level + m.group(2)

    return _HEADING.sub(_demote, markdown_text.strip())
