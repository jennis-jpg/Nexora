"""Risk classification badge component."""

from __future__ import annotations

import streamlit as st

from config.theme import RISK_STYLES


def render_risk_badge(risk_level: str, *, compact: bool = False) -> None:
    risk = RISK_STYLES.get(risk_level.upper(), RISK_STYLES["MEDIUM"])
    bg = f"background: {risk['color']}22; border: 1px solid {risk['color']}55;"
    if compact:
        st.markdown(
            f"""
            <span class="status-pill" style="background:{risk['color']}22;border-color:{risk['color']}55;color:{risk['color']};">
                {risk["icon"]} {risk["label"]}
            </span>
            """,
            unsafe_allow_html=True,
        )
        return
    st.markdown(
        f"""
        <div class="risk-badge" style="{bg}">
            <span class="risk-icon">{risk["icon"]}</span>
            <div>
                <div class="risk-label">Risk Classification</div>
                <div class="risk-level" style="color: {risk['color']};">{risk["label"]}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_tier(risk_level: str) -> str:
    level = risk_level.upper()
    if level in ("HIGH", "CRITICAL"):
        return "high"
    if level == "LOW":
        return "low"
    return "medium"
