"""Boundary proximity / safe-zone status card."""

from __future__ import annotations

from typing import Any

import streamlit as st

from config.theme import COLORS


def render_water_level_card(vessel: dict[str, Any]) -> None:
    """Shows distance-to-boundary and zone status — maritime 'safe water' indicator."""
    dist = float(vessel.get("distance_to_boundary_nm", 0))
    eta = vessel.get("eta_to_boundary_min", "—")
    crossed = vessel.get("already_crossed", False)
    in_waters = not crossed

    if crossed:
        zone_label = "Outside Indian Waters"
        zone_color = COLORS["red"]
        zone_icon = "🚨"
        bar_pct = 5
    elif dist <= 1.5:
        zone_label = "Critical Zone — Near Border"
        zone_color = COLORS["red"]
        zone_icon = "⚠"
        bar_pct = max(10, int((1.5 - dist) / 1.5 * 40) + 60)
    elif dist <= 5:
        zone_label = "Warning Zone"
        zone_color = COLORS["orange"]
        zone_icon = "⚡"
        bar_pct = int((5 - dist) / 5 * 40) + 30
    else:
        zone_label = "Safe Operating Zone"
        zone_color = COLORS["green"]
        zone_icon = "✓"
        bar_pct = min(30, int(dist / 10 * 30))

    st.markdown(
        f"""
        <div class="glass-card glass-card--accent">
            <p class="section-title"><span>🌊</span> Safe Water Status</p>
            <div style="display:flex; align-items:center; gap:0.85rem; margin-bottom:0.85rem;">
                <div style="font-size:1.75rem;">{zone_icon}</div>
                <div>
                    <div style="font-size:0.95rem; font-weight:600; color:{zone_color};">{zone_label}</div>
                    <div style="font-size:0.72rem; color:rgba(255,255,255,0.5); margin-top:0.15rem;">
                        {"Currently in Indian waters" if in_waters else "Vessel may have crossed boundary"}
                    </div>
                </div>
            </div>
            <div style="background:rgba(0,0,0,0.25); border-radius:8px; height:8px; overflow:hidden; margin-bottom:0.65rem;">
                <div style="width:{bar_pct}%; height:100%; background:linear-gradient(90deg,{zone_color},{COLORS['sky']}); border-radius:8px; transition:width 0.4s ease;"></div>
            </div>
            <div class="metric-grid">
                <div class="metric-tile">
                    <div class="metric-label">Distance to Border</div>
                    <div class="metric-value">{dist:.1f}<span class="metric-unit">nm</span></div>
                </div>
                <div class="metric-tile">
                    <div class="metric-label">ETA to Crossing</div>
                    <div class="metric-value">{eta}<span class="metric-unit">min</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
