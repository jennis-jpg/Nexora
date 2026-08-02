"""
components/sea_level_indicator.py
===================================
Sea-water level indicator card for the Fisherman Dashboard.

Three fill levels rendered as an SVG water-droplet:
  normal  – green,  ~25 % fill
  rising  – orange, ~55 % fill
  high    – red,    ~85 % fill

NOTE: This is NOT water_level_card.py.  That component shows boundary
proximity / ETA.  This one shows ocean swell / tide height.
"""

from __future__ import annotations

import streamlit as st

# SVG viewBox "0 0 60 80".  The droplet body spans roughly y=4..y=68.
# fill_y is where the fill rect starts; lower y → more fill.
_FILL_Y = {
    "normal": 52,   # ≈25 % full
    "rising": 33,   # ≈55 % full
    "high":   14,   # ≈85 % full
}
_COLOR = {
    "normal": "#2ECC71",
    "rising": "#FF9800",
    "high":   "#E53935",
}
_LABEL = {
    "normal": "Normal",
    "rising": "Rising",
    "high":   "HIGH",
}
_GLOW = {
    "normal": "rgba(46,204,113,0.18)",
    "rising": "rgba(255,152,0,0.25)",
    "high":   "rgba(229,57,53,0.35)",
}


def render_sea_level_indicator(
    status: str,
    level_m: float,
    description: str,
    uid: str = "sl0",
) -> None:
    """Render the sea-water level indicator into the current Streamlit
    column / container.

    ``uid`` must be unique per page to avoid SVG clipPath id collisions
    when the card is rendered more than once (e.g. in simulation reruns).
    """
    s = status if status in _FILL_Y else "normal"
    color  = _COLOR[s]
    fill_y = _FILL_Y[s]
    wave_y = fill_y + 5
    label  = _LABEL[s]
    glow   = _GLOW[s]

    st.markdown(
        f"""
        <div class="fh-card fh-in" style="box-shadow: 0 0 28px {glow};">
            <div class="fh-card-icon">🌊</div>
            <div class="fh-card-label">Sea Water Level</div>
            <div style="display:flex; justify-content:center; margin:0.35rem 0 0.2rem;">
                <svg viewBox="0 0 60 80" width="52" height="69" aria-label="Sea level: {label}">
                    <defs>
                        <clipPath id="drop-{uid}">
                            <path d="M30 4 C30 4 8 28 8 46 A22 22 0 0 0 52 46 C52 28 30 4 30 4 Z"/>
                        </clipPath>
                    </defs>
                    <path d="M30 4 C30 4 8 28 8 46 A22 22 0 0 0 52 46 C52 28 30 4 30 4 Z"
                          fill="rgba(255,255,255,0.06)" stroke="{color}" stroke-width="2.2"/>
                    <rect x="0" y="{fill_y}" width="60" height="80"
                          fill="{color}" fill-opacity="0.70"
                          clip-path="url(#drop-{uid})"/>
                    <path d="M8 {wave_y} Q22 {wave_y - 4} 30 {wave_y} Q42 {wave_y + 4} 52 {wave_y}"
                          stroke="{color}" stroke-width="1.4" fill="none" opacity="0.9"
                          clip-path="url(#drop-{uid})"/>
                </svg>
            </div>
            <div class="fh-card-value" style="color:{color}; font-size:1.65rem;">{label}</div>
            <div class="fh-card-sub">{level_m:.1f} m · {description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
