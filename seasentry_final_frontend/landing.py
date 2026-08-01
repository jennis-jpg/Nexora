"""SeaSentry marketing landing page."""

from __future__ import annotations

import streamlit as st

from controls import COLORS


def inject_landing_css() -> None:
    """Landing-page styles — animated ocean, waves, and section layout."""
    st.markdown(
        f"""
        <style>
        .block-container {{
            padding-top: 0 !important;
            max-width: 100% !important;
        }}

        .landing-wrap {{
            position: relative;
            overflow: hidden;
        }}

        /* ── Top navigation ─────────────────────────────────────────────── */
        .landing-navbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.9rem 1.75rem;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .landing-navbar-brand {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .landing-navbar-icon {{
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, {COLORS["ocean"]}, {COLORS["teal"]});
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            box-shadow: 0 4px 16px rgba(0, 194, 168, 0.35);
            transition: transform 0.3s ease;
        }}

        .landing-navbar:hover .landing-navbar-icon {{
            transform: scale(1.06) rotate(-4deg);
        }}

        .landing-navbar-title {{
            font-size: 1.3rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
            line-height: 1.2;
            background: linear-gradient(90deg, {COLORS["white"]}, {COLORS["sky"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .landing-navbar-tagline {{
            font-size: 0.72rem;
            font-weight: 400;
            color: rgba(255, 255, 255, 0.55);
            margin: 0;
            letter-spacing: 0.03em;
        }}

        /* Animated ocean hero background */
        .landing-hero {{
            position: relative;
            min-height: 88vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 3.5rem 1.5rem 8rem;
            background: linear-gradient(
                135deg,
                {COLORS["navy"]} 0%,
                #022847 25%,
                {COLORS["ocean"]} 50%,
                #023e6b 75%,
                {COLORS["navy"]} 100%
            );
            background-size: 400% 400%;
            animation: ocean-gradient 14s ease infinite;
        }}

        @keyframes ocean-gradient {{
            0%, 100% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
        }}

        .landing-hero::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(ellipse 70% 50% at 50% 0%, rgba(77, 182, 255, 0.22) 0%, transparent 60%),
                radial-gradient(ellipse 50% 40% at 80% 80%, rgba(0, 194, 168, 0.15) 0%, transparent 55%);
            pointer-events: none;
        }}

        /* SVG wave layers */
        .wave-container {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 140px;
            overflow: hidden;
            line-height: 0;
        }}

        .wave-layer {{
            position: absolute;
            bottom: 0;
            left: 0;
            width: 200%;
            height: 100%;
            animation: wave-drift linear infinite;
        }}

        .wave-layer--1 {{
            animation-duration: 18s;
            opacity: 0.35;
        }}

        .wave-layer--2 {{
            animation-duration: 12s;
            animation-direction: reverse;
            opacity: 0.55;
            bottom: 8px;
        }}

        .wave-layer--3 {{
            animation-duration: 8s;
            opacity: 0.75;
            bottom: 16px;
        }}

        @keyframes wave-drift {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        .hero-content {{
            position: relative;
            z-index: 2;
            max-width: 900px;
            animation: fade-slide-up 0.8s ease-out both;
        }}

        /* Boat illustration */
        .hero-illustration {{
            display: flex;
            justify-content: center;
            margin-bottom: 1.25rem;
            transition: transform 0.4s ease;
        }}

        .hero-illustration:hover {{
            transform: translateY(-4px) scale(1.03);
        }}

        .hero-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.45rem 1rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: {COLORS["teal"]};
            background: rgba(0, 194, 168, 0.12);
            border: 1px solid rgba(0, 194, 168, 0.35);
            margin-bottom: 1.5rem;
        }}

        .hero-title {{
            font-size: clamp(2.4rem, 5vw, 3.75rem);
            font-weight: 700;
            line-height: 1.12;
            letter-spacing: -0.03em;
            margin: 0 0 1.25rem;
            background: linear-gradient(90deg, {COLORS["white"]} 0%, {COLORS["sky"]} 55%, {COLORS["teal"]} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .hero-subtitle {{
            font-size: clamp(1rem, 2vw, 1.2rem);
            line-height: 1.65;
            color: rgba(255, 255, 255, 0.72);
            max-width: 620px;
            margin: 0 auto 1rem;
            font-weight: 400;
        }}

        /* ── Role selection cards ───────────────────────────────────────── */
        .role-cards-offset {{
            position: relative;
            z-index: 5;
            margin-top: -4.5rem;
            padding-bottom: 1.5rem;
        }}

        .role-cards-offset div[data-testid="stHorizontalBlock"] {{
            max-width: 820px;
            margin: 0 auto;
        }}

        .role-card {{
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 20px;
            padding: 1.85rem 1.6rem 1.25rem;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
            margin-bottom: -0.6rem;
        }}

        .role-card:hover {{
            transform: translateY(-6px);
            border-color: rgba(77, 182, 255, 0.4);
            box-shadow: 0 16px 44px rgba(0, 91, 150, 0.3);
        }}

        .role-card-icon {{
            width: 60px;
            height: 60px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            margin: 0 auto 1rem;
            background: linear-gradient(135deg, {COLORS["ocean"]}, {COLORS["teal"]});
            box-shadow: 0 4px 18px rgba(0, 194, 168, 0.35);
            transition: transform 0.3s ease;
        }}

        .role-card--coastguard .role-card-icon {{
            background: linear-gradient(135deg, {COLORS["red"]}, {COLORS["orange"]});
            box-shadow: 0 4px 18px rgba(229, 57, 53, 0.32);
        }}

        .role-card:hover .role-card-icon {{
            transform: scale(1.08) rotate(-4deg);
        }}

        .role-card h3 {{
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0 0 0.55rem;
            color: {COLORS["white"]};
        }}

        .role-card p {{
            font-size: 0.88rem;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.64);
            margin: 0 0 1.35rem;
            min-height: 46px;
        }}

        .role-card-btn-wrap {{
            position: relative;
            z-index: 6;
        }}

        .role-card-btn-wrap div[data-testid="stButton"] button {{
            border-radius: 12px !important;
            font-weight: 600 !important;
        }}

        .landing-section {{
            padding: 4.5rem 1.5rem;
            max-width: 1100px;
            margin: 0 auto;
        }}

        .section-heading {{
            text-align: center;
            margin-bottom: 2.75rem;
        }}

        .section-heading h2 {{
            font-size: clamp(1.75rem, 3vw, 2.25rem);
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0 0 0.65rem;
            color: {COLORS["white"]};
        }}

        .section-heading p {{
            font-size: 1rem;
            color: rgba(255, 255, 255, 0.58);
            margin: 0;
            max-width: 540px;
            margin-left: auto;
            margin-right: auto;
        }}

        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
        }}

        .feature-card {{
            background: rgba(255, 255, 255, 0.07);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            padding: 1.5rem;
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            animation: fade-slide-up 0.6s ease-out both;
        }}

        .feature-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(77, 182, 255, 0.35);
            box-shadow: 0 12px 40px rgba(0, 91, 150, 0.25);
        }}

        .feature-icon {{
            width: 48px;
            height: 48px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, {COLORS["ocean"]}, {COLORS["teal"]});
            box-shadow: 0 4px 16px rgba(0, 194, 168, 0.3);
            transition: transform 0.3s ease;
        }}

        .feature-card:hover .feature-icon {{
            transform: scale(1.08) rotate(-4deg);
        }}

        .feature-card h3 {{
            font-size: 1.05rem;
            font-weight: 600;
            margin: 0 0 0.5rem;
            color: {COLORS["white"]};
        }}

        .feature-card p {{
            font-size: 0.88rem;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.62);
            margin: 0;
        }}

        .landing-footer {{
            padding: 2.5rem 1.5rem;
            text-align: center;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(0, 0, 0, 0.25);
        }}

        .landing-footer-brand {{
            font-size: 1.15rem;
            font-weight: 700;
            background: linear-gradient(90deg, {COLORS["white"]}, {COLORS["sky"]});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.35rem;
        }}

        .landing-footer-tagline {{
            font-size: 0.78rem;
            color: rgba(255, 255, 255, 0.45);
            letter-spacing: 0.04em;
            margin-bottom: 1.25rem;
        }}

        .landing-footer-links {{
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 1.25rem;
        }}

        .landing-footer-links a {{
            color: rgba(255, 255, 255, 0.55);
            text-decoration: none;
            font-size: 0.82rem;
            transition: color 0.2s ease;
        }}

        .landing-footer-links a:hover {{
            color: {COLORS["sky"]};
        }}

        .landing-footer-copy {{
            font-size: 0.72rem;
            color: rgba(255, 255, 255, 0.3);
        }}

        div[data-testid="column"] .stButton > button {{
            min-width: 160px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        div[data-testid="column"] .stButton > button:hover {{
            transform: translateY(-2px);
        }}

        @media (max-width: 768px) {{
            .landing-hero {{
                min-height: 78vh;
                padding: 2.5rem 1rem 7rem;
            }}
            .landing-section {{
                padding: 3rem 1rem;
            }}
            .landing-navbar {{
                padding: 0.75rem 1rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_navbar() -> None:
    """Top navigation — logo, project title, and tagline."""
    st.markdown(
        """
        <div class="landing-navbar animate-in">
            <div class="landing-navbar-brand">
                <div class="landing-navbar-icon">⚓</div>
                <div>
                    <p class="landing-navbar-title">SeaSentry AI</p>
                    <p class="landing-navbar-tagline">AI Powered Maritime Safety Assistant</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_hero_html() -> None:
    """Self-contained hero section: boat illustration, gradient, title, and waves.

    Rendered as a single st.markdown call so every tag opened here is also
    closed here — Streamlit parses each markdown call independently, so an
    element can't be opened here and closed by a later call.
    """
    st.markdown(
        f"""
        <div class="landing-wrap">
            <section class="landing-hero">
                <div class="hero-content">
                    <div class="hero-illustration">
                        <svg width="200" height="140" viewBox="0 0 220 150" xmlns="http://www.w3.org/2000/svg">
                            <path d="M15,120 Q55,104 95,120 T175,120 T215,120" stroke="{COLORS['sky']}"
                                  stroke-width="3" fill="none" opacity="0.35"/>
                            <path d="M5,132 Q50,116 95,132 T185,132 T225,132" stroke="{COLORS['teal']}"
                                  stroke-width="3" fill="none" opacity="0.5"/>
                            <line x1="110" y1="18" x2="110" y2="88" stroke="{COLORS['white']}"
                                  stroke-width="3" stroke-linecap="round" opacity="0.9"/>
                            <path d="M113,22 L113,80 L153,76 Z" fill="{COLORS['sky']}" opacity="0.9"/>
                            <path d="M107,28 L107,80 L75,74 Z" fill="{COLORS['teal']}" opacity="0.85"/>
                            <rect x="58" y="86" width="104" height="9" rx="4" fill="{COLORS['ocean']}"/>
                            <path d="M50,95 L170,95 L152,126 L68,126 Z" fill="{COLORS['navy']}"
                                  stroke="{COLORS['sky']}" stroke-width="2"/>
                            <circle cx="110" cy="14" r="4" fill="{COLORS['orange']}"/>
                        </svg>
                    </div>
                    <div class="hero-badge">
                        <span>⚓</span> SeaSentry · AI-Powered Maritime Drift Guard
                    </div>
                    <h1 class="hero-title">Navigate Safely. Stay Within Borders.</h1>
                    <p class="hero-subtitle">
                        AI-powered prediction system preventing accidental maritime boundary crossings.
                    </p>
                </div>
                <div class="wave-container">
                    <svg class="wave-layer wave-layer--1" viewBox="0 0 1200 120" preserveAspectRatio="none">
                        <path d="M0,60 C300,120 600,0 900,60 C1050,90 1150,80 1200,60 L1200,120 L0,120 Z"
                              fill="{COLORS['ocean']}" fill-opacity="0.6"/>
                    </svg>
                    <svg class="wave-layer wave-layer--2" viewBox="0 0 1200 120" preserveAspectRatio="none">
                        <path d="M0,70 C250,20 550,100 800,50 C1000,20 1100,90 1200,70 L1200,120 L0,120 Z"
                              fill="{COLORS['teal']}" fill-opacity="0.45"/>
                    </svg>
                    <svg class="wave-layer wave-layer--3" viewBox="0 0 1200 120" preserveAspectRatio="none">
                        <path d="M0,80 C200,40 400,100 600,65 C800,30 1000,95 1200,75 L1200,120 L0,120 Z"
                              fill="{COLORS['sky']}" fill-opacity="0.3"/>
                    </svg>
                </div>
            </section>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_role_cards() -> None:
    """Two large role-selection cards: Fisherman and Coastguard.

    Pulled up over the hero's wave area with a negative margin, the same
    trick the original hero CTA buttons used — Streamlit elements can't be
    nested inside the hero's own (already-closed) markup, so this is a
    separate section that visually overlaps it instead.
    """
    st.markdown('<div class="role-cards-offset">', unsafe_allow_html=True)
    col_fisher, col_guard = st.columns(2, gap="large")

    with col_fisher:
        st.markdown(
            """
            <div class="role-card role-card--fisherman">
                <div class="role-card-icon">🐟</div>
                <h3>Fisherman</h3>
                <p>Monitor your journey, receive voice alerts, emergency assistance
                   and weather updates.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="role-card-btn-wrap">', unsafe_allow_html=True)
        if st.button("▶ Enter Dashboard", use_container_width=True, type="primary", key="btn_fisherman"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_guard:
        st.markdown(
            """
            <div class="role-card role-card--coastguard">
                <div class="role-card-icon">🛡</div>
                <h3>Coastguard</h3>
                <p>Monitor vessels, receive emergency alerts and coordinate
                   rescue operations.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="role-card-btn-wrap">', unsafe_allow_html=True)
        if st.button("Open Control Center", use_container_width=True, type="secondary", key="btn_coastguard"):
            st.session_state.page = "coastguard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


_FEATURES: list[tuple[str, str, str]] = [
    ("🌊", "AI Drift Prediction", "Projects vessel trajectory using live currents, wind, and heading to forecast drift."),
    ("🧭", "Border Crossing Detection", "Flags the exact moment a vessel is on course to cross a maritime boundary."),
    ("🆘", "SOS Emergency", "One-tap distress signal that instantly alerts nearby crews and coastguard responders."),
    ("🔊", "Voice Alerts", "Hands-free spoken warnings in Kannada or English so crews can act without leaving the helm."),
    ("📡", "Weather Intelligence", "Real-time wind and ocean current data feeds the prediction engine for accurate modeling."),
    ("📏", "Water Level Monitoring", "Tracks distance and ETA to the boundary so crews always know how much safe water remains."),
    ("📋", "Automatic Incident Report", "Generates a structured incident report the moment a crossing or emergency is detected."),
    ("🛑", "Dead Man Switch", "Detects an unresponsive crew and automatically escalates to an emergency alert."),
    ("🛰️", "Live Vessel Tracking", "Continuously tracks vessel position, heading, and speed on an interactive map."),
]


def _render_features() -> None:
    # NOTE: each card fragment is built as a single line (no embedded newlines
    # or indentation), and the section wrapper below has no blank line between
    # its tags and cards_html. A whitespace-only line inside an
    # unsafe_allow_html block makes Streamlit's markdown parser drop out of
    # "raw HTML" mode, so any indented line right after it gets rendered as
    # literal visible text instead of markup -- this is what was causing the
    # stray "</div>" text to show up on the page.
    cards_html = "".join(
        f'<div class="feature-card" style="animation-delay:{0.05 * (i + 1):.2f}s">'
        f'<div class="feature-icon">{icon}</div>'
        f"<h3>{title}</h3>"
        f"<p>{desc}</p>"
        f"</div>"
        for i, (icon, title, desc) in enumerate(_FEATURES)
    )
    section_html = (
        '<section id="features" class="landing-section">'
        '<div class="section-heading">'
        "<h2>Features</h2>"
        "<p>Everything fishermen and coastguard teams need to stay safe and coordinated at sea.</p>"
        "</div>"
        f'<div class="feature-grid">{cards_html}</div>'
        "</section>"
    )
    st.markdown(section_html, unsafe_allow_html=True)


def _render_landing_footer() -> None:
    st.markdown(
        """
        <footer class="landing-footer">
            <div class="landing-footer-brand">SeaSentry AI</div>
            <div class="landing-footer-tagline">AI Powered Maritime Safety Assistant</div>
            <nav class="landing-footer-links">
                <a href="#features">Features</a>
            </nav>
            <div class="landing-footer-copy">
                © 2026 SeaSentry · Protecting fishermen · Preventing accidental boundary crossings
            </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    """Render the full SeaSentry landing page."""
    inject_landing_css()
    _render_navbar()
    _render_hero_html()
    _render_role_cards()
    _render_features()
    _render_landing_footer()
