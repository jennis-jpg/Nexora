"""Environmental / weather condition cards."""

from __future__ import annotations

from typing import Any

from components.kpi_cards import build_env_condition_cards, render_single_card
from components.status_card import render_section_title
import streamlit as st


def _weather_display(wind_speed_kn: float) -> tuple[str, str]:
    if wind_speed_kn >= 20:
        return "🌊", "Strong Winds"
    if wind_speed_kn >= 12:
        return "💨", "Moderate Winds"
    if wind_speed_kn >= 6:
        return "🌤️", "Light Winds"
    return "☀️", "Calm Conditions"


def render_weather_card(vessel: dict[str, Any]) -> None:
    wind_speed = float(vessel["wind_speed_kn"])
    weather_icon, weather_label = _weather_display(wind_speed)
    cards = build_env_condition_cards(vessel)
    weather_sub = (
        "Live · weather data"
        if "pred_latitude" in vessel
        else "Demo · run a prediction for live data"
    )

    st.markdown(
        f"""
        <div class="glass-card" style="margin-top:0;">
            {render_section_title.__doc__ and ""}
            <p class="section-title"><span>🌐</span> Environmental Conditions</p>
            <div class="env-weather-banner">
                <div class="env-weather-icon">{weather_icon}</div>
                <div class="env-weather-text">
                    <div class="env-weather-label">{weather_label}</div>
                    <div class="env-weather-sub">{weather_sub}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        render_single_card(cards[0])
        render_single_card(cards[2])
    with col2:
        render_single_card(cards[1])
        render_single_card(cards[3])
