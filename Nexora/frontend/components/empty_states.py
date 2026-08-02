"""Empty state placeholders."""

from __future__ import annotations

import streamlit as st


def render_empty_state(
    icon: str,
    title: str,
    message: str,
    hint: str = "",
) -> None:
    st.markdown(
        f"""
        <div class="glass-card" style="text-align:center; padding:2rem 1.5rem;">
            <div style="font-size:2.5rem; margin-bottom:0.75rem;">{icon}</div>
            <div style="font-size:1.05rem; font-weight:600; color:white; margin-bottom:0.45rem;">{title}</div>
            <div style="font-size:0.88rem; color:rgba(255,255,255,0.62); line-height:1.55; max-width:420px; margin:0 auto;">
                {message}
            </div>
            {"<div style='font-size:0.72rem; color:rgba(255,255,255,0.4); margin-top:0.85rem;'>" + hint + "</div>" if hint else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_fleet_empty() -> None:
    render_empty_state(
        icon="🛰️",
        title="No vessels tracked yet",
        message="Fleet data appears when fishermen run drift predictions. Ask vessels to submit a prediction first.",
        hint="Each /predict call registers a vessel in the fleet tracker.",
    )


def render_map_empty() -> None:
    render_empty_state(
        icon="🗺️",
        title="Map awaiting coordinates",
        message="Enter your boat position and run a drift prediction to see your location on the map.",
    )
