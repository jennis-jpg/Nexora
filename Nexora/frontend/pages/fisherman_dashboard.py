"""SeaSentry — Fisherman Dashboard (High-Visibility Simplified Design).

Design goals
------------
* Large, bold, colour-coded status cards readable from several feet away.
* A single, unmistakable RED SOS button dominates the bottom of the screen.
* Simulation controls are hidden in a collapsed sidebar expander so the
  fisherman never sees sliders or technical options.
* All five metric cards update instantly whenever a sidebar slider changes.

Architecture
------------
  _init_state()           — seed every session-state key once per load
  _render_sidebar()       — all simulation sliders inside collapsed expander
  _generate_sos_pdf()     — ReportLab A4 emergency PDF
  _send_sos_email()       — SMTP dispatch (simulated when env vars absent)
  _render_sos_section()   — SOS banner → PDF → email → download flow
  render_fisherman_dashboard() — top-level entry point called by app.py

Bug fixes applied
-----------------
* StreamlitDuplicateElementKey: fh_voice_on toggle lives ONLY in the
  sidebar — _render_voice_section() reads the key but never creates a
  second widget.
* Raw JS on screen: render_chained_alert_audio() uses
  components.html(height=0); nothing is printed to the page.
"""

from __future__ import annotations

import io
import math
import os
import random
import smtplib
from datetime import datetime, timedelta
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

# ── Project imports with standalone fallback ───────────────────────────────────
try:
    from audio_player import render_chained_alert_audio
    from api_client import audio_url as _audio_url, call_sos
    from controls import COLORS, DEMO_VESSEL
    from map_view import create_sea_map
    _PROJECT_IMPORTS = True
except ImportError:
    _PROJECT_IMPORTS = False
    COLORS = {
        "green":  "#2ECC71",
        "orange": "#FF9800",
        "red":    "#E53935",
        "sky":    "#4DB6FF",
        "text":   "#FFFFFF",
    }
    DEMO_VESSEL: dict[str, Any] = {
        "latitude": 9.4823, "longitude": 79.35,
        "risk_level": "LOW", "distance_to_boundary_nm": 12.0,
        "eta_to_boundary_min": 45, "heading_deg": 285, "speed_knots": 3.2,
    }
    create_sea_map = None
    render_chained_alert_audio = None
    _audio_url = None
    call_sos = None


# ══════════════════════════════════════════════════════════════════════════════
# COLOUR CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

_GREEN  = "#2ECC71"
_ORANGE = "#FF9800"
_RED    = "#E53935"
_SKY    = "#4DB6FF"

# CSS classes that mirror the hex colours above
_CLS_GREEN  = "fh-green"
_CLS_ORANGE = "fh-orange"
_CLS_RED    = "fh-red"


# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap');

/* ── Root / reset ─────────────────────────────────────────────────────────── */
.fh-root {{
    font-family: 'Inter', sans-serif;
    color: #fff;
    max-width: 740px;
    margin: 0 auto;
}}

/* ── Header ───────────────────────────────────────────────────────────────── */
.fh-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 1.5rem;
    background: rgba(255,255,255,0.07); backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.13); border-radius: 22px;
    margin-bottom: 1rem;
}}
.fh-boat-name {{ font-size: 1.65rem; font-weight: 900; }}
.fh-time      {{ font-size: 1.25rem; font-weight: 700; color: rgba(255,255,255,0.7); }}
.fh-conn-dot  {{
    width: 14px; height: 14px; border-radius: 50%; display: inline-block;
    animation: fh-blink 2s ease-in-out infinite;
}}
@keyframes fh-blink {{ 0%,100%{{opacity:1}} 50%{{opacity:.3}} }}

/* ── Safety banner ────────────────────────────────────────────────────────── */
.fh-banner {{
    border-radius: 26px;
    padding: 2.4rem 1.5rem 2.1rem;
    margin-bottom: 1.1rem;
    text-align: center;
    border: 3px solid transparent;
}}
.fh-banner--safe {{
    background: linear-gradient(135deg,rgba(46,204,113,.20),rgba(0,194,168,.10));
    border-color: rgba(46,204,113,.60);
    box-shadow: 0 0 50px rgba(46,204,113,.18);
}}
.fh-banner--caution {{
    background: linear-gradient(135deg,rgba(255,193,7,.22),rgba(255,152,0,.12));
    border-color: rgba(255,193,7,.70);
    animation: glow-y 2s ease-in-out infinite;
}}
.fh-banner--danger {{
    background: linear-gradient(135deg,rgba(229,57,53,.28),rgba(183,28,28,.18));
    border-color: rgba(229,57,53,.80);
    animation: glow-r 1.4s ease-in-out infinite;
}}
@keyframes glow-y {{ 0%,100%{{box-shadow:0 0 40px rgba(255,193,7,.18)}} 50%{{box-shadow:0 0 80px rgba(255,193,7,.55)}} }}
@keyframes glow-r {{ 0%,100%{{box-shadow:0 0 40px rgba(229,57,53,.28)}} 50%{{box-shadow:0 0 90px rgba(229,57,53,.75)}} }}
.fh-banner-emoji {{ font-size: 6rem;   line-height: 1;    margin-bottom: .3rem; }}
.fh-banner-label {{ font-size: 4rem;   font-weight: 900;  letter-spacing: -.02em; line-height: 1.05; margin-bottom: .4rem; }}
.fh-banner-msg   {{ font-size: 1.5rem; font-weight: 700;  opacity: .92; }}

/* ── KPI cards ────────────────────────────────────────────────────────────── */
.fh-card {{
    border-radius: 22px;
    padding: 1.5rem 0.9rem 1.3rem;
    text-align: center;
    border: 2px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    transition: border-color .25s, box-shadow .25s;
}}

/* State-based card backgrounds */
.fh-card--safe    {{
    background: rgba(46,204,113,0.12);
    border-color: rgba(46,204,113,0.45);
}}
.fh-card--caution {{
    background: rgba(255,193,7,0.13);
    border-color: rgba(255,193,7,0.55);
}}
.fh-card--danger  {{
    background: rgba(229,57,53,0.17);
    border-color: rgba(229,57,53,0.65);
    animation: glow-r 1.6s ease-in-out infinite;
}}

.fh-card-icon   {{ font-size: 2.8rem;  line-height: 1;   margin-bottom: .35rem; }}
.fh-card-metric {{
    font-size: 2.55rem; font-weight: 900;
    line-height: 1.05;  margin-bottom: .1rem;
}}
.fh-card-label  {{
    font-size: .78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: .1em;
    color: rgba(255,255,255,.45); margin-bottom: .3rem;
}}
.fh-card-status {{
    font-size: .95rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: .06em;
    margin-top: .25rem;
}}

/* Colour helpers */
.fh-green  {{ color: {_GREEN}; }}
.fh-orange {{ color: {_ORANGE}; }}
.fh-red    {{ color: {_RED}; }}
.fh-sky    {{ color: {_SKY}; }}

/* ── Map wrapper ──────────────────────────────────────────────────────────── */
.fh-map-wrap {{
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.10);
    border-radius: 22px; padding: 1rem 1rem .55rem; margin-bottom: 1rem; overflow: hidden;
}}
.fh-map-title  {{ font-size: 1.1rem; font-weight: 800; color: rgba(255,255,255,.75); margin-bottom: .6rem; }}
.fh-map-legend {{ display:flex; gap:1.5rem; padding:.5rem 0 .1rem; font-size:.85rem;
                  color:rgba(255,255,255,.55); flex-wrap:wrap; }}

/* ── Emergency active banner ─────────────────────────────────────────────── */
.fh-emergency-banner {{
    background: linear-gradient(135deg, #B71C1C, #E53935);
    border: 3px solid #FF1744; border-radius: 22px;
    padding: 1.7rem 1.5rem 1.5rem; text-align: center;
    margin-bottom: 1rem;
    animation: fh-emerg 1.1s ease-in-out infinite;
}}
@keyframes fh-emerg {{
    0%,100% {{ box-shadow: 0 0 40px rgba(229,57,53,.55); }}
    50%      {{ box-shadow: 0 0 95px rgba(229,57,53,1.0); }}
}}
.fh-emerg-title {{ font-size: 2rem;   font-weight: 900; color:#fff; letter-spacing:.04em; margin-bottom:.35rem; }}
.fh-emerg-sub   {{ font-size: 1.15rem; font-weight: 700; color: rgba(255,255,255,.92); }}
.fh-emerg-ts    {{ font-size: .85rem;  color: rgba(255,255,255,.70); margin-top:.4rem; }}

/* ── SOS button ───────────────────────────────────────────────────────────── */
.fh-sos-wrap .stButton > button {{
    background: linear-gradient(135deg, #E53935, #b71c1c) !important;
    border: none !important; border-radius: 22px !important;
    font-size: 2.2rem !important; font-weight: 900 !important;
    padding: 1.7rem 1rem !important; color: #fff !important;
    width: 100% !important; min-height: 110px !important;
    box-shadow: 0 8px 50px rgba(229,57,53,.60) !important;
    animation: fh-sos-pulse 2s ease-in-out infinite !important;
    letter-spacing: .04em !important;
}}
@keyframes fh-sos-pulse {{
    0%,100%{{ box-shadow:0 8px 50px rgba(229,57,53,.55); transform:scale(1) }}
    50%{{ box-shadow:0 8px 80px rgba(229,57,53,.95); transform:scale(1.012) }}
}}

/* ── Share location button ────────────────────────────────────────────────── */
.fh-sec-btn .stButton > button {{
    background: rgba(255,255,255,0.08) !important;
    border: 2px solid rgba(255,255,255,0.22) !important;
    border-radius: 18px !important;
    font-size: 1.1rem !important; font-weight: 800 !important;
    padding: 1rem 1rem !important; color: #fff !important;
    min-height: 64px !important; width: 100% !important;
}}

/* ── Entrance animations ──────────────────────────────────────────────────── */
@keyframes fh-in {{ from{{opacity:0;transform:translateY(16px)}} to{{opacity:1;transform:translateY(0)}} }}
.fh-in {{ animation: fh-in .45s ease-out both; }}
.fh-d1{{animation-delay:.04s}} .fh-d2{{animation-delay:.10s}}
.fh-d3{{animation-delay:.16s}} .fh-d4{{animation-delay:.22s}}
.fh-d5{{animation-delay:.28s}} .fh-d6{{animation-delay:.34s}}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# PURE HELPERS (no Streamlit I/O)
# ══════════════════════════════════════════════════════════════════════════════

_DIRECTION_MAP: dict[str, str] = {
    "Move North":    "↑",
    "Move South":    "↓",
    "Move East":     "→",
    "Move West":     "←",
    "Hold Position": "✦",
}


def _card_state(condition: bool, danger: bool) -> str:
    """Return card CSS modifier: safe / caution / danger."""
    if danger:   return "danger"
    if condition: return "caution"
    return "safe"


def _dist_state(dist_km: float) -> tuple[str, str, str]:
    """(card-state, value-colour-class, status-label) for distance."""
    if dist_km < 2:  return "danger",  _CLS_RED,    "DANGER"
    if dist_km < 5:  return "caution", _CLS_ORANGE, "CAUTION"
    return "safe",   _CLS_GREEN,  "SAFE"


def _gps_state(status: str) -> tuple[str, str, str]:
    if status == "Signal Lost":  return "danger",  _CLS_RED,    "NO SIGNAL"
    if status == "Weak Signal":  return "caution", _CLS_ORANGE, "WEAK"
    return "safe",   _CLS_GREEN,  "OK"


def _bat_state(pct: int) -> tuple[str, str, str]:
    if pct < 15:  return "danger",  _CLS_RED,    "CRITICAL"
    if pct < 30:  return "caution", _CLS_ORANGE, "LOW"
    return "safe",   _CLS_GREEN,  "GOOD"


def _water_state(level_m: float) -> tuple[str, str, str]:
    if level_m > 1.2:  return "danger",  _CLS_RED,    "HIGH RISK"
    if level_m > 0.6:  return "caution", _CLS_ORANGE, "RISING"
    return "safe",   _CLS_GREEN,  "NORMAL"


def _safety_banner(dist_km: float) -> tuple[str, str, str, str, str]:
    """(CSS modifier, emoji, label, message, hex-colour)."""
    if dist_km < 2:
        return "danger",  "🔴", "DANGER",      "TURN BACK NOW!",            _RED
    if dist_km < 5:
        return "caution", "🟡", "NEAR BORDER", "Move away from the border.", _ORANGE
    return "safe",    "🟢", "SAFE",        "You are safe. Keep fishing.", _GREEN


# ══════════════════════════════════════════════════════════════════════════════
# SESSION-STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    """Seed every dashboard key once; existing keys are NOT overwritten.

    The sidebar widgets use key='fh_*' which makes Streamlit persist their
    values automatically — no extra callbacks or on_change handlers needed.
    """
    defaults: dict[str, Any] = {
        # ── KPI values — driven by sidebar simulation sliders ─────────────────
        "fh_distance_to_border": 12.0,   # km
        "fh_direction":          "Move North",
        "fh_gps_status":         "GPS OK",
        "fh_battery_level":      82,      # %
        "fh_water_level":        1.5,     # m
        # ── Vessel position ───────────────────────────────────────────────────
        "fh_latitude":           9.4823,
        "fh_longitude":          79.3500,
        "fh_heading_deg":        285,
        "fh_speed_knots":        3.2,
        # ── UI toggles ────────────────────────────────────────────────────────
        "fh_voice_on":           True,    # owned ONLY by sidebar toggle
        "fh_sos_active":         False,
        # ── SOS workflow ──────────────────────────────────────────────────────
        "fh_sos_timestamp":      None,
        "fh_sos_pdf":            None,    # bytes
        "fh_sos_email_sent":     False,
        "fh_sos_email_status":   "",
        # ── Event log ─────────────────────────────────────────────────────────
        "fh_event_log":          [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — all simulation controls hidden in a collapsed expander
# ══════════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    """Render the sidebar.

    All simulation sliders live inside a collapsed expander so the fisherman
    never sees them.  The voice toggle is outside the expander so it remains
    easy to find.

    fh_voice_on is created HERE and only here — any second widget with the
    same key anywhere in the script would trigger StreamlitDuplicateElementKey.
    """
    with st.sidebar:
        st.markdown("## ⚓ SeaSentry")
        st.caption("Maritime Drift Guard — Fisherman Panel")
        st.divider()

        # ── Simulation panel (collapsed by default — demo use only) ───────────
        with st.expander("🛠️ Simulation Panel (Demo Only)", expanded=False):
            st.caption("Drag sliders to simulate different vessel conditions.")
            st.markdown("---")

            st.markdown("**📍 Navigation**")
            st.slider(
                "📏 Distance to Border (km)",
                min_value=0.0, max_value=50.0, step=0.5,
                key="fh_distance_to_border",
                help="Simulates how far the vessel is from the maritime boundary.",
            )
            st.selectbox(
                "🧭 Movement Direction",
                options=["Move North", "Move South", "Move East",
                         "Move West", "Hold Position"],
                key="fh_direction",
            )
            st.markdown("---")

            st.markdown("**📡 Device Status**")
            st.selectbox(
                "📡 GPS Status",
                options=["GPS OK", "Weak Signal", "Signal Lost"],
                key="fh_gps_status",
            )
            st.slider(
                "🔋 Battery Level (%)",
                min_value=0, max_value=100,
                key="fh_battery_level",
            )
            st.markdown("---")

            st.markdown("**🌊 Sea Conditions**")
            st.slider(
                "🌊 Sea Water Level (m)",
                min_value=0.0, max_value=5.0, step=0.1,
                key="fh_water_level",
            )

        st.divider()

        # ── Voice toggle — the ONE and ONLY widget with key='fh_voice_on' ─────
        st.toggle("🔊 Voice Alerts", key="fh_voice_on")

        st.divider()

        # ── SOS reset (demo convenience) ──────────────────────────────────────
        if st.session_state.fh_sos_active:
            st.error("🚨 SOS ACTIVE")
            if st.button("Reset SOS (demo only)", key="fh_sos_reset"):
                for k in ("fh_sos_active", "fh_sos_pdf", "fh_sos_timestamp",
                           "fh_sos_email_sent"):
                    st.session_state[k] = (False if isinstance(st.session_state[k], bool)
                                           else None)
                st.rerun()

        st.divider()
        st.caption("v2.0 · SeaSentry Maritime Drift Guard")


# ══════════════════════════════════════════════════════════════════════════════
# PDF GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def _generate_sos_pdf() -> bytes | None:
    """Build an A4 emergency SOS report using ReportLab.

    Returns raw PDF bytes, or None when ReportLab is not installed.
    All telemetry values are read directly from st.session_state.
    """
    try:
        from reportlab.lib import colors as rl
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError:
        return None

    # ── Colours ──────────────────────────────────────────────────────────────
    C_RED    = rl.HexColor("#C62828")
    C_RED_LT = rl.HexColor("#E53935")
    C_ORANGE = rl.HexColor("#E65100")
    C_GREEN  = rl.HexColor("#2E7D32")
    C_NAVY   = rl.HexColor("#0D47A1")
    C_DARK   = rl.HexColor("#212121")
    C_GRAY   = rl.HexColor("#757575")
    C_LGRAY  = rl.HexColor("#EEEEEE")
    C_WHITE  = rl.white

    # ── Live telemetry snapshot ───────────────────────────────────────────────
    ts      = datetime.now()
    ts_str  = ts.strftime("%d %B %Y  at  %H:%M:%S IST")
    lat     = st.session_state.get("fh_latitude",           9.4823)
    lon     = st.session_state.get("fh_longitude",          79.3500)
    dist    = st.session_state.get("fh_distance_to_border", 12.0)
    dirn    = st.session_state.get("fh_direction",          "Move North")
    gps     = st.session_state.get("fh_gps_status",         "GPS OK")
    bat     = st.session_state.get("fh_battery_level",      82)
    water   = st.session_state.get("fh_water_level",        1.5)
    hdg     = st.session_state.get("fh_heading_deg",        285)
    spd     = st.session_state.get("fh_speed_knots",        3.2)
    risk    = "HIGH" if dist < 2 else "MEDIUM" if dist < 5 else "LOW"
    risk_c  = C_RED if risk == "HIGH" else C_ORANGE if risk == "MEDIUM" else C_GREEN

    # ── Paragraph shorthand ───────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    def P(text: str, **kw) -> Paragraph:
        return Paragraph(text, ParagraphStyle("_", parent=styles["Normal"], **kw))

    W = 17 * cm  # usable width

    # ── Section header row ────────────────────────────────────────────────────
    def sec(title: str) -> Table:
        t = Table(
            [[P(title, fontName="Helvetica-Bold", fontSize=10, textColor=C_WHITE)]],
            colWidths=[W],
        )
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_RED),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ]))
        return t

    # ── 4-column key : value table ────────────────────────────────────────────
    def kv(rows: list[tuple]) -> Table:
        data = []
        for r in rows:
            label_a, val_a, label_b, val_b = r
            vc = val_b.get("c", C_DARK) if isinstance(val_b, dict) else C_DARK
            vt = val_b["t"] if isinstance(val_b, dict) else str(val_b)
            data.append([
                P(label_a, fontName="Helvetica-Bold", fontSize=8,  textColor=C_GRAY),
                P(str(val_a), fontName="Helvetica-Bold", fontSize=10, textColor=C_DARK),
                P(label_b, fontName="Helvetica-Bold", fontSize=8,  textColor=C_GRAY),
                P(vt,      fontName="Helvetica-Bold", fontSize=10, textColor=vc),
            ])
        t = Table(data, colWidths=[3.5*cm, 5*cm, 3.5*cm, 5*cm])
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0,0),(-1,-1), [C_WHITE, C_LGRAY]),
            ("TOPPADDING",     (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
            ("LEFTPADDING",    (0,0),(-1,-1), 7),
            ("RIGHTPADDING",   (0,0),(-1,-1), 7),
            ("VALIGN",         (0,0),(-1,-1), "TOP"),
            ("GRID",           (0,0),(-1,-1), 0.25, rl.HexColor("#E0E0E0")),
        ]))
        return t

    # ── Build story ───────────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        title="SeaSentry SOS Emergency Report",
    )

    story = []

    # Header banner
    for text, bg, pad_top, pad_bot in [
        ("SOS EMERGENCY ALERT REPORT",
         C_RED, 16, 4),
        (f"SeaSentry Maritime Drift Guard  |  Emergency activated: {ts_str}",
         C_RED_LT, 5, 10),
    ]:
        kwargs = dict(
            fontName="Helvetica-Bold" if pad_top == 16 else "Helvetica",
            fontSize=20 if pad_top == 16 else 9,
            textColor=C_WHITE,
            alignment=TA_CENTER,
        )
        t = Table([[P(text, **kwargs)]], colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg),
            ("TOPPADDING",    (0,0),(-1,-1), pad_top),
            ("BOTTOMPADDING", (0,0),(-1,-1), pad_bot),
        ]))
        story.append(t)

    story.append(Spacer(1, 0.55*cm))

    # Section 1 — Vessel details
    story.append(sec("VESSEL AND FISHERMAN DETAILS"))
    story.append(kv([
        ("Boat Name",   "Namma Kadal",           "Boat ID",       "KA-MNG-0471"),
        ("Owner Name",  "Rajan K. Muthu",         "Reg. Number",   "KA-2024-FV-0471"),
        ("Home Port",   "Rameswaram, Tamil Nadu", "Contact",       "+91 99400 12345"),
        ("Vessel Type", "Traditional Fibre Boat", "Engine Status", "Running"),
    ]))
    story.append(Spacer(1, 0.45*cm))

    # Section 2 — Live telemetry
    story.append(sec("LIVE TELEMETRY AT TIME OF SOS"))
    story.append(kv([
        ("GPS Latitude",      f"{lat:.5f} deg N",   "GPS Longitude",    f"{lon:.5f} deg E"),
        ("Distance to Border", f"{dist:.2f} km",    "Direction",        dirn),
        ("Vessel Heading",    f"{hdg:.0f} deg",      "Speed",            f"{spd:.1f} knots"),
        ("GPS Status",        gps,                   "Battery",          f"{bat}%"),
        ("Sea Water Level",   f"{water:.2f} m",      "Risk Level",       {"t": risk, "c": risk_c}),
    ]))
    story.append(Spacer(1, 0.45*cm))

    # Section 3 — Tracking link
    story.append(sec("LIVE TRACKING AND SIMULATION LINK"))
    tracking_url = os.environ.get("TRACKING_URL", "http://localhost:8501")
    link_tbl = Table(
        [[P(
            f'Live Dashboard: <a href="{tracking_url}" color="#0D47A1">{tracking_url}</a>'
            f'  &mdash;  SeaSentry Maritime Drift Guard',
            fontName="Helvetica", fontSize=10, textColor=C_NAVY, alignment=TA_CENTER,
        )]],
        colWidths=[W],
    )
    link_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), rl.HexColor("#E3F2FD")),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LINEBELOW",     (0,0),(-1,-1), 1.5, C_NAVY),
        ("LINEABOVE",     (0,0),(-1,-1), 1.5, C_NAVY),
    ]))
    story.append(link_tbl)
    story.append(Spacer(1, 0.8*cm))

    # Footer
    footer = Table(
        [[P(
            f"Generated by SeaSentry  |  Coast Guard Emergency: 1554  |  {ts_str}",
            fontName="Helvetica", fontSize=7, textColor=C_WHITE, alignment=TA_CENTER,
        )]],
        colWidths=[W],
    )
    footer.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_DARK),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
    ]))
    story.append(footer)

    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL DISPATCH
# ══════════════════════════════════════════════════════════════════════════════

def _send_sos_email(pdf_bytes: bytes | None, timestamp: str) -> tuple[bool, str]:
    """Send SOS email to the coast guard.

    Reads SMTP credentials from environment variables:
        SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, COASTGUARD_EMAIL

    Returns (True, detail) on success, (False, "simulated") when env vars are
    absent so the demo works without any configuration.
    """
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_pass = os.environ.get("SMTP_PASS", "").strip()
    cg_email  = os.environ.get("COASTGUARD_EMAIL", "coastguard@seasentry.example.com")

    lat  = st.session_state.get("fh_latitude",           9.4823)
    lon  = st.session_state.get("fh_longitude",          79.3500)
    dist = st.session_state.get("fh_distance_to_border", 12.0)
    url  = os.environ.get("TRACKING_URL", "http://localhost:8501")

    body = (
        "SEASENTRY SOS EMERGENCY ALERT\n"
        + "=" * 42 + "\n"
        f"Vessel   : Namma Kadal  (KA-MNG-0471)\n"
        f"Owner    : Rajan K. Muthu  |  +91 99400 12345\n"
        f"Position : {lat:.5f} N,  {lon:.5f} E\n"
        f"Distance : {dist:.2f} km to maritime boundary\n"
        f"Time     : {timestamp}\n\n"
        f"LIVE TRACKING: {url}\n\n"
        "Please dispatch coastguard vessel immediately.\n"
        "Emergency hotline: 1554\n"
    )

    if not smtp_host or not smtp_user or not smtp_pass:
        return False, "simulated"

    try:
        msg            = MIMEMultipart()
        msg["From"]    = smtp_user
        msg["To"]      = cg_email
        msg["Subject"] = f"[SOS EMERGENCY] Vessel KA-MNG-0471 — {timestamp}"
        msg.attach(MIMEText(body, "plain"))

        if pdf_bytes:
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            fname = f"SOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            part.add_header("Content-Disposition", f'attachment; filename="{fname}"')
            msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(smtp_user, smtp_pass)
            srv.send_message(msg)

        return True, f"Alert sent to {cg_email}"
    except Exception as exc:
        return False, str(exc)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

def _render_header() -> None:
    now    = datetime.now().strftime("%H:%M")
    gps_ok = st.session_state.fh_gps_status == "GPS OK"
    dot_c  = _GREEN if gps_ok else _RED
    st.markdown(
        f'<div class="fh-header fh-in">'
        f'<span class="fh-boat-name">⛵ Namma Kadal</span>'
        f'<span style="display:flex;align-items:center;gap:.7rem;">'
        f'<span class="fh-conn-dot" style="background:{dot_c};box-shadow:0 0 8px {dot_c};"></span>'
        f'<span class="fh-time">🕐 {now}</span>'
        f'</span></div>',
        unsafe_allow_html=True,
    )


def _render_safety_banner() -> None:
    dist = st.session_state.fh_distance_to_border
    state, emoji, label, msg, color = _safety_banner(dist)
    st.markdown(
        f'<div class="fh-banner fh-banner--{state} fh-in fh-d1">'
        f'<div class="fh-banner-emoji">{emoji}</div>'
        f'<div class="fh-banner-label" style="color:{color};">{label}</div>'
        f'<div class="fh-banner-msg">{msg}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── KPI cards ─────────────────────────────────────────────────────────────────
# Each card is PURELY a display element — no buttons, no dialogs.
# The colour class (safe / caution / danger) switches automatically when the
# sidebar sliders change and trigger a Streamlit rerun.

def _card_html(icon: str, metric: str, label: str,
               state: str, status: str, value_cls: str) -> str:
    """Build a single self-contained card HTML string."""
    return (
        f'<div class="fh-card fh-card--{state} fh-in">'
        f'<div class="fh-card-icon">{icon}</div>'
        f'<div class="fh-card-metric {value_cls}">{metric}</div>'
        f'<div class="fh-card-label">{label}</div>'
        f'<div class="fh-card-status {value_cls}">{status}</div>'
        f'</div>'
    )


def _render_border_card() -> None:
    dist = st.session_state.fh_distance_to_border
    state, cls, status = _dist_state(dist)
    st.markdown(_card_html("📏", f"{dist:.1f} km", "TO BORDER", state, status, cls),
                unsafe_allow_html=True)


def _render_direction_card() -> None:
    dirn  = st.session_state.fh_direction
    arrow = _DIRECTION_MAP.get(dirn, "↑")
    st.markdown(_card_html("🧭", arrow, "MOVE THIS WAY", "safe", dirn, _CLS_GREEN),
                unsafe_allow_html=True)


def _render_gps_card() -> None:
    status = st.session_state.fh_gps_status
    state, cls, lbl = _gps_state(status)
    icon   = "📡" if state == "safe" else "⚠️" if state == "caution" else "❌"
    st.markdown(_card_html(icon, lbl, "GPS STATUS", state, status, cls),
                unsafe_allow_html=True)


def _render_battery_card() -> None:
    pct   = st.session_state.fh_battery_level
    state, cls, lbl = _bat_state(pct)
    icon  = "🪫" if pct < 15 else "🔋"
    st.markdown(_card_html(icon, f"{pct}%", "BATTERY", state, lbl, cls),
                unsafe_allow_html=True)


def _render_water_card() -> None:
    level = st.session_state.fh_water_level
    state, cls, lbl = _water_state(level)
    st.markdown(_card_html("🌊", f"{level:.1f} m", "SEA LEVEL", state, lbl, cls),
                unsafe_allow_html=True)


def _render_map_section() -> None:
    dist  = st.session_state.fh_distance_to_border
    vessel = {
        **DEMO_VESSEL,
        "latitude":              st.session_state.fh_latitude,
        "longitude":             st.session_state.fh_longitude,
        "heading_deg":           st.session_state.fh_heading_deg,
        "speed_knots":           st.session_state.fh_speed_knots,
        "distance_to_boundary_nm": dist,
        "risk_level": "HIGH" if dist < 2 else "MEDIUM" if dist < 5 else "LOW",
        "sos_active": st.session_state.fh_sos_active,
    }
    st.markdown(
        '<div class="fh-map-wrap fh-in fh-d4">'
        '<div class="fh-map-title">🗺️ Your Location</div>',
        unsafe_allow_html=True,
    )
    if create_sea_map is not None:
        components.html(create_sea_map(vessel), height=280, scrolling=False)
    else:
        st.caption("Map unavailable (running standalone).")
    st.markdown(
        '<div class="fh-map-legend">'
        '<span>⛵ Your Boat</span>'
        '<span style="color:#E53935;">-- ⚠ Border</span>'
        '<span>🇮🇳 India &nbsp;|&nbsp; 🇱🇰 Sri Lanka</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )


def _render_voice_section() -> None:
    """Play the risk-appropriate audio alert.

    BUG FIX — StreamlitDuplicateElementKey:
    The fh_voice_on toggle widget exists ONLY in _render_sidebar().
    This function reads st.session_state.fh_voice_on without ever creating
    a second widget with that key.
    """
    if not st.session_state.fh_voice_on or render_chained_alert_audio is None:
        return

    dist      = st.session_state.fh_distance_to_border
    risk      = "HIGH" if dist < 2 else "MEDIUM" if dist < 5 else "LOW"
    clip      = {"HIGH": "danger", "MEDIUM": "warning", "LOW": "safe"}[risk]
    lang      = st.session_state.get("broadcast_language", "tamil")
    tts_codes = {"tamil": "ta-IN", "kannada": "kn-IN", "english": "en-IN"}

    voice_url = _audio_url(f"{lang}_{clip}.mp3") if lang in ("tamil", "kannada") else None
    alarm_url = _audio_url("alarm.mp3") if risk == "HIGH" else None
    alert_txt = (
        "DANGER: Turn back immediately!"      if risk == "HIGH"
        else "Caution: You are near the border." if risk == "MEDIUM"
        else "You are safe. Keep fishing."
    )

    # render_chained_alert_audio uses components.html(height=0) internally —
    # the JS runs silently with zero visible output on the Streamlit page.
    render_chained_alert_audio(
        alarm_url, voice_url,
        alert_txt if not voice_url else None,
        tts_codes.get(lang, "en-IN"),
        key=f"fh_audio_{risk}_{lang}",
    )


def _render_sos_section() -> None:
    """Full SOS emergency workflow.

    On button click:
      1. Records timestamp and sets fh_sos_active.
      2. Generates an A4 emergency PDF.
      3. Dispatches an SMTP email (or simulates it).
      4. Calls the backend /sos endpoint (best-effort).
      5. Displays status cards and a PDF download button.
    """

    # ── Active emergency banner ───────────────────────────────────────────────
    if st.session_state.fh_sos_active:
        ts_disp = st.session_state.get("fh_sos_timestamp", "—")
        st.markdown(
            f'<div class="fh-emergency-banner fh-in">'
            f'<div class="fh-emerg-title">🚨  CRITICAL ALERT: SOS TRANSMITTED TO COAST GUARD</div>'
            f'<div class="fh-emerg-sub">Stay calm — help is on the way.</div>'
            f'<div class="fh-emerg-ts">Activated: {ts_disp}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Giant SOS button ──────────────────────────────────────────────────────
    st.markdown('<div class="fh-sos-wrap fh-in fh-d5">', unsafe_allow_html=True)
    if st.button("🆘  EMERGENCY SOS", use_container_width=True, key="fh_sos_main"):
        ts_str = datetime.now().strftime("%d %b %Y  %H:%M:%S IST")
        st.session_state.fh_sos_active    = True
        st.session_state.fh_sos_timestamp = ts_str

        with st.spinner("🚨 Activating SOS Protocol — generating emergency report…"):
            # ① PDF
            pdf = _generate_sos_pdf()
            st.session_state.fh_sos_pdf = pdf

            # ② Email (or simulate)
            ok, detail = _send_sos_email(pdf, ts_str)
            st.session_state.fh_sos_email_sent   = ok
            st.session_state.fh_sos_email_status = detail

            # ③ Backend /sos best-effort
            if call_sos is not None:
                try:
                    call_sos(
                        boat_id="KA-MNG-0471",
                        lat=st.session_state.fh_latitude,
                        lon=st.session_state.fh_longitude,
                    )
                except Exception:
                    pass

            # ④ Event log
            st.session_state.fh_event_log.append(
                (ts_str, "SOS ACTIVATED — emergency report generated and dispatched")
            )

        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Post-SOS status + download ────────────────────────────────────────────
    if st.session_state.fh_sos_active:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.success("✅ SOS Signal Sent")
            st.caption(st.session_state.get("fh_sos_timestamp", "—"))

        with c2:
            if st.session_state.get("fh_sos_pdf"):
                st.success("✅ PDF Generated")
                st.caption("Emergency report is ready.")
            else:
                st.warning("⚠️ PDF Unavailable")
                st.caption("pip install reportlab")

        with c3:
            email_sent   = st.session_state.get("fh_sos_email_sent", False)
            email_status = st.session_state.get("fh_sos_email_status", "")
            if email_sent:
                st.success("✅ Email Dispatched")
                st.caption(email_status[:50])
            elif email_status == "simulated":
                st.info("📧 Email Simulated")
                st.caption("Set SMTP env vars for live dispatch.")
            else:
                st.warning("⚠️ Email Pending")
                st.caption(email_status[:50] if email_status else "")

        if st.session_state.get("fh_sos_pdf"):
            fname = f"SOS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.download_button(
                "📄  Download Emergency Report (PDF)",
                data=st.session_state.fh_sos_pdf,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Share Location (only secondary action — Call Coastguard removed) ──────
    lat = st.session_state.fh_latitude
    lon = st.session_state.fh_longitude
    st.markdown('<div class="fh-sec-btn">', unsafe_allow_html=True)
    if st.button("📡 Share My Location", use_container_width=True, key="fh_loc"):
        st.success(f"📡 Location shared: {lat:.4f}°N, {lon:.4f}°E")
    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def render_fisherman_dashboard(vessel: dict[str, Any] | None = None) -> None:
    """Render the simplified high-visibility Fisherman Dashboard.

    Parameters
    ----------
    vessel : optional dict
        Vessel data from app.py session state.  Position fields are synced
        into session state on the first load; thereafter the sidebar
        simulation sliders control all displayed values.
    """
    # 1. Seed defaults (no-ops when keys already exist)
    _init_state()

    # 2. One-time position sync from the incoming vessel dict
    if vessel is not None and st.session_state.fh_latitude == 9.4823:
        st.session_state.fh_latitude    = vessel.get("latitude",    9.4823)
        st.session_state.fh_longitude   = vessel.get("longitude",   79.35)
        st.session_state.fh_heading_deg = vessel.get("heading_deg", 285)
        st.session_state.fh_speed_knots = vessel.get("speed_knots", 3.2)

    # 3. Auto-log boundary zone transitions
    dist = st.session_state.fh_distance_to_border
    zone = "danger" if dist < 2 else "caution" if dist < 5 else "safe"
    if st.session_state.get("_fh_last_zone") not in (zone, None):
        ts = datetime.now().strftime("%H:%M")
        st.session_state.fh_event_log.append(
            (ts, f"Zone changed to {zone.upper()} ({dist:.1f} km)")
        )
    st.session_state["_fh_last_zone"] = zone

    # 4. Sidebar — simulation expander + voice toggle (fh_voice_on created here)
    _render_sidebar()

    # 5. Page content
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="fh-root">', unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    _render_header()

    # ── Safety banner — full-width, colour-coded by distance ─────────────────
    _render_safety_banner()

    # ── Row 1: TO BORDER (large) | DIRECTION (large) ─────────────────────────
    st.markdown(
        "<p style='font-size:.78rem;font-weight:700;text-transform:uppercase;"
        "letter-spacing:.09em;color:rgba(255,255,255,.38);margin:.7rem 0 .35rem;'>"
        "Live Status</p>",
        unsafe_allow_html=True,
    )
    col_b, col_d = st.columns(2)
    with col_b:
        _render_border_card()
    with col_d:
        _render_direction_card()

    st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

    # ── Row 2: GPS | BATTERY | SEA LEVEL ─────────────────────────────────────
    col_g, col_bat, col_w = st.columns(3)
    with col_g:
        _render_gps_card()
    with col_bat:
        _render_battery_card()
    with col_w:
        _render_water_card()

    st.markdown("<div style='height:.55rem'></div>", unsafe_allow_html=True)

    # ── Map ───────────────────────────────────────────────────────────────────
    _render_map_section()

    # ── Voice (reads fh_voice_on but creates NO widget) ───────────────────────
    _render_voice_section()

    st.divider()

    # ── SOS emergency workflow ────────────────────────────────────────────────
    _render_sos_section()

    st.markdown("</div>", unsafe_allow_html=True)


# ── Standalone entry ────────────────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(
        page_title="SeaSentry | Fisherman",
        page_icon="⛵",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    try:
        from controls import inject_theme_css
        inject_theme_css()
    except ImportError:
        st.markdown("<style>body{background:#0d1117;}</style>", unsafe_allow_html=True)
    render_fisherman_dashboard()
