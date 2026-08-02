"""SeaSentry dashboard controls, metrics, and themed UI components."""

from __future__ import annotations

from typing import Any

import streamlit as st

# ── Theme palette ──────────────────────────────────────────────────────────
COLORS = {
    "navy": "#031B34",
    "ocean": "#005B96",
    "sky": "#4DB6FF",
    "teal": "#00C2A8",
    "green": "#2ECC71",
    "orange": "#FF9800",
    "red": "#E53935",
    "white": "#FFFFFF",
}

RISK_STYLES = {
    "LOW": {"color": COLORS["green"], "label": "Low Risk", "icon": "✓"},
    "MEDIUM": {"color": COLORS["orange"], "label": "Medium Risk", "icon": "⚠"},
    "HIGH": {"color": COLORS["red"], "label": "High Risk", "icon": "⛔"},
    "CRITICAL": {"color": COLORS["red"], "label": "Critical", "icon": "🚨"},
}

# Demo state — replaced by backend responses when wired up.
DEMO_VESSEL: dict[str, Any] = {
    "latitude": 9.4823,
    "longitude": 79.3500,
    "heading_deg": 285,
    "speed_knots": 3.2,
    "risk_level": "HIGH",
    "distance_to_boundary_nm": 12.0,
    "eta_to_boundary_min": 45,
    "current_speed_kn": 1.8,
    "current_direction_deg": 312,
    "wind_speed_kn": 12.4,
    "wind_direction_deg": 278,
    "alert_message": (
        "Drift toward international waters detected. "
        "Adjust course starboard within 38 minutes."
    ),
    "safe_heading_deg": 15,
    "turn_direction": "Starboard",
    "voice_alert_status": "Disabled · placeholder",
}


def inject_theme_css() -> None:
    """Inject global glassmorphism maritime theme."""
    from dashboard_cards import ALERT_PANEL_CSS, DASHBOARD_CARD_CSS

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

        :root {{
            --navy: {COLORS["navy"]};
            --ocean: {COLORS["ocean"]};
            --sky: {COLORS["sky"]};
            --teal: {COLORS["teal"]};
            --green: {COLORS["green"]};
            --orange: {COLORS["orange"]};
            --red: {COLORS["red"]};
            --white: {COLORS["white"]};
        }}

        .stApp {{
            background:
                radial-gradient(ellipse 80% 50% at 20% -10%, rgba(77, 182, 255, 0.18) 0%, transparent 55%),
                radial-gradient(ellipse 60% 40% at 90% 100%, rgba(0, 194, 168, 0.12) 0%, transparent 50%),
                linear-gradient(160deg, #031B34 0%, #022847 35%, #005B96 70%, #031B34 100%);
            font-family: 'Inter', sans-serif;
            color: var(--white);
        }}

        #MainMenu, footer, header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0;
        }}

        .block-container {{
            padding-top: 1.25rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }}

        /* Glass cards */
        .glass-card {{
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 18px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 0.85rem;
            box-shadow:
                0 4px 24px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}

        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}

        .glass-card--accent {{
            border-color: rgba(77, 182, 255, 0.35);
            box-shadow:
                0 4px 24px rgba(0, 91, 150, 0.3),
                inset 0 1px 0 rgba(77, 182, 255, 0.12);
        }}

        .glass-card--alert {{
            border-color: rgba(229, 57, 53, 0.45);
            animation: pulse-alert 2.5s ease-in-out infinite;
        }}

        @keyframes pulse-alert {{
            0%, 100% {{ box-shadow: 0 0 0 0 rgba(229, 57, 53, 0.25); }}
            50% {{ box-shadow: 0 0 24px 4px rgba(229, 57, 53, 0.35); }}
        }}

        @keyframes fade-slide-up {{
            from {{ opacity: 0; transform: translateY(14px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .animate-in {{
            animation: fade-slide-up 0.55s ease-out both;
        }}

        .delay-1 {{ animation-delay: 0.05s; }}
        .delay-2 {{ animation-delay: 0.12s; }}
        .delay-3 {{ animation-delay: 0.2s; }}

        /* Brand header */
        .brand-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.65rem 1.25rem;
            margin-bottom: 1rem;
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        }}

        .brand-logo {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .brand-icon {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--ocean), var(--teal));
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            box-shadow: 0 4px 16px rgba(0, 194, 168, 0.35);
        }}

        .brand-title {{
            font-size: 1.55rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
            background: linear-gradient(90deg, var(--white), var(--sky));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-subtitle {{
            font-size: 0.78rem;
            font-weight: 400;
            color: rgba(255, 255, 255, 0.62);
            margin: 0;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }}

        .status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.4rem 0.9rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            background: rgba(0, 194, 168, 0.15);
            border: 1px solid rgba(0, 194, 168, 0.4);
            color: var(--teal);
        }}

        .status-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--teal);
            animation: blink 2s ease-in-out infinite;
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.35; }}
        }}

        /* Section headers */
        .section-title {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.55);
            margin: 0 0 0.75rem 0;
        }}

        .section-title span {{
            color: var(--sky);
        }}

        /* Metric tiles */
        .metric-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.65rem;
        }}

        .metric-tile {{
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 0.75rem 0.85rem;
            transition: border-color 0.2s ease;
        }}

        .metric-tile:hover {{
            border-color: rgba(77, 182, 255, 0.3);
        }}

        .metric-label {{
            font-size: 0.68rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 0.25rem;
        }}

        .metric-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.15rem;
            font-weight: 500;
            color: var(--white);
        }}

        .metric-unit {{
            font-size: 0.72rem;
            color: rgba(255, 255, 255, 0.45);
            margin-left: 0.15rem;
        }}

        /* Risk badge */
        .risk-badge {{
            display: flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.85rem 1rem;
            border-radius: 14px;
            margin-bottom: 0.85rem;
        }}

        .risk-icon {{
            font-size: 1.5rem;
        }}

        .risk-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            opacity: 0.75;
        }}

        .risk-level {{
            font-size: 1.1rem;
            font-weight: 700;
        }}

        /* Alert box */
        .alert-body {{
            font-size: 0.88rem;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.88);
        }}

        .alert-meta {{
            display: flex;
            gap: 1rem;
            margin-top: 0.75rem;
            font-size: 0.72rem;
            color: rgba(255, 255, 255, 0.5);
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Map panel chrome */
        .map-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.65rem;
        }}

        .map-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--white);
        }}

        .map-legend {{
            display: flex;
            gap: 0.85rem;
            flex-wrap: wrap;
            margin-top: 0.65rem;
            font-size: 0.68rem;
            color: rgba(255, 255, 255, 0.6);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .legend-swatch {{
            width: 10px;
            height: 10px;
            border-radius: 3px;
        }}

        /* Streamlit widget overrides */
        div[data-testid="stNumberInput"] label,
        div[data-testid="stSlider"] label {{
            color: rgba(255, 255, 255, 0.65) !important;
            font-size: 0.78rem !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        div[data-testid="stNumberInput"] input {{
            background: rgba(0, 0, 0, 0.25) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            color: var(--white) !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}

        div[data-testid="stSlider"] div[data-baseweb="slider"] {{
            padding-top: 0.5rem;
        }}

        .stButton > button {{
            width: 100%;
            background: linear-gradient(135deg, var(--ocean), var(--teal)) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.65rem 1rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.03em !important;
            box-shadow: 0 4px 16px rgba(0, 91, 150, 0.4) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 24px rgba(0, 194, 168, 0.45) !important;
        }}

        .stButton > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.18) !important;
            box-shadow: none !important;
        }}

        /* Footer */
        .dashboard-footer {{
            text-align: center;
            padding: 0.75rem;
            margin-top: 0.5rem;
            font-size: 0.68rem;
            color: rgba(255, 255, 255, 0.35);
            letter-spacing: 0.04em;
        }}

        /* Column panels — glass wrapper for Streamlit widgets */
        [data-testid="column"] > div {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 0.85rem 0.75rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.22);
            min-height: 100%;
        }}

        [data-testid="column"]:nth-child(2) > div {{
            border-color: rgba(77, 182, 255, 0.22);
            background: rgba(255, 255, 255, 0.04);
        }}

        /* ── Prediction controls panel ──────────────────────────────────── */
        .pred-controls-card {{
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-top: 0.75rem;
        }}

        .pred-btn-row {{
            display: flex;
            gap: 0.65rem;
            margin-top: 0.65rem;
        }}

        .pred-horizon-row {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }}

        .horizon-chip {{
            padding: 0.3rem 0.75rem;
            border-radius: 8px;
            font-size: 0.72rem;
            font-weight: 600;
            border: 1px solid rgba(77, 182, 255, 0.3);
            color: rgba(255, 255, 255, 0.7);
            background: rgba(77, 182, 255, 0.08);
            cursor: pointer;
            transition: background 0.18s ease, border-color 0.18s ease;
        }}

        .horizon-chip--active {{
            background: rgba(77, 182, 255, 0.22);
            border-color: rgba(77, 182, 255, 0.65);
            color: var(--sky);
        }}

        /* ── Prediction panel: input field overrides ────────────────────── */
        .pred-field-label {{
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.52);
            margin: 0 0 0.28rem;
        }}

        .pred-field-error {{
            font-size: 0.66rem;
            color: {COLORS["red"]};
            margin-top: 0.22rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .pred-field-ok {{
            font-size: 0.66rem;
            color: {COLORS["teal"]};
            margin-top: 0.22rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        /* Engine toggle row */
        .engine-toggle-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0, 0, 0, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 12px;
            padding: 0.65rem 0.9rem;
            margin-bottom: 0.6rem;
        }}

        .engine-toggle-label {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.82rem;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.82);
        }}

        .engine-on-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}

        .engine-on-badge--on {{
            background: rgba(46, 204, 113, 0.18);
            border: 1px solid rgba(46, 204, 113, 0.45);
            color: {COLORS["green"]};
        }}

        .engine-on-badge--off {{
            background: rgba(229, 57, 53, 0.14);
            border: 1px solid rgba(229, 57, 53, 0.35);
            color: {COLORS["red"]};
        }}

        /* Live preview panel */
        .live-preview-card {{
            background: rgba(0, 0, 0, 0.28);
            border: 1px solid rgba(77, 182, 255, 0.18);
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin-top: 0.75rem;
        }}

        .live-preview-title {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: {COLORS["sky"]};
            margin-bottom: 0.65rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .live-preview-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 0.5rem;
        }}

        .live-field {{
            display: flex;
            flex-direction: column;
            gap: 0.12rem;
        }}

        .live-field-key {{
            font-size: 0.6rem;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.4);
        }}

        .live-field-val {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.88rem;
            font-weight: 500;
            color: var(--white);
        }}

        .live-field-val--warn {{
            color: {COLORS["orange"]};
        }}

        .live-field-val--ok {{
            color: {COLORS["teal"]};
        }}

        .live-field-val--err {{
            color: {COLORS["red"]};
        }}

        /* Divider */
        .pred-divider {{
            border: none;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            margin: 0.75rem 0;
        }}

        /* Predict / Reset buttons — override defaults for this panel */
        .pred-action-row {{
            display: flex;
            gap: 0.6rem;
            margin-top: 0.75rem;
        }}

        /* Streamlit toggle override */
        div[data-testid="stToggle"] label {{
            color: rgba(255, 255, 255, 0.75) !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
        }}

        div[data-testid="stToggle"] {{
            background: transparent !important;
        }}

        /* ── Responsive breakpoints ─────────────────────────────────────── */
        @media (max-width: 1100px) {{
            .metric-grid {{
                grid-template-columns: 1fr;
            }}
            .brand-bar {{
                flex-direction: column;
                gap: 0.65rem;
                text-align: center;
            }}
            [data-testid="column"] > div {{
                margin-bottom: 0.75rem;
            }}
        }}

        @media (max-width: 720px) {{
            .kpi-row {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    # Inject card CSS separately — these strings already contain evaluated CSS braces
    # and cannot be embedded inside an f-string without breaking Python's parser.
    st.markdown(
        "<style>"
        + DASHBOARD_CARD_CSS
        + ALERT_PANEL_CSS
        + "</style>",
        unsafe_allow_html=True,
    )


def render_brand_header() -> None:
    """Top navigation bar with brand identity and live-status indicator."""
    st.markdown(
        """
        <div class="brand-bar animate-in">
            <div class="brand-logo">
                <div class="brand-icon">⚓</div>
                <div>
                    <p class="brand-title">SeaSentry</p>
                    <p class="brand-subtitle">AI-Powered Maritime Drift Guard</p>
                </div>
            </div>
            <div class="status-pill">
                <span class="status-dot"></span>
                Monitoring Active · Demo Mode
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_vessel_controls(vessel: dict[str, Any]) -> dict[str, Any] | None:
    """Left panel — vessel position and navigation inputs (layout only)."""
    st.markdown(
        '<p class="section-title"><span>⛵</span> Vessel Telemetry</p>',
        unsafe_allow_html=True,
    )

    lat = st.number_input(
        "Latitude",
        value=float(vessel["latitude"]),
        format="%.4f",
        step=0.0001,
        key="input_lat",
    )
    lon = st.number_input(
        "Longitude",
        value=float(vessel["longitude"]),
        format="%.4f",
        step=0.0001,
        key="input_lon",
    )
    heading = st.slider(
        "Heading (°)",
        min_value=0,
        max_value=359,
        value=int(vessel["heading_deg"]),
        key="input_heading",
    )
    speed = st.slider(
        "Speed (kn)",
        min_value=0.0,
        max_value=15.0,
        value=float(vessel["speed_knots"]),
        step=0.1,
        key="input_speed",
    )

    st.markdown(
        '<p class="section-title" style="margin-top:0.5rem;"><span>🌊</span> Environment</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-tile">
                <div class="metric-label">Current</div>
                <div class="metric-value">{vessel["current_speed_kn"]:.1f}<span class="metric-unit">kn @ {vessel["current_direction_deg"]}°</span></div>
            </div>
            <div class="metric-tile">
                <div class="metric-label">Wind</div>
                <div class="metric-value">{vessel["wind_speed_kn"]:.1f}<span class="metric-unit">kn @ {vessel["wind_direction_deg"]}°</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="section-title" style="margin-top:0.75rem;"><span>⚙️</span> Actions</p>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        st.button("▶ Run Prediction", use_container_width=True, disabled=True, help="Backend not connected")
    with col_b:
        st.button("🔊 Voice Alert", type="secondary", use_container_width=True, disabled=True)

    return {
        "latitude": lat,
        "longitude": lon,
        "heading_deg": heading,
        "speed_knots": speed,
    }


def render_metrics_row(vessel: dict[str, Any]) -> None:
    """Right panel — key drift metrics."""
    risk = RISK_STYLES.get(vessel["risk_level"], RISK_STYLES["MEDIUM"])
    risk_bg = f"background: {risk['color']}22; border: 1px solid {risk['color']}55;"

    st.markdown(
        f"""
        <div class="glass-card">
            <p class="section-title"><span>📡</span> Drift Analytics</p>
            <div class="risk-badge" style="{risk_bg}">
                <span class="risk-icon">{risk["icon"]}</span>
                <div>
                    <div class="risk-label">Risk Classification</div>
                    <div class="risk-level" style="color: {risk["color"]};">{risk["label"]}</div>
                </div>
            </div>
            <div class="metric-grid">
                <div class="metric-tile">
                    <div class="metric-label">Distance to Boundary</div>
                    <div class="metric-value">{vessel["distance_to_boundary_nm"]:.1f}<span class="metric-unit">nm</span></div>
                </div>
                <div class="metric-tile">
                    <div class="metric-label">ETA to Boundary</div>
                    <div class="metric-value">{vessel["eta_to_boundary_min"]}<span class="metric-unit">min</span></div>
                </div>
                <div class="metric-tile">
                    <div class="metric-label">Vessel Speed</div>
                    <div class="metric-value">{vessel["speed_knots"]:.1f}<span class="metric-unit">kn</span></div>
                </div>
                <div class="metric-tile">
                    <div class="metric-label">Heading</div>
                    <div class="metric-value">{vessel["heading_deg"]}°</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_panel(vessel: dict[str, Any]) -> None:
    """Bottom-right panel — alert status with risk-tier animations."""
    from dashboard_cards import render_alert_panel_view

    render_alert_panel_view(vessel)

    # Audio playback happens here, in the browser, NOT on the backend server
    # -- see backend/voice_resolver.py's docstring for why that distinction
    # matters once this is deployed. The alarm and voice message now play
    # as a real SEQUENCE (alarm finishes, then the message starts) via
    # audio_player.py, instead of two independent, unlinked <audio>
    # elements. If there's no recorded clip for the selected language, this
    # automatically falls back to the browser's own text-to-speech reading
    # the alert text aloud.
    from api_client import audio_url
    from audio_player import render_chained_alert_audio

    render_chained_alert_audio(
        alarm_url=audio_url(vessel.get("alarm_file")),
        voice_url=audio_url(vessel.get("voice_file")),
        fallback_text=vessel.get("alert_message"),
        fallback_lang=vessel.get("tts_lang_code", "en-IN"),
        key=f"alert_{vessel.get('latitude')}_{vessel.get('longitude')}_{vessel.get('risk_level')}",
    )


def render_footer() -> None:
    """Dashboard footer."""
    st.markdown(
        """
        <div class="dashboard-footer">
            SeaSentry · Maritime Drift Guard · Layout Preview · Backend integration pending
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_top_kpi_row(vessel: dict[str, Any]) -> None:
    """Full-width top row — 4 KPI tiles: position, distance, ETA, risk."""
    from dashboard_cards import render_vessel_kpi_row

    render_vessel_kpi_row(vessel)


def render_env_conditions(vessel: dict[str, Any]) -> None:
    """Right panel — environmental conditions using reusable dashboard cards."""
    from dashboard_cards import render_env_conditions_panel

    render_env_conditions_panel(vessel)


def render_prediction_controls() -> None:
    """Bottom-left panel — full prediction control form with live preview and validation."""

    # ── Session-state defaults (first run) ────────────────────────────────
    if "pc_lat" not in st.session_state:
        st.session_state.pc_lat = DEMO_VESSEL["latitude"]
    if "pc_lon" not in st.session_state:
        st.session_state.pc_lon = DEMO_VESSEL["longitude"]
    if "pc_speed" not in st.session_state:
        st.session_state.pc_speed = DEMO_VESSEL["speed_knots"]
    if "pc_heading" not in st.session_state:
        st.session_state.pc_heading = DEMO_VESSEL["heading_deg"]
    if "pc_engine" not in st.session_state:
        st.session_state.pc_engine = True
    if "pc_submitted" not in st.session_state:
        st.session_state.pc_submitted = False

    # ── Reset callback ─────────────────────────────────────────────────────
    def _reset() -> None:
        st.session_state.pc_lat = DEMO_VESSEL["latitude"]
        st.session_state.pc_lon = DEMO_VESSEL["longitude"]
        st.session_state.pc_speed = DEMO_VESSEL["speed_knots"]
        st.session_state.pc_heading = DEMO_VESSEL["heading_deg"]
        st.session_state.pc_engine = True
        st.session_state.pc_language = "tamil"
        st.session_state.pc_submitted = False

    # ── Panel header ───────────────────────────────────────────────────────
    st.markdown(
        """
        <p class="section-title" style="margin-top:0.85rem;">
            <span>🎛️</span> Prediction Controls
        </p>
        """,
        unsafe_allow_html=True,
    )

    # ── Row 1: Latitude / Longitude ────────────────────────────────────────
    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat_val = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=float(st.session_state.pc_lat),
            format="%.4f",
            step=0.0001,
            key="pc_lat",
            help="Decimal degrees (−90 to +90)",
        )
    with col_lon:
        lon_val = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=float(st.session_state.pc_lon),
            format="%.4f",
            step=0.0001,
            key="pc_lon",
            help="Decimal degrees (−180 to +180)",
        )

    # ── Validation: lat/lon ───────────────────────────────────────────────
    lat_ok = -90.0 <= lat_val <= 90.0
    lon_ok = -180.0 <= lon_val <= 180.0

    col_lat_msg, col_lon_msg = st.columns(2)
    with col_lat_msg:
        if lat_ok:
            st.markdown(
                '<div class="pred-field-ok">✓ Valid latitude</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="pred-field-error">✕ Must be −90 to +90</div>',
                unsafe_allow_html=True,
            )
    with col_lon_msg:
        if lon_ok:
            st.markdown(
                '<div class="pred-field-ok">✓ Valid longitude</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="pred-field-error">✕ Must be −180 to +180</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="pred-divider">', unsafe_allow_html=True)

    # ── Row 2: Engine toggle (moved before Speed so the speed validation
    # below can react to engine state -- see the note on all_valid further
    # down for why the ordering matters) ────────────────────────────────────
    engine_on = st.toggle(
        "🔧  Engine",
        value=st.session_state.pc_engine,
        key="pc_engine",
        help="Engine ON uses propulsion speed; Engine OFF models pure drift.",
    )

    badge_cls = "engine-on-badge--on" if engine_on else "engine-on-badge--off"
    badge_txt = "● ON" if engine_on else "● OFF"
    engine_note = (
        "Propulsion active — speed contributes to trajectory."
        if engine_on
        else "Engine off — vessel in free drift mode. Speed may be 0."
    )
    st.markdown(
        f"""
        <div class="engine-toggle-row" style="margin-top:0.35rem;">
            <span class="engine-toggle-label">Engine status</span>
            <span class="engine-on-badge {badge_cls}">{badge_txt}</span>
        </div>
        <div style="font-size:0.72rem; color:rgba(255,255,255,0.45); margin-bottom:0.1rem;">
            {engine_note}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="pred-divider">', unsafe_allow_html=True)

    # ── Row 3: Speed slider ────────────────────────────────────────────────
    speed_val = st.slider(
        "Boat Speed (knots)",
        min_value=0.0,
        max_value=30.0,
        value=float(st.session_state.pc_speed),
        step=0.1,
        key="pc_speed",
        help="Speed over ground in knots (0 – 30 kn)",
    )

    # Speed validation tiers -- FIXED: speed=0 is only a problem when the
    # engine is ON (a boat "in gear" that isn't moving is worth flagging).
    # With the engine OFF, speed=0 is the correct, expected value for the
    # core "crew asleep, pure drift" scenario -- it used to be flagged as
    # an error unconditionally, which also fed into a bug below that made
    # it IMPOSSIBLE to ever submit an engine-off/speed-0 prediction at all.
    if speed_val == 0.0 and engine_on:
        speed_msg_cls = "pred-field-error"
        speed_msg_txt = "✕ Engine is ON but speed is 0 — vessel should be moving"
    elif speed_val == 0.0 and not engine_on:
        speed_msg_cls = "pred-field-ok"
        speed_msg_txt = "✓ Drifting — no propulsion (engine off)"
    elif speed_val <= 5.0:
        speed_msg_cls = "pred-field-ok"
        speed_msg_txt = "✓ Typical fishing speed"
    elif speed_val <= 15.0:
        speed_msg_cls = "pred-field-ok"
        speed_msg_txt = "✓ Normal transit speed"
    else:
        speed_msg_cls = "pred-field-error"
        speed_msg_txt = "⚠ Speed unusually high — verify reading"

    st.markdown(
        f'<div class="{speed_msg_cls}">{speed_msg_txt}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="pred-divider">', unsafe_allow_html=True)

    # ── Row 4: Heading ─────────────────────────────────────────────────────
    heading_val = st.number_input(
        "Heading (°)",
        min_value=0,
        max_value=359,
        value=int(st.session_state.pc_heading),
        step=1,
        key="pc_heading",
        help="Compass heading 0°–359° (0 = North)",
    )

    # Cardinal label
    _cardinals = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    _cardinal = _cardinals[round(heading_val / 22.5) % 16]

    heading_ok = 0 <= heading_val <= 359
    if heading_ok:
        st.markdown(
            f'<div class="pred-field-ok">✓ Heading {heading_val}° — {_cardinal}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="pred-field-error">✕ Heading must be 0°–359°</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="pred-divider">', unsafe_allow_html=True)

    # ── Row 5: Voice alert language ────────────────────────────────────────
    if "pc_language" not in st.session_state:
        st.session_state.pc_language = "tamil"

    language_val = st.selectbox(
        "🔊 Voice Alert Language",
        options=["tamil", "kannada", "english"],
        format_func=lambda v: {
            "tamil":   "தமிழ் · Tamil",
            "kannada": "ಕನ್ನಡ · Kannada",
            "english": "English",
        }[v],
        key="pc_language",
        help=(
            "Tamil and Kannada play recorded human voice clips. English "
            "uses browser text-to-speech when no recording is available."
        ),
    )
    if language_val == "english":
        st.markdown(
            '<div class="pred-field-ok" style="opacity:0.75;">'
            'ℹ using browser text-to-speech (no recorded clip for English yet)'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="pred-divider">', unsafe_allow_html=True)

    # ── Live preview panel ─────────────────────────────────────────────────
    # FIXED: this used to require speed_val > 0.0 unconditionally, which
    # made it IMPOSSIBLE to ever submit a prediction with the engine off and
    # speed at 0 -- i.e. the core "engine off, crew asleep, pure drift"
    # scenario the whole project is built around could never actually be
    # tested through the UI. Speed=0 is now only invalid when the engine is
    # ON (which genuinely is a data-entry mistake worth flagging).
    all_valid = lat_ok and lon_ok and heading_ok and (speed_val > 0.0 or not engine_on)

    speed_cls = "live-field-val--ok" if 0 < speed_val <= 15.0 else "live-field-val--warn"
    pos_cls   = "live-field-val--ok" if (lat_ok and lon_ok) else "live-field-val--err"
    hdg_cls   = "live-field-val--ok" if heading_ok else "live-field-val--err"

    st.markdown(
        f"""
        <div class="live-preview-card">
            <div class="live-preview-title">
                ⚡ Live Input Preview
            </div>
            <div class="live-preview-grid">
                <div class="live-field">
                    <span class="live-field-key">Latitude</span>
                    <span class="live-field-val {pos_cls}">{lat_val:.4f}°</span>
                </div>
                <div class="live-field">
                    <span class="live-field-key">Longitude</span>
                    <span class="live-field-val {pos_cls}">{lon_val:.4f}°</span>
                </div>
                <div class="live-field">
                    <span class="live-field-key">Speed</span>
                    <span class="live-field-val {speed_cls}">{speed_val:.1f} kn</span>
                </div>
                <div class="live-field">
                    <span class="live-field-key">Heading</span>
                    <span class="live-field-val {hdg_cls}">{heading_val}° {_cardinal}</span>
                </div>
                <div class="live-field">
                    <span class="live-field-key">Engine</span>
                    <span class="live-field-val {'live-field-val--ok' if engine_on else 'live-field-val--warn'}">
                        {'ON' if engine_on else 'OFF'}
                    </span>
                </div>
                <div class="live-field">
                    <span class="live-field-key">Ready</span>
                    <span class="live-field-val {'live-field-val--ok' if all_valid else 'live-field-val--err'}">
                        {'✓ Valid' if all_valid else '✕ Fix errors'}
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Action buttons ─────────────────────────────────────────────────────
    col_predict, col_reset = st.columns([1.6, 1.0])
    with col_predict:
        predict_clicked = st.button(
            "▶ Predict Drift",
            use_container_width=True,
            disabled=not all_valid,
            help=(
                "Calls the backend /predict endpoint with these inputs"
                if all_valid
                else "Fix validation errors before running prediction"
            ),
            key="pc_btn_predict",
        )

        if predict_clicked and all_valid:
            from api_client import call_predict, to_vessel_dict

            try:
                with st.spinner("Contacting backend..."):
                    prediction = call_predict(
                        lat=lat_val,
                        lon=lon_val,
                        speed_kn=speed_val,
                        heading_deg=heading_val,
                        engine_off=not engine_on,
                        language=language_val,
                    )
                st.session_state.vessel_data = to_vessel_dict(
                    prediction, lat_val, lon_val, heading_val, speed_val, language=language_val
                )
                st.session_state.pc_submitted = True
                st.rerun()
            except Exception as exc:  # noqa: BLE001 -- surface any backend/network error to the user
                st.markdown(
                    f'<div class="pred-field-error" style="margin-top:0.3rem;">'
                    f"✕ Could not reach backend: {exc}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        if not all_valid:
            st.markdown(
                '<div class="pred-field-error" style="margin-top:0.3rem;">'
                '✕ Resolve input errors to enable prediction'
                '</div>',
                unsafe_allow_html=True,
            )
        elif st.session_state.pc_submitted:
            st.markdown(
                '<div class="pred-field-ok" style="margin-top:0.3rem;">'
                '✓ Prediction received — see panels above'
                '</div>',
                unsafe_allow_html=True,
            )

    with col_reset:
        if st.button(
            "↺ Reset",
            type="secondary",
            use_container_width=True,
            key="pc_btn_reset",
        ):
            _reset()
            st.rerun()