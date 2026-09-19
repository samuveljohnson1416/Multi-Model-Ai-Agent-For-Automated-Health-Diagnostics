"""
Shared look-and-feel for the Streamlit UI.

Design plan
-----------
Subject   Reading a blood test report. Audience: people holding a lab printout,
          PDF or phone photo, not clinicians; some older or low-vision. Job: see
          which values sit outside their range, and what to ask a doctor.

Colour    Paper white #FFFFFF, chart grey #EEF3F4 (sidebar, panels), ink #1C2B33,
          analyzer teal #0B5D68 (actions), flag red #B3261E (high), flag blue
          #1F4FA3 (low). Red-for-high and blue-for-low is how printed lab reports
          ink their flags, so the UI reads like the document it explains.
Type      Atkinson Hyperlegible (Braille Institute; built for low-vision readers),
          400 and 700, self-hosted in static/fonts. One family; hierarchy comes
          from size and weight. Prose is capped near 68 characters per line.
Layout    Left-aligned single column. The memorable element is the reference-range
          strip: each flagged value is drawn as a marker on its own normal range,
          the way an analyzer plots it. Everything else stays quiet.
Rules     Status is never colour alone (a word and the marker position say it too).
          No all-caps labels, eyebrows, gradient washes or repeated identical
          cards. Visible keyboard focus; motion off when the user asks for less.

Reviewed against the usual generated-UI defaults (cream + serif + terracotta,
near-black + acid accent, SaaS card kit, tracked caps eyebrows). Changes made in
review: "low" moved from amber to blue to match printed lab flags; the deviation
bar chart became range strips; the History cards became divided rows.
"""

import html
import re

# pyrefly: ignore [missing-import]
import streamlit as st

# Status -> (label, text colour, background). Contrast is at least 5.5:1 for each pair.
STATUS_STYLE = {
    "LOW":        ("Low",        "#1F4FA3", "#E8EEF9"),
    "HIGH":       ("High",       "#B3261E", "#FBEAE8"),
    "CRITICAL":   ("Critical",   "#FFFFFF", "#8E1B14"),
    "NORMAL":     ("Normal",     "#1E6B3A", "#E6F2EA"),
    "BORDERLINE": ("Borderline", "#7A5200", "#FFF4DC"),
    "UNKNOWN":    ("Not rated",  "#4A5560", "#EDF0F2"),
}

RISK_LABEL = {
    "low": "Low",
    "medium": "Moderate",
    "high": "High",
    "critical": "Needs attention",
    "unknown": "Not rated",
}

# Overall-assessment chip colours (same palette as STATUS_STYLE).
RISK_STYLE = {
    "low": STATUS_STYLE["NORMAL"][1:],
    "medium": STATUS_STYLE["BORDERLINE"][1:],
    "high": STATUS_STYLE["HIGH"][1:],
    "critical": STATUS_STYLE["CRITICAL"][1:],
}

_CSS = """
<style>
/* Strip dev-preview chrome */
#MainMenu, header [data-testid="stToolbar"], footer {visibility: hidden;}
[data-testid="stDecoration"] {display: none;}

/* Keep the internal /agent-review page out of the menu */
[data-testid="stSidebarNav"] a[href$="/agent-review"] {display: none;}

/* Layout: one calm column; prose stays near 68 characters per line */
.block-container {padding-top: 2.5rem; padding-bottom: 4rem; max-width: 56rem;}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {max-width: 68ch; line-height: 1.6;}
[data-testid="stVerticalBlock"] {gap: 0.9rem;}

/* Type scale (Atkinson Hyperlegible is set in .streamlit/config.toml) */
html {font-size: 17px;}
h1 {font-size: 2rem; font-weight: 700; line-height: 1.2;}
h2 {font-size: 1.4rem; font-weight: 700; margin-top: 1.4rem;}
h3 {font-size: 1.15rem; font-weight: 700;}

/* Visible keyboard focus everywhere */
a:focus-visible, button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="button"]:focus-visible, [tabindex]:focus-visible {
    outline: 3px solid #0B5D68 !important; outline-offset: 2px !important;
}

/* Respect a request for less motion */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {animation: none !important; transition: none !important;}
}

/* Status chips */
.chip {display: inline-block; padding: 1px 10px; border-radius: 4px;
       font-size: 0.85rem; font-weight: 700; line-height: 1.6;}

.stButton button {border-radius: 6px; font-weight: 700;}

/* Reference-range strips */
.rng {display: grid; grid-template-columns: minmax(6rem, 11rem) minmax(9rem, 13rem) 1fr;
      gap: 0.4rem 1.2rem; align-items: center; padding: 0.7rem 0;
      border-bottom: 1px solid #D5DEE1;}
.rng:first-child {border-top: 1px solid #D5DEE1;}
.rng-name {font-weight: 700;}
.rng-val {font-variant-numeric: tabular-nums;}
.rng-val .chip {margin-left: 0.5rem;}
.rng-strip {position: relative; height: 0.9rem; background: #EEF3F4; border-radius: 2px;}
.rng-band {position: absolute; top: 0; bottom: 0; background: #C9DDE1;}
.rng-mark {position: absolute; top: -0.25rem; bottom: -0.25rem; width: 5px;
           margin-left: -2px; border-radius: 1px;}
.rng-ref {grid-column: 3; font-size: 0.85rem; color: #4A5560;
          font-variant-numeric: tabular-nums;}
@media (max-width: 640px) {
    h1 {font-size: 1.5rem;}
    .rng {grid-template-columns: 1fr;}
    .rng-ref {grid-column: 1;}
}
</style>
"""


def apply_chrome() -> None:
    """Inject the shared stylesheet. Call once per page, after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def chip(text: str, fg: str, bg: str) -> str:
    return f'<span class="chip" style="color:{fg};background:{bg}">{html.escape(text)}</span>'


def status_chip(status: str) -> str:
    label, fg, bg = STATUS_STYLE.get(status, STATUS_STYLE["UNKNOWN"])
    return chip(label, fg, bg)


def risk_label(level: str) -> str:
    return RISK_LABEL.get((level or "unknown").lower(), "Not rated")


def risk_chip(level: str) -> str:
    fg, bg = RISK_STYLE.get((level or "unknown").lower(), STATUS_STYLE["UNKNOWN"][1:])
    return chip(risk_label(level), fg, bg)


def _num(v) -> str:
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return str(v)


def range_strips(params: list) -> str:
    """
    HTML for one reference-range strip per parameter: the normal range is a band and
    the value is a marker, drawn on a scale that extends one range-width past each
    end. A value beyond the scale pins to the edge. Text carries the same facts, so
    nothing depends on colour or on seeing the strip.

    Names, units and values come from an uploaded document, so everything is escaped.
    """
    rows = []
    for p in params:
        name, unit = html.escape(str(p.get("name", ""))), html.escape(str(p.get("unit") or ""))
        status = p.get("status", "UNKNOWN")
        label, fg, bg = STATUS_STYLE.get(status, STATUS_STYLE["UNKNOWN"])
        lo, hi, value = p.get("reference_min"), p.get("reference_max"), p.get("value")

        strip, ref_text, aria = "", "No reference range on this report", ""
        try:
            lo, hi, value = float(lo), float(hi), float(value)
            span = hi - lo
            if span <= 0:
                raise ValueError
            start, end = lo - span, hi + span  # normal range = the middle third
            pos = min(max((value - start) / (end - start), 0.02), 0.98) * 100
            band_left, band_w = (lo - start) / (end - start) * 100, span / (end - start) * 100
            strip = (
                '<div class="rng-strip">'
                f'<div class="rng-band" style="left:{band_left:.1f}%;width:{band_w:.1f}%"></div>'
                f'<div class="rng-mark" style="left:{pos:.1f}%;background:{fg if status != "CRITICAL" else bg}"></div>'
                "</div>"
            )
            ref_text = f"Normal range {_num(lo)} to {_num(hi)} {unit}".strip()
            aria = f'role="img" aria-label="{name} {_num(value)} {unit}, {label.lower()}. {ref_text}"'
        except (TypeError, ValueError):
            pass

        rows.append(
            f'<div class="rng" {aria}>'
            f'<div class="rng-name">{name}</div>'
            f'<div class="rng-val"><strong>{html.escape(_num(p.get("value")))}</strong> {unit}'
            f'{chip(label, fg, bg)}</div>'
            f"{strip}"
            f'<div class="rng-ref">{ref_text}</div>'
            "</div>"
        )
    return "".join(rows)


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
