"""
components/sea_level_droplet.py
================================
Sea-water level droplet card — THREE fill states based on the predicted tier.

This is NOT water_level_card.py (boundary proximity / ETA — leave that unchanged).
This component shows ocean tide/swell height as a filled water-droplet SVG.

Tier mapping
------------
"high"   → droplet fully filled,        COLORS["red"],    "Sea Level High — Increased Risk"
"rising" → droplet filled to middle,    COLORS["orange"], "Sea Level Rising — Take Precaution"
"normal" → droplet filled to bottom,    COLORS["green"],  "Sea Level Normal"

Data source: GET /predict/sea-level/{boat_id}  →  {"tier", "level_m", "trend"}
"""

from __future__ import annotations

import streamlit as st

from config.theme import COLORS

# SVG viewBox "0 0 60 80".  Droplet body spans roughly y=4..y=68.
# fill_y is where the fill rect starts — lower y → more fill.
_FILL_Y: dict[str, int] = {
    "normal": 52,   # ≈25 % full  (bottom third)
    "rising": 33,   # ≈55 % full  (middle third)
    "high":   14,   # ≈85 % full  (fully filled)
}
_COLOR: dict[str, str] = {
    "normal": COLORS["green"],
    "rising": COLORS["orange"],
    "high":   COLORS["red"],
}
_LABEL: dict[str, str] = {
    "normal": "Sea Level Normal",
    "rising": "Sea Level Rising — Take Precaution",
    "high":   "Sea Level High — Increased Risk",
}
_GLOW: dict[str, str] = {
    "normal": "rgba(46,204,113,0.15)",
    "rising": "rgba(255,152,0,0.22)",
    "high":   "rgba(229,57,53,0.32)",
}
_TREND_ICON: dict[str, str] = {
    "rising":  "↑",
    "falling": "↓",
    "steady":  "→",
}


def render_sea_level_droplet(
    tier: str,
    level_m: float,
    trend: str,
    uid: str = "sld0",
) -> None:
    """Render the sea-water level droplet card.

    Parameters
    ----------
    tier:    "normal" | "rising" | "high"
    level_m: Predicted water level in metres.
    trend:   "rising" | "falling" | "steady"
    uid:     Unique suffix per page to prevent SVG clipPath id collisions.
    """
    s = tier if tier in _FILL_Y else "normal"
    color  = _COLOR[s]
    fill_y = _FILL_Y[s]
    wave_y = fill_y + 5
    label  = _LABEL[s]
    glow   = _GLOW[s]
    trend_icon = _TREND_ICON.get(trend, "→")

    # Flattened single-string HTML — no blank lines inside the f-string to
    # avoid Streamlit's raw-HTML blank-line rendering bug (same fix applied
    # in dashboard_cards.py and landing.py render helpers).
    html = (
        f'<div class="glass-card glass-card--accent" style="box-shadow:0 0 28px {glow}; text-align:center;">'
        f'<p class="section-title" style="justify-content:center;"><span>🌊</span> Sea Water Level</p>'
        f'<div style="display:flex;justify-content:center;margin:0.35rem 0 0.2rem;">'
        f'<svg viewBox="0 0 60 80" width="52" height="69" aria-label="Sea level: {s}">'
        f'<defs>'
        f'<clipPath id="sldrop-{uid}">'
        f'<path d="M30 4 C30 4 8 28 8 46 A22 22 0 0 0 52 46 C52 28 30 4 30 4 Z"/>'
        f'</clipPath>'
        f'</defs>'
        f'<path d="M30 4 C30 4 8 28 8 46 A22 22 0 0 0 52 46 C52 28 30 4 30 4 Z"'
        f' fill="rgba(255,255,255,0.06)" stroke="{color}" stroke-width="2.2"/>'
        f'<rect x="0" y="{fill_y}" width="60" height="80"'
        f' fill="{color}" fill-opacity="0.70" clip-path="url(#sldrop-{uid})"/>'
        f'<path d="M8 {wave_y} Q22 {wave_y - 4} 30 {wave_y} Q42 {wave_y + 4} 52 {wave_y}"'
        f' stroke="{color}" stroke-width="1.4" fill="none" opacity="0.9"'
        f' clip-path="url(#sldrop-{uid})"/>'
        f'</svg>'
        f'</div>'
        f'<div style="font-size:0.88rem;font-weight:700;color:{color};margin:0.3rem 0 0.15rem;">{label}</div>'
        f'<div class="metric-grid" style="margin-top:0.55rem;">'
        f'<div class="metric-tile">'
        f'<div class="metric-label">Level</div>'
        f'<div class="metric-value">{level_m:.2f}<span class="metric-unit"> m</span></div>'
        f'</div>'
        f'<div class="metric-tile">'
        f'<div class="metric-label">Trend</div>'
        f'<div class="metric-value" style="color:{color};">{trend_icon} {trend.title()}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
