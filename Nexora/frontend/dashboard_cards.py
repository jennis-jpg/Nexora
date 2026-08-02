"""Reusable glassmorphism dashboard KPI cards (placeholder data, no backend)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from controls import COLORS, RISK_STYLES

DASHBOARD_CARD_CSS = f"""
        /* ── Reusable dashboard KPI cards ─────────────────────────────── */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}

        .kpi-card {{
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.13);
            border-radius: 16px;
            padding: 1rem 1.15rem;
            display: flex;
            align-items: center;
            gap: 0.85rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.22);
            transition:
                transform 0.28s cubic-bezier(0.22, 1, 0.36, 1),
                box-shadow 0.28s ease,
                border-color 0.28s ease;
            animation: fade-slide-up 0.5s ease-out both;
            cursor: default;
        }}

        .kpi-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.38);
            border-color: rgba(255, 255, 255, 0.22);
        }}

        .kpi-card:hover .kpi-icon-wrap {{
            transform: scale(1.1);
        }}

        .kpi-card--risk-low {{
            border-color: {COLORS["green"]}55;
            box-shadow: 0 4px 20px {COLORS["green"]}18;
        }}

        .kpi-card--risk-low:hover {{
            box-shadow: 0 12px 32px {COLORS["green"]}28;
            border-color: {COLORS["green"]}77;
        }}

        .kpi-card--risk-medium {{
            border-color: {COLORS["orange"]}55;
            box-shadow: 0 4px 20px {COLORS["orange"]}18;
        }}

        .kpi-card--risk-medium:hover {{
            box-shadow: 0 12px 32px {COLORS["orange"]}28;
            border-color: {COLORS["orange"]}77;
        }}

        .kpi-card--risk-high {{
            border-color: {COLORS["red"]}55;
            box-shadow: 0 4px 20px {COLORS["red"]}22;
        }}

        .kpi-card--risk-high:hover {{
            box-shadow: 0 12px 32px {COLORS["red"]}35;
            border-color: {COLORS["red"]}77;
        }}

        .kpi-icon-wrap {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            flex-shrink: 0;
            transition: transform 0.28s cubic-bezier(0.22, 1, 0.36, 1);
        }}

        .kpi-text {{
            min-width: 0;
        }}

        .kpi-label {{
            font-size: 0.66rem;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.52);
            margin-bottom: 0.18rem;
            white-space: nowrap;
        }}

        .kpi-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--white);
            line-height: 1.1;
            white-space: nowrap;
        }}

        .kpi-value-animated {{
            display: inline-block;
            animation: kpi-value-in 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
        }}

        @keyframes kpi-value-in {{
            0% {{
                opacity: 0;
                transform: translateY(10px);
                filter: blur(4px);
            }}
            60% {{
                opacity: 1;
                transform: translateY(-2px);
                filter: blur(0);
            }}
            100% {{
                opacity: 1;
                transform: translateY(0);
                filter: blur(0);
            }}
        }}

        .kpi-unit {{
            font-size: 0.72rem;
            color: rgba(255, 255, 255, 0.42);
            margin-left: 0.2rem;
        }}

        .kpi-sub {{
            font-size: 0.68rem;
            color: rgba(255, 255, 255, 0.45);
            margin-top: 0.1rem;
        }}

        @media (max-width: 1100px) {{
            .kpi-row {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}

        @media (max-width: 720px) {{
            .kpi-row {{
                grid-template-columns: 1fr 1fr;
            }}
        }}

        /* ── Environmental conditions panel (reusable cards) ──────────── */
        .env-weather-banner {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-top: 0.5rem;
            padding: 0.85rem 1rem;
            background: rgba(0, 0, 0, 0.22);
            border: 1px solid rgba(77, 182, 255, 0.22);
            border-radius: 14px;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }}

        .env-weather-banner:hover {{
            border-color: rgba(77, 182, 255, 0.4);
            box-shadow: 0 4px 18px rgba(77, 182, 255, 0.12);
        }}

        .env-weather-icon {{
            width: 52px;
            height: 52px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            flex-shrink: 0;
            background: linear-gradient(135deg, {COLORS["sky"]}33, {COLORS["ocean"]}44);
            animation: env-weather-pulse 3s ease-in-out infinite;
        }}

        @keyframes env-weather-pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.06); }}
        }}

        .env-weather-text {{
            min-width: 0;
        }}

        .env-weather-label {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--white);
            line-height: 1.2;
        }}

        .env-weather-sub {{
            font-size: 0.65rem;
            color: rgba(255, 255, 255, 0.42);
            margin-top: 0.15rem;
            letter-spacing: 0.04em;
        }}

        .env-card-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.55rem;
            margin-top: 0.65rem;
        }}

        .env-card-grid .kpi-card {{
            padding: 0.8rem 0.75rem;
            gap: 0.65rem;
        }}

        .env-card-grid .kpi-icon-wrap {{
            width: 38px;
            height: 38px;
            font-size: 1.1rem;
            border-radius: 10px;
        }}

        .env-card-grid .kpi-value {{
            font-size: 1.1rem;
        }}

        .env-card-grid .kpi-label {{
            font-size: 0.6rem;
        }}

        @media (max-width: 720px) {{
            .env-card-grid {{
                grid-template-columns: 1fr;
            }}
        }}
"""

ALERT_PANEL_CSS = f"""
        /* ── Alert panel (reusable cards + risk-tier animations) ──────── */
        .alert-panel {{
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}

        .alert-panel--high {{
            border-color: {COLORS["red"]}88;
            animation: alert-glow-red 2s ease-in-out infinite;
        }}

        @keyframes alert-glow-red {{
            0%, 100% {{
                box-shadow:
                    0 0 10px 2px {COLORS["red"]}44,
                    0 4px 24px rgba(0, 0, 0, 0.25);
                border-color: {COLORS["red"]}66;
            }}
            50% {{
                box-shadow:
                    0 0 32px 10px {COLORS["red"]}66,
                    0 4px 24px rgba(0, 0, 0, 0.25);
                border-color: {COLORS["red"]}cc;
            }}
        }}

        .alert-panel--high .alert-warning-icon {{
            animation: alert-icon-flash 1.1s ease-in-out infinite;
        }}

        @keyframes alert-icon-flash {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.3; transform: scale(1.18); }}
        }}

        .alert-panel--medium {{
            border-color: {COLORS["orange"]}77;
            animation: alert-pulse-orange 2.5s ease-in-out infinite;
        }}

        @keyframes alert-pulse-orange {{
            0%, 100% {{
                box-shadow: 0 0 0 0 {COLORS["orange"]}22;
                border-color: {COLORS["orange"]}55;
            }}
            50% {{
                box-shadow: 0 0 22px 5px {COLORS["orange"]}44;
                border-color: {COLORS["orange"]}99;
            }}
        }}

        .alert-panel--low {{
            border-color: {COLORS["green"]}77;
            box-shadow:
                0 4px 24px {COLORS["green"]}18,
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }}

        .alert-risk-strip {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            margin-bottom: 0.85rem;
        }}

        .alert-risk-strip-icon {{
            font-size: 1.55rem;
            flex-shrink: 0;
        }}

        .alert-risk-strip-label {{
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: rgba(255, 255, 255, 0.52);
        }}

        .alert-risk-strip-value {{
            font-size: 1.15rem;
            font-weight: 700;
            line-height: 1.2;
        }}

        .alert-message-block {{
            margin-bottom: 0.85rem;
            padding: 0.85rem 1rem;
            background: rgba(0, 0, 0, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
        }}

        .alert-message-label {{
            font-size: 0.68rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            color: rgba(255, 255, 255, 0.52);
            margin-bottom: 0.4rem;
        }}

        .alert-voice-status {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-top: 0.75rem;
            padding: 0.75rem 1rem;
            background: rgba(0, 0, 0, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
        }}

        .alert-voice-icon {{
            font-size: 1.25rem;
            opacity: 0.55;
        }}

        .alert-voice-label {{
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: rgba(255, 255, 255, 0.45);
        }}

        .alert-voice-value {{
            font-size: 0.82rem;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.72);
            font-family: 'JetBrains Mono', monospace;
        }}
"""


@dataclass(frozen=True)
class DashboardCard:
    """Configuration for a single dashboard KPI card."""

    icon: str
    title: str
    value: str
    subtitle: str
    unit: str = ""
    icon_bg: str = ""
    value_color: str = ""
    accent_color: str = ""
    animation_delay: str = "0s"
    risk_tier: str = ""  # "low" | "medium" | "high"


def _risk_tier_for_level(risk_level: str) -> str:
    """Map vessel risk level to card accent tier."""
    level = risk_level.upper()
    if level == "LOW":
        return "low"
    if level in ("HIGH", "CRITICAL"):
        return "high"
    return "medium"


def render_dashboard_card_html(card: DashboardCard) -> str:
    """Render HTML for one reusable dashboard card."""
    extra_style = f"animation-delay:{card.animation_delay};"
    if card.accent_color:
        extra_style += f" border-color: {card.accent_color}55; box-shadow: 0 4px 20px {card.accent_color}22;"

    risk_class = f" kpi-card--risk-{card.risk_tier}" if card.risk_tier else ""
    value_style = f' style="color: {card.value_color};"' if card.value_color else ""
    unit_html = f'<span class="kpi-unit">{card.unit}</span>' if card.unit else ""

    return (
        f'<div class="kpi-card{risk_class}" style="{extra_style}">'
        f'<div class="kpi-icon-wrap" style="background: {card.icon_bg};">{card.icon}</div>'
        '<div class="kpi-text">'
        f'<div class="kpi-label">{card.title}</div>'
        f'<div class="kpi-value"{value_style}>'
        f'<span class="kpi-value-animated" style="animation-delay: {card.animation_delay};">{card.value}</span>'
        f"{unit_html}"
        "</div>"
        f'<div class="kpi-sub">{card.subtitle}</div>'
        "</div>"
        "</div>"
    )


def render_single_card(card: DashboardCard) -> None:
    """Safely render a single DashboardCard into Streamlit."""
    st.markdown(render_dashboard_card_html(card), unsafe_allow_html=True)


def build_vessel_kpi_cards(vessel: dict[str, Any]) -> list[DashboardCard]:
    """Build the four top-row KPI cards from placeholder vessel data."""
    risk = RISK_STYLES.get(vessel["risk_level"], RISK_STYLES["MEDIUM"])
    risk_tier = _risk_tier_for_level(vessel["risk_level"])

    return [
        DashboardCard(
            icon="📍",
            title="Current Position",
            value=f'{abs(vessel["latitude"]):.4f}°',
            unit="N" if vessel["latitude"] >= 0 else "S",
            subtitle=f'{abs(vessel["longitude"]):.4f}° {"E" if vessel["longitude"] >= 0 else "W"}',
            icon_bg=f"linear-gradient(135deg, {COLORS['ocean']}55, {COLORS['teal']}44)",
            animation_delay="0.04s",
        ),
        DashboardCard(
            icon="⚓",
            title="Distance to Border",
            value=f'{vessel["distance_to_boundary_nm"]:.1f}',
            unit="nm",
            subtitle="Nearest EEZ boundary",
            icon_bg=f"linear-gradient(135deg, {COLORS['sky']}44, {COLORS['ocean']}44)",
            animation_delay="0.09s",
        ),
        DashboardCard(
            icon="⏱",
            title="Estimated Time to Crossing",
            value=str(round(vessel["eta_to_boundary_min"])),
            unit="min",
            subtitle="At current drift rate",
            icon_bg=f"linear-gradient(135deg, {COLORS['orange']}44, {COLORS['red']}33)",
            animation_delay="0.14s",
        ),
        DashboardCard(
            icon=risk["icon"],
            title="Risk Level",
            value=risk["label"],
            subtitle=f'Tier: {vessel["risk_level"]}',
            icon_bg=f"{risk['color']}33",
            value_color=risk["color"],
            accent_color=risk["color"],
            animation_delay="0.19s",
            risk_tier=risk_tier,
        ),
    ]


def render_dashboard_card_row(cards: list[DashboardCard]) -> None:
    """Render a row of reusable dashboard cards."""
    cards_html = "".join(render_dashboard_card_html(card) for card in cards)
    st.markdown(f'<div class="kpi-row">{cards_html}</div>', unsafe_allow_html=True)


def _cardinal_label(degrees: float) -> str:
    """Convert bearing to 8-point compass label."""
    cardinals = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return cardinals[round(degrees / 45) % 8]


def _weather_display(wind_speed_kn: float) -> tuple[str, str]:
    """Placeholder weather icon and label."""
    if wind_speed_kn >= 20:
        return "🌊", "Strong Winds"
    if wind_speed_kn >= 12:
        return "💨", "Moderate Winds"
    if wind_speed_kn >= 6:
        return "🌤️", "Light Winds"
    return "☀️", "Calm Conditions"


def build_env_condition_cards(vessel: dict[str, Any]) -> list[DashboardCard]:
    """Build environmental condition cards from vessel data (demo or live)."""
    wind_dir = int(vessel["wind_direction_deg"])
    current_dir = int(vessel["current_direction_deg"])
    is_live = "pred_latitude" in vessel
    wind_subtitle = "Surface wind · live" if is_live else "Surface wind · demo"
    current_subtitle = "Surface current · live" if is_live else "Surface current · demo"

    return [
        DashboardCard(
            icon="💨",
            title="Wind Speed",
            value=f'{vessel["wind_speed_kn"]:.1f}',
            unit="kn",
            subtitle=wind_subtitle,
            icon_bg=f"linear-gradient(135deg, {COLORS['sky']}44, {COLORS['ocean']}44)",
            animation_delay="0.05s",
        ),
        DashboardCard(
            icon="🧭",
            title="Wind Direction",
            value=f"{wind_dir}°",
            subtitle=f"From {_cardinal_label(wind_dir)}",
            icon_bg=f"linear-gradient(135deg, {COLORS['green']}33, {COLORS['teal']}33)",
            animation_delay="0.10s",
        ),
        DashboardCard(
            icon="🌊",
            title="Ocean Current Speed",
            value=f'{vessel["current_speed_kn"]:.1f}',
            unit="kn",
            subtitle=current_subtitle,
            icon_bg=f"linear-gradient(135deg, {COLORS['ocean']}55, {COLORS['teal']}44)",
            animation_delay="0.15s",
        ),
        DashboardCard(
            icon="↗️",
            title="Ocean Current Direction",
            value=f"{current_dir}°",
            subtitle=f"Flow toward {_cardinal_label(current_dir)}",
            icon_bg=f"linear-gradient(135deg, {COLORS['teal']}44, {COLORS['sky']}33)",
            animation_delay="0.20s",
        ),
    ]


def render_env_conditions_panel(vessel: dict[str, Any]) -> None:
    """Environmental Conditions panel — weather icon + reusable metric cards."""
    wind_speed = float(vessel["wind_speed_kn"])
    weather_icon, weather_label = _weather_display(wind_speed)
    cards = build_env_condition_cards(vessel)
    weather_sub = (
        "Live · weather_client.py"
        if "pred_latitude" in vessel
        else "Placeholder · run a prediction for live data"
    )

    st.markdown(
        f"""
        <div class="glass-card" style="margin-top:0;">
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


def render_vessel_kpi_row(vessel: dict[str, Any]) -> None:
    """Render the standard four-card vessel KPI dashboard row."""
    render_dashboard_card_row(build_vessel_kpi_cards(vessel))


def _alert_risk_tier(risk_level: str) -> str:
    """Map vessel risk level to alert panel animation tier."""
    level = risk_level.upper()
    if level in ("HIGH", "CRITICAL"):
        return "high"
    if level == "LOW":
        return "low"
    return "medium"


def build_alert_metric_cards(vessel: dict[str, Any]) -> list[DashboardCard]:
    """Build alert panel metric cards from placeholder vessel data."""
    safe_heading = int(vessel["safe_heading_deg"])

    return [
        DashboardCard(
            icon="📏",
            title="Distance Remaining",
            value=f'{vessel["distance_to_boundary_nm"]:.1f}',
            unit="nm",
            subtitle="To nearest EEZ boundary",
            icon_bg=f"linear-gradient(135deg, {COLORS['sky']}44, {COLORS['ocean']}44)",
            animation_delay="0.05s",
        ),
        DashboardCard(
            icon="⏱",
            title="Est. Time to Crossing",
            value=str(round(vessel["eta_to_boundary_min"])),
            unit="min",
            subtitle="At current drift rate",
            icon_bg=f"linear-gradient(135deg, {COLORS['orange']}44, {COLORS['red']}33)",
            animation_delay="0.10s",
        ),
        DashboardCard(
            icon="🧭",
            title="Safe Heading",
            value=f"{safe_heading}°",
            subtitle=f"Bearing {_cardinal_label(safe_heading)}",
            icon_bg=f"linear-gradient(135deg, {COLORS['green']}33, {COLORS['teal']}33)",
            animation_delay="0.15s",
        ),
        DashboardCard(
            icon="↪",
            title="Turn Direction",
            value=vessel["turn_direction"],
            subtitle="Recommended correction",
            icon_bg=f"linear-gradient(135deg, {COLORS['teal']}44, {COLORS['sky']}33)",
            animation_delay="0.20s",
        ),
    ]


def render_alert_panel_view(vessel: dict[str, Any]) -> None:
    """Alert Panel — risk tier animations, message, and reusable metric cards."""
    risk = RISK_STYLES.get(vessel["risk_level"], RISK_STYLES["MEDIUM"])
    tier = _alert_risk_tier(vessel["risk_level"])
    header_icon = "⚠" if tier in ("high", "medium") else "✓"
    cards = build_alert_metric_cards(vessel)
    voice_status = vessel.get("voice_alert_status", "Disabled · placeholder")

    st.markdown(
        f"""
        <div class="glass-card alert-panel alert-panel--{tier}">
            <p class="section-title"><span class="alert-warning-icon">{header_icon}</span> Alert Panel</p>
            <div class="alert-risk-strip" style="background: {risk['color']}22; border: 1px solid {risk['color']}55;">
                <span class="alert-risk-strip-icon alert-warning-icon">{risk["icon"]}</span>
                <div class="alert-risk-strip-text">
                    <div class="alert-risk-strip-label">Risk Level</div>
                    <div class="alert-risk-strip-value" style="color: {risk['color']};">{risk["label"]}</div>
                </div>
            </div>
            <div class="alert-message-block">
                <div class="alert-message-label">Alert Message</div>
                <div class="alert-body">{vessel["alert_message"]}</div>
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

    st.markdown(
        f"""
        <div class="alert-voice-status">
            <span class="alert-voice-icon">🔊</span>
            <div>
                <div class="alert-voice-label">Voice Alert Status</div>
                <div class="alert-voice-value">{voice_status}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )