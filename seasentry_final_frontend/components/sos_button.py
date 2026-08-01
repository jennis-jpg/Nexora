"""Emergency SOS button for fishermen."""

from __future__ import annotations

import streamlit as st

from config.theme import COLORS


def render_sos_button(*, key: str = "sos_btn") -> bool:
    """Returns True if SOS was triggered this run."""
    st.markdown(
        f"""
        <style>
        div[data-testid="stButton"] button[data-testid="baseButton-{key}"] {{
            background: linear-gradient(135deg, {COLORS["red"]}, #b71c1c) !important;
            box-shadow: 0 4px 20px {COLORS["red"]}66 !important;
            font-size: 0.95rem !important;
            animation: sos-pulse 2s ease-in-out infinite;
        }}
        @keyframes sos-pulse {{
            0%, 100% {{ box-shadow: 0 0 0 0 {COLORS["red"]}44; }}
            50% {{ box-shadow: 0 0 20px 4px {COLORS["red"]}55; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    triggered = st.button("🆘  SOS — Send Distress Signal", use_container_width=True, key=key)

    if triggered:
        st.session_state.sos_active = True
        st.markdown(
            f"""
            <div class="glass-card glass-card--alert" style="margin-top:0.5rem;">
                <p class="section-title"><span>🚨</span> SOS Activated</p>
                <div class="alert-body">
                    Distress signal logged locally. In production this would alert the coastguard
                    with your current GPS position. Continue monitoring drift and adjust course immediately.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return triggered
