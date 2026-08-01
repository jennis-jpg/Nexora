"""SeaSentry — Fisherman Dashboard.

Designed for low-literacy, elderly fishermen:
  • Large icons and colour coding replace numeric labels wherever possible.
  • Minimal text; every status communicated in one short sentence.
  • All interactive elements are oversized and easy to tap.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from controls import COLORS, DEMO_VESSEL, RISK_STYLES


# ── CSS ────────────────────────────────────────────────────────────────────────

FISHERMAN_CSS = f"""
<style>
/* ── Base overrides for fisherman view ─────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

/* Larger base font for readability */
.fisherman-root {{
    font-family: 'Inter', sans-serif;
    color: #fff;
}}

/* ─────────── TOP HEADER ──────────────────────────────────────────────── */
.fh-header {{
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 1rem;
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 22px;
    padding: 1rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}}

.fh-boat-info {{
    display: flex;
    align-items: center;
    gap: 1rem;
}}

.fh-boat-icon {{
    font-size: 2.4rem;
    line-height: 1;
    filter: drop-shadow(0 2px 8px rgba(77,182,255,0.5));
}}

.fh-boat-name {{
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fff, {COLORS["sky"]});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.15;
}}

.fh-boat-id {{
    font-size: 0.82rem;
    font-weight: 600;
    color: rgba(255,255,255,0.5);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}

.fh-status-row {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    flex-wrap: wrap;
    justify-content: flex-end;
}}

.fh-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.42rem 0.9rem;
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    white-space: nowrap;
}}

.fh-pill-green {{
    background: rgba(46,204,113,0.15);
    border: 1.5px solid rgba(46,204,113,0.45);
    color: {COLORS["green"]};
}}

.fh-pill-orange {{
    background: rgba(255,152,0,0.15);
    border: 1.5px solid rgba(255,152,0,0.45);
    color: {COLORS["orange"]};
}}

.fh-pill-red {{
    background: rgba(229,57,53,0.15);
    border: 1.5px solid rgba(229,57,53,0.45);
    color: {COLORS["red"]};
}}

.fh-pill-blue {{
    background: rgba(77,182,255,0.15);
    border: 1.5px solid rgba(77,182,255,0.4);
    color: {COLORS["sky"]};
}}

.fh-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    animation: fh-blink 2s ease-in-out infinite;
}}

.fh-time {{
    font-size: 1.05rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    color: rgba(255,255,255,0.85);
}}

/* ─────────── SAFETY BANNER ────────────────────────────────────────────── */
.fh-banner {{
    border-radius: 22px;
    padding: 1.35rem 1.75rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1.25rem;
    box-shadow: 0 8px 40px rgba(0,0,0,0.3);
    transition: background 0.5s ease, box-shadow 0.5s ease;
    border: 2px solid transparent;
}}

.fh-banner--safe {{
    background: linear-gradient(135deg, rgba(46,204,113,0.22), rgba(0,194,168,0.15));
    border-color: rgba(46,204,113,0.5);
    box-shadow: 0 8px 40px rgba(46,204,113,0.2);
}}

.fh-banner--caution {{
    background: linear-gradient(135deg, rgba(255,152,0,0.22), rgba(255,193,7,0.12));
    border-color: rgba(255,152,0,0.55);
    box-shadow: 0 8px 40px rgba(255,152,0,0.2);
    animation: fh-pulse-orange 2.5s ease-in-out infinite;
}}

.fh-banner--danger {{
    background: linear-gradient(135deg, rgba(229,57,53,0.28), rgba(183,28,28,0.2));
    border-color: rgba(229,57,53,0.6);
    box-shadow: 0 8px 40px rgba(229,57,53,0.25);
    animation: fh-pulse-red 2s ease-in-out infinite;
}}

@keyframes fh-pulse-orange {{
    0%, 100% {{ box-shadow: 0 8px 40px rgba(255,152,0,0.2); }}
    50% {{ box-shadow: 0 8px 60px rgba(255,152,0,0.45); }}
}}

@keyframes fh-pulse-red {{
    0%, 100% {{ box-shadow: 0 8px 40px rgba(229,57,53,0.25); }}
    50% {{ box-shadow: 0 8px 64px rgba(229,57,53,0.6); }}
}}

.fh-banner-emoji {{
    font-size: 3.5rem;
    line-height: 1;
    flex-shrink: 0;
}}

.fh-banner-text {{
    flex: 1;
}}

.fh-banner-status {{
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.02em;
    line-height: 1.1;
}}

.fh-banner-sub {{
    font-size: 1.05rem;
    font-weight: 600;
    margin-top: 0.2rem;
    opacity: 0.85;
}}

/* ─────────── SECTION HEADER ───────────────────────────────────────────── */
.fh-section-title {{
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    margin: 0.25rem 0 0.65rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}}

.fh-section-title span {{ color: {COLORS["sky"]}; font-size: 0.85rem; }}

/* ─────────── BOAT STATUS CARDS ─────────────────────────────────────────── */
.fh-stat-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.65rem;
    margin-bottom: 1rem;
}}

.fh-stat-card {{
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 18px;
    padding: 1rem 0.9rem;
    text-align: center;
    transition: transform 0.22s ease, border-color 0.22s ease;
}}

.fh-stat-card:hover {{
    transform: translateY(-3px);
    border-color: rgba(77,182,255,0.35);
}}

.fh-stat-icon {{ font-size: 1.65rem; line-height: 1; margin-bottom: 0.35rem; }}
.fh-stat-label {{
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    margin-bottom: 0.35rem;
}}
.fh-stat-value {{
    font-size: 1.25rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.01em;
    line-height: 1.15;
}}
.fh-stat-unit {{
    font-size: 0.68rem;
    font-weight: 600;
    color: rgba(255,255,255,0.45);
    margin-top: 0.1rem;
}}

/* ─────────── WEATHER PANEL ─────────────────────────────────────────────── */
.fh-weather-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.65rem;
    margin-bottom: 1rem;
}}

.fh-weather-card {{
    background: rgba(0,91,150,0.18);
    border: 1px solid rgba(77,182,255,0.18);
    border-radius: 16px;
    padding: 0.9rem 0.75rem;
    text-align: center;
}}

.fh-weather-icon {{ font-size: 1.9rem; margin-bottom: 0.25rem; line-height: 1; }}
.fh-weather-label {{
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.42);
    margin-bottom: 0.3rem;
}}
.fh-weather-value {{
    font-size: 1.1rem;
    font-weight: 800;
    color: {COLORS["sky"]};
}}

/* ─────────── WATER LEVEL CARD ──────────────────────────────────────────── */
.fh-water-card {{
    border-radius: 22px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    border: 2px solid transparent;
    transition: all 0.4s ease;
}}

.fh-water-card--normal {{
    background: linear-gradient(135deg, rgba(46,204,113,0.18), rgba(0,194,168,0.12));
    border-color: rgba(46,204,113,0.45);
}}

.fh-water-card--rising {{
    background: linear-gradient(135deg, rgba(255,152,0,0.2), rgba(255,193,7,0.1));
    border-color: rgba(255,152,0,0.5);
}}

.fh-water-card--rough {{
    background: linear-gradient(135deg, rgba(229,57,53,0.22), rgba(183,28,28,0.15));
    border-color: rgba(229,57,53,0.55);
    animation: fh-pulse-red 2.5s ease-in-out infinite;
}}

.fh-water-emoji {{ font-size: 3rem; flex-shrink: 0; line-height: 1; }}

.fh-water-status {{
    font-size: 1.5rem;
    font-weight: 900;
    letter-spacing: -0.01em;
    line-height: 1.15;
}}

.fh-water-msg {{
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0.25rem;
    opacity: 0.82;
}}

/* ─────────── VOICE SECTION ─────────────────────────────────────────────── */
.fh-voice-card {{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 1rem;
}}

/* ─────────── EMERGENCY PANEL ───────────────────────────────────────────── */
.fh-emergency-card {{
    background: rgba(229,57,53,0.1);
    border: 2px solid rgba(229,57,53,0.4);
    border-radius: 22px;
    padding: 1.25rem 1.4rem;
    margin-bottom: 1rem;
    animation: fh-pulse-red-border 3s ease-in-out infinite;
}}

@keyframes fh-pulse-red-border {{
    0%, 100% {{ border-color: rgba(229,57,53,0.4); }}
    50% {{ border-color: rgba(229,57,53,0.75); }}
}}

/* SOS button override */
.fh-sos-wrapper .stButton > button {{
    background: linear-gradient(135deg, #E53935, #b71c1c) !important;
    border: none !important;
    border-radius: 18px !important;
    font-size: 1.6rem !important;
    font-weight: 900 !important;
    padding: 1rem 1rem !important;
    letter-spacing: 0.04em !important;
    box-shadow: 0 6px 30px rgba(229,57,53,0.55) !important;
    animation: fh-sos-pulse 2s ease-in-out infinite !important;
    min-height: 80px !important;
    color: #fff !important;
}}

@keyframes fh-sos-pulse {{
    0%, 100% {{ box-shadow: 0 6px 30px rgba(229,57,53,0.45); }}
    50% {{ box-shadow: 0 6px 55px rgba(229,57,53,0.85); }}
}}

/* Secondary emergency buttons */
.fh-sos-secondary .stButton > button {{
    background: rgba(255,255,255,0.09) !important;
    border: 1.5px solid rgba(255,255,255,0.2) !important;
    border-radius: 14px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    padding: 0.75rem 1rem !important;
    color: #fff !important;
    box-shadow: none !important;
    min-height: 60px !important;
}}

/* ─────────── ALERTS TIMELINE ───────────────────────────────────────────── */
.fh-alert-item {{
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    padding: 0.9rem 1rem;
    border-radius: 14px;
    margin-bottom: 0.6rem;
    border-left: 4px solid transparent;
}}

.fh-alert-item--danger {{
    background: rgba(229,57,53,0.1);
    border-left-color: {COLORS["red"]};
}}

.fh-alert-item--caution {{
    background: rgba(255,152,0,0.1);
    border-left-color: {COLORS["orange"]};
}}

.fh-alert-item--safe {{
    background: rgba(46,204,113,0.08);
    border-left-color: {COLORS["green"]};
}}

.fh-alert-icon {{ font-size: 1.35rem; flex-shrink: 0; margin-top: 0.05rem; }}
.fh-alert-msg {{ font-size: 0.95rem; font-weight: 600; color: rgba(255,255,255,0.88); line-height: 1.45; }}
.fh-alert-time {{ font-size: 0.68rem; font-weight: 600; color: rgba(255,255,255,0.38); margin-top: 0.25rem; }}

/* ─────────── GLASS CARD BASE ───────────────────────────────────────────── */
.fh-glass {{
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 20px;
    padding: 1.15rem 1.3rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.22);
}}

/* ─────────── ANIMATIONS ─────────────────────────────────────────────────── */
@keyframes fh-blink {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.3; }}
}}

@keyframes fh-slide-up {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.fh-animate {{ animation: fh-slide-up 0.5s ease-out both; }}
.fh-d1 {{ animation-delay: 0.05s; }}
.fh-d2 {{ animation-delay: 0.12s; }}
.fh-d3 {{ animation-delay: 0.2s; }}
.fh-d4 {{ animation-delay: 0.28s; }}
.fh-d5 {{ animation-delay: 0.36s; }}
.fh-d6 {{ animation-delay: 0.44s; }}
.fh-d7 {{ animation-delay: 0.52s; }}

/* Streamlit selectbox + toggle overrides */
div[data-testid="stSelectbox"] label,
div[data-testid="stToggle"] label {{
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: rgba(255,255,255,0.82) !important;
}}

div[data-testid="stSelectbox"] > div > div {{
    background: rgba(0,0,0,0.25) !important;
    border: 1.5px solid rgba(77,182,255,0.3) !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}}
</style>
"""


# ── Helper: cardinal from degrees ────────────────────────────────────────────

def _cardinal(deg: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[round(deg / 45) % 8]


# ── Map ───────────────────────────────────────────────────────────────────────

def _build_fisherman_map(vessel: dict[str, Any]) -> folium.Map:
    """Folium map tuned for fisherman view: big icons, clear colour coding."""
    lat = float(vessel["latitude"])
    lon = float(vessel["longitude"])
    heading_deg = float(vessel.get("heading_deg", 0))
    risk_level = vessel.get("risk_level", "LOW")
    risk = RISK_STYLES.get(risk_level, RISK_STYLES["LOW"])

    m = folium.Map(location=[lat, lon], zoom_start=10, tiles=None)

    # Dark sea base layer
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap &copy; CARTO",
        name="Dark Sea",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    # Maritime boundary (dashed red)
    boundary_coords = [
        [lat - 0.6, lon + 0.05],
        [lat,       lon + 0.03],
        [lat + 0.6, lon + 0.01],
    ]
    folium.PolyLine(
        locations=boundary_coords,
        color="#E53935",
        weight=4,
        dash_array="10, 8",
        tooltip="⚠ Maritime Boundary — Do Not Cross",
    ).add_to(m)

    # International waters shading
    intl_poly = [
        [lat - 0.6, lon + 0.05],
        [lat,       lon + 0.03],
        [lat + 0.6, lon + 0.01],
        [lat + 0.6, lon + 0.9],
        [lat - 0.6, lon + 0.9],
    ]
    folium.Polygon(
        locations=intl_poly,
        color="#E53935",
        weight=1,
        fill=True,
        fill_color="#E53935",
        fill_opacity=0.12,
        tooltip="International Waters — Danger Zone",
    ).add_to(m)

    # Past/crossed route (red)  — placeholder: 0.06° behind heading
    heading_rad = math.radians(heading_deg)
    past_lat = lat - 0.06 * math.cos(heading_rad)
    past_lon = lon - 0.06 * math.sin(heading_rad)
    folium.PolyLine(
        locations=[[past_lat, past_lon], [lat, lon]],
        color="#FF5252",
        weight=3,
        tooltip="Route Already Travelled",
    ).add_to(m)

    # Predicted future route (blue)
    if "pred_latitude" in vessel and "pred_longitude" in vessel:
        pred_lat = float(vessel["pred_latitude"])
        pred_lon = float(vessel["pred_longitude"])
    else:
        pred_lat = lat + 0.12 * math.cos(heading_rad)
        pred_lon = lon + 0.12 * math.sin(heading_rad)

    folium.PolyLine(
        locations=[[lat, lon], [pred_lat, pred_lon]],
        color="#4DB6FF",
        weight=4,
        dash_array="8, 6",
        tooltip="Predicted Route (next 30 min)",
    ).add_to(m)

    # Midpoint future marker
    mid_lat = (lat + pred_lat) / 2
    mid_lon = (lon + pred_lon) / 2
    folium.CircleMarker(
        location=[mid_lat, mid_lon],
        radius=5,
        color="#4DB6FF",
        fill=True,
        fill_color="#031B34",
        fill_opacity=0.9,
        weight=2,
        tooltip="15 min mark",
    ).add_to(m)

    # Predicted end point marker
    folium.CircleMarker(
        location=[pred_lat, pred_lon],
        radius=7,
        color="#4DB6FF",
        fill=True,
        fill_color="#031B34",
        fill_opacity=0.9,
        weight=2,
        tooltip="Predicted Position in 30 min",
    ).add_to(m)

    # Crossing point marker (where route intersects boundary)
    cross_lat = (lat + pred_lat) * 0.5 + 0.01
    cross_lon = lon + 0.025
    folium.Marker(
        location=[cross_lat, cross_lon],
        icon=folium.DivIcon(
            html="""<div style="
                font-size:1.4rem; line-height:1;
                filter: drop-shadow(0 2px 6px rgba(229,57,53,0.8));
            ">⚠️</div>""",
            icon_size=(28, 28),
            icon_anchor=(14, 14),
        ),
        tooltip="⚠ Predicted Crossing Point",
    ).add_to(m)

    # Danger glow halo around vessel
    folium.Circle(
        location=[lat, lon],
        radius=1500,
        color=risk["color"],
        fill=True,
        fill_color=risk["color"],
        fill_opacity=0.15,
        weight=1,
    ).add_to(m)

    # Boat icon — large, clearly visible
    boat_html = f"""
    <div style="
        position: relative;
        width: 44px; height: 44px;
        display: flex; align-items: center; justify-content: center;
    ">
        <div style="
            position: absolute;
            width: 54px; height: 54px;
            border-radius: 50%;
            background: {risk['color']}33;
            border: 2px solid {risk['color']}88;
            top: -5px; left: -5px;
            animation: none;
        "></div>
        <span style="font-size:2rem; filter: drop-shadow(0 2px 8px {risk['color']});">⛵</span>
    </div>
    """
    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(
            html=boat_html,
            icon_size=(44, 44),
            icon_anchor=(22, 22),
        ),
        tooltip=f"Your Boat — {risk['label']} ⚠" if risk_level != "LOW" else "Your Boat ✓",
        popup=folium.Popup(
            f"<b>⛵ Your Boat</b><br>"
            f"Lat: {lat:.4f}° | Lon: {lon:.4f}°<br>"
            f"Speed: {vessel.get('speed_knots', 0):.1f} kn &nbsp;|&nbsp; "
            f"Heading: {heading_deg:.0f}°<br>"
            f"Status: <b style='color:{risk['color']}'>{risk['label']}</b>",
            max_width=230,
        ),
    ).add_to(m)

    folium.LayerControl(position="topright", collapsed=True).add_to(m)
    return m


# ── Section renderers ─────────────────────────────────────────────────────────

def _render_header(vessel: dict[str, Any]) -> None:
    now = datetime.now().strftime("%H:%M")
    bat = vessel.get("battery_pct", 82)
    gps_ok = vessel.get("gps_ok", True)
    connected = vessel.get("connected", True)

    bat_icon = "🔋" if bat > 50 else "🪫"
    bat_cls = "fh-pill-green" if bat > 50 else ("fh-pill-orange" if bat > 20 else "fh-pill-red")
    gps_cls = "fh-pill-green" if gps_ok else "fh-pill-red"
    conn_cls = "fh-pill-green" if connected else "fh-pill-red"

    st.markdown(
        f"""
        <div class="fh-header fh-animate">
            <div class="fh-boat-info">
                <div class="fh-boat-icon">⛵</div>
                <div>
                    <div class="fh-boat-name">{vessel.get("boat_name", "Namma Kadal")}</div>
                    <div class="fh-boat-id">ID · {vessel.get("boat_id", "KA-MNG-0471")}</div>
                </div>
            </div>
            <div class="fh-status-row">
                <span class="fh-time">🕐 {now}</span>
                <span class="fh-pill {conn_cls}">
                    <span class="fh-dot"></span>
                    {"Online" if connected else "Offline"}
                </span>
                <span class="fh-pill {bat_cls}">{bat_icon} {bat}%</span>
                <span class="fh-pill {gps_cls}">
                    {"📡 GPS OK" if gps_ok else "❌ No GPS"}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_safety_banner(vessel: dict[str, Any]) -> None:
    risk_level = vessel.get("risk_level", "LOW").upper()
    dist = float(vessel.get("distance_to_boundary_nm", 99))

    if risk_level in ("HIGH", "CRITICAL") or dist < 2:
        cls = "fh-banner--danger"
        emoji = "🔴"
        status = "DANGER"
        sub = "Turn back now! You are close to the border."
    elif risk_level == "MEDIUM" or dist < 5:
        cls = "fh-banner--caution"
        emoji = "🟠"
        status = "CAUTION"
        sub = "Watch out — you are getting close to the border."
    else:
        cls = "fh-banner--safe"
        emoji = "🟢"
        status = "SAFE"
        sub = "You are in safe waters. Keep fishing!"

    st.markdown(
        f"""
        <div class="fh-banner {cls} fh-animate fh-d1">
            <div class="fh-banner-emoji">{emoji}</div>
            <div class="fh-banner-text">
                <div class="fh-banner-status">{status}</div>
                <div class="fh-banner-sub">{sub}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_map(vessel: dict[str, Any]) -> None:
    st.markdown(
        '<div class="fh-glass fh-animate fh-d2" style="padding-bottom:0.5rem;">'
        '<div class="fh-section-title"><span>🗺️</span> Live Map — Your Position</div>',
        unsafe_allow_html=True,
    )

    m = _build_fisherman_map(vessel)
    st_folium(m, width="100%", height=420, returned_objects=[], key="fh_map")

    st.markdown(
        f"""
        <div style="display:flex; gap:1.2rem; flex-wrap:wrap; padding:0.6rem 0 0.3rem; font-size:0.78rem; color:rgba(255,255,255,0.6);">
            <span>⛵ <b>Your Boat</b></span>
            <span style="color:{COLORS['sky']}">━━ Predicted Route</span>
            <span style="color:#FF5252">━━ Travelled Route</span>
            <span style="color:{COLORS['red']}">-- Border Line</span>
            <span>⚠️ Crossing Point</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_boat_status(vessel: dict[str, Any]) -> None:
    lat = vessel.get("latitude", 8.5241)
    lon = vessel.get("longitude", 76.9366)
    heading = vessel.get("heading_deg", 285)
    speed = vessel.get("speed_knots", 3.2)
    dist = vessel.get("distance_to_boundary_nm", 1.4)
    eta = vessel.get("eta_to_boundary_min", 38)
    risk = vessel.get("risk_level", "HIGH")

    risk_meta = RISK_STYLES.get(risk.upper(), RISK_STYLES["MEDIUM"])
    risk_color = risk_meta["color"]
    risk_icon = risk_meta["icon"]
    risk_label = risk_meta["label"]

    st.markdown(
        f"""
        <div class="fh-glass fh-animate fh-d3">
        <div class="fh-section-title"><span>📊</span> Boat Status</div>
        <div class="fh-stat-grid">
            <div class="fh-stat-card">
                <div class="fh-stat-icon">📍</div>
                <div class="fh-stat-label">Latitude</div>
                <div class="fh-stat-value">{lat:.3f}°</div>
            </div>
            <div class="fh-stat-card">
                <div class="fh-stat-icon">📍</div>
                <div class="fh-stat-label">Longitude</div>
                <div class="fh-stat-value">{lon:.3f}°</div>
            </div>
            <div class="fh-stat-card">
                <div class="fh-stat-icon">🧭</div>
                <div class="fh-stat-label">Heading</div>
                <div class="fh-stat-value">{heading}°</div>
                <div class="fh-stat-unit">{_cardinal(heading)}</div>
            </div>
            <div class="fh-stat-card">
                <div class="fh-stat-icon">💨</div>
                <div class="fh-stat-label">Speed</div>
                <div class="fh-stat-value">{speed:.1f}</div>
                <div class="fh-stat-unit">knots</div>
            </div>
            <div class="fh-stat-card">
                <div class="fh-stat-icon">📏</div>
                <div class="fh-stat-label">To Border</div>
                <div class="fh-stat-value">{dist:.1f}</div>
                <div class="fh-stat-unit">nm away</div>
            </div>
            <div class="fh-stat-card" style="border-color:{risk_color}55;">
                <div class="fh-stat-icon">{risk_icon}</div>
                <div class="fh-stat-label">Risk</div>
                <div class="fh-stat-value" style="color:{risk_color}; font-size:1rem;">{risk_label}</div>
                <div class="fh-stat-unit">ETA {eta} min</div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_weather(vessel: dict[str, Any]) -> None:
    wind_kn = vessel.get("wind_speed_kn", 12.4)
    wind_dir = vessel.get("wind_direction_deg", 278)
    temp = vessel.get("temperature_c", 28)
    wave_m = vessel.get("wave_height_m", 1.2)
    vis_km = vessel.get("visibility_km", 8)
    rain_pct = vessel.get("rain_chance_pct", 15)

    # wind icon by speed
    if wind_kn >= 20:
        wind_icon, wind_label = "🌪️", f"{wind_kn:.0f} kn"
    elif wind_kn >= 12:
        wind_icon, wind_label = "💨", f"{wind_kn:.0f} kn"
    else:
        wind_icon, wind_label = "🍃", f"{wind_kn:.0f} kn"

    wave_icon = "🌊" if wave_m > 1.5 else "〰️"
    rain_icon = "🌧️" if rain_pct > 50 else ("🌦️" if rain_pct > 20 else "☀️")
    vis_icon = "👁️" if vis_km > 5 else "🌫️"

    st.markdown(
        f"""
        <div class="fh-glass fh-animate fh-d4">
        <div class="fh-section-title"><span>🌤️</span> Weather Right Now</div>
        <div class="fh-weather-grid">
            <div class="fh-weather-card">
                <div class="fh-weather-icon">🌡️</div>
                <div class="fh-weather-label">Temperature</div>
                <div class="fh-weather-value">{temp}°C</div>
            </div>
            <div class="fh-weather-card">
                <div class="fh-weather-icon">{wind_icon}</div>
                <div class="fh-weather-label">Wind Speed</div>
                <div class="fh-weather-value">{wind_label}</div>
            </div>
            <div class="fh-weather-card">
                <div class="fh-weather-icon">🧭</div>
                <div class="fh-weather-label">Wind Direction</div>
                <div class="fh-weather-value">{_cardinal(wind_dir)}</div>
            </div>
            <div class="fh-weather-card">
                <div class="fh-weather-icon">{wave_icon}</div>
                <div class="fh-weather-label">Wave Height</div>
                <div class="fh-weather-value">{wave_m:.1f} m</div>
            </div>
            <div class="fh-weather-card">
                <div class="fh-weather-icon">{vis_icon}</div>
                <div class="fh-weather-label">Visibility</div>
                <div class="fh-weather-value">{vis_km} km</div>
            </div>
            <div class="fh-weather-card">
                <div class="fh-weather-icon">{rain_icon}</div>
                <div class="fh-weather-label">Rain Chance</div>
                <div class="fh-weather-value">{rain_pct}%</div>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_water_level(vessel: dict[str, Any]) -> None:
    dist = float(vessel.get("distance_to_boundary_nm", 5))
    wave_m = float(vessel.get("wave_height_m", 1.2))

    # Determine sea state from wave height + proximity
    if wave_m > 2.0 or dist < 1.5:
        cls = "fh-water-card--rough"
        emoji = "🌊"
        label_text = "Rough Sea"
        sentence = "Dangerous sea conditions"
        color = COLORS["red"]
    elif wave_m > 1.0 or dist < 4:
        cls = "fh-water-card--rising"
        emoji = "🌊"
        label_text = "Rising Sea"
        sentence = "Sea becoming rough"
        color = COLORS["orange"]
    else:
        cls = "fh-water-card--normal"
        emoji = "🌊"
        label_text = "Normal"
        sentence = "Sea is safe"
        color = COLORS["green"]

    st.markdown(
        f"""
        <div class="fh-water-card {cls} fh-animate fh-d5">
            <div class="fh-water-emoji">{emoji}</div>
            <div>
                <div class="fh-water-status" style="color:{color};">{label_text}</div>
                <div class="fh-water-msg">{sentence}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_voice_section() -> None:
    st.markdown(
        '<div class="fh-voice-card fh-animate fh-d5">'
        '<div class="fh-section-title"><span>🔊</span> Voice Alerts</div>',
        unsafe_allow_html=True,
    )

    col_toggle, col_lang = st.columns([1, 1])

    with col_toggle:
        voice_on = st.toggle(
            "🔊 Voice Enabled",
            value=st.session_state.get("fh_voice_on", True),
            key="fh_voice_on",
        )

    with col_lang:
        lang = st.selectbox(
            "Language / ಭಾಷೆ",
            options=["kannada", "english"],
            format_func=lambda v: {"kannada": "🇮🇳 ಕನ್ನಡ", "english": "🇬🇧 English"}[v],
            key="fh_language",
        )

    if st.button("▶ Play Test Alert", use_container_width=True, key="fh_test_alert"):
        msg = (
            "ಎಚ್ಚರಿಕೆ! ನಿಮ್ಮ ದೋಣಿ ಗಡಿಯ ಕಡೆ ಚಲಿಸುತ್ತಿದೆ."
            if lang == "kannada"
            else "Warning! Your boat is moving toward the border."
        )
        st.info(f"🔊 {msg}")

    st.markdown("</div>", unsafe_allow_html=True)


def _render_emergency(vessel: dict[str, Any]) -> None:
    lat = vessel.get("latitude", 8.5241)
    lon = vessel.get("longitude", 76.9366)

    st.markdown(
        '<div class="fh-emergency-card fh-animate fh-d6">'
        '<div class="fh-section-title" style="color:rgba(255,100,100,0.75);">'
        '<span>🚨</span> Emergency</div>',
        unsafe_allow_html=True,
    )

    # Big SOS button
    st.markdown('<div class="fh-sos-wrapper">', unsafe_allow_html=True)
    if st.button("🆘  SOS — SEND DISTRESS SIGNAL", use_container_width=True, key="fh_sos"):
        st.session_state.fh_sos_active = True

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("fh_sos_active", False):
        st.error("🚨 **SOS Sent!** Coastguard has been notified. Stay calm and wait for help.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Secondary buttons
    st.markdown('<div class="fh-sos-secondary">', unsafe_allow_html=True)
    col_cg, col_loc = st.columns(2)
    with col_cg:
        if st.button("📞 Call Coastguard", use_container_width=True, key="fh_call_cg"):
            st.info("📞 Connecting to Coastguard — 1554")
    with col_loc:
        if st.button("📡 Share My Location", use_container_width=True, key="fh_share_loc"):
            st.success(f"📡 Location shared: {lat:.4f}°N, {lon:.4f}°E")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_alerts_timeline() -> None:
    # Demo alerts — in production replace with backend feed
    alerts = [
        {
            "type": "danger",
            "icon": "🚨",
            "msg": "Drift toward maritime border detected. Turn starboard now.",
            "time": "2 min ago",
        },
        {
            "type": "caution",
            "icon": "⚠️",
            "msg": "Wind speed increasing. Rough sea expected in 30 minutes.",
            "time": "18 min ago",
        },
        {
            "type": "caution",
            "icon": "⚠️",
            "msg": "Border is 3.2 nm away. Reduce speed and correct heading.",
            "time": "35 min ago",
        },
        {
            "type": "safe",
            "icon": "✅",
            "msg": "Course corrected. You are back in safe waters.",
            "time": "1 hr ago",
        },
        {
            "type": "safe",
            "icon": "🟢",
            "msg": "Monitoring started. GPS signal strong.",
            "time": "3 hr ago",
        },
    ]

    st.markdown(
        '<div class="fh-glass fh-animate fh-d7">'
        '<div class="fh-section-title"><span>🔔</span> Recent Alerts</div>',
        unsafe_allow_html=True,
    )

    for a in alerts:
        st.markdown(
            f"""
            <div class="fh-alert-item fh-alert-item--{a['type']}">
                <div class="fh-alert-icon">{a['icon']}</div>
                <div>
                    <div class="fh-alert-msg">{a['msg']}</div>
                    <div class="fh-alert-time">🕐 {a['time']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ── Main entry point ──────────────────────────────────────────────────────────

def render_fisherman_dashboard(vessel: dict[str, Any] | None = None) -> None:
    """Render the full Fisherman Dashboard.

    Args:
        vessel: vessel data dict (uses DEMO_VESSEL if not provided).
    """
    if vessel is None:
        vessel = DEMO_VESSEL.copy()

    # Enrich with fisherman-specific demo fields if missing
    vessel.setdefault("boat_name", "Namma Kadal")
    vessel.setdefault("boat_id", "KA-MNG-0471")
    vessel.setdefault("battery_pct", 82)
    vessel.setdefault("gps_ok", True)
    vessel.setdefault("connected", True)
    vessel.setdefault("temperature_c", 28)
    vessel.setdefault("wave_height_m", 1.2)
    vessel.setdefault("visibility_km", 8)
    vessel.setdefault("rain_chance_pct", 15)

    st.markdown(FISHERMAN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="fisherman-root">', unsafe_allow_html=True)

    # ── Layout ────────────────────────────────────────────────────────────────
    # Full-width sections stacked vertically for a phone-friendly layout.

    _render_header(vessel)
    _render_safety_banner(vessel)

    # Map + status side by side on wide screens, stacked on mobile
    col_map, col_right = st.columns([1.45, 1.0])

    with col_map:
        _render_map(vessel)
        _render_water_level(vessel)
        _render_voice_section()

    with col_right:
        _render_boat_status(vessel)
        _render_weather(vessel)
        _render_emergency(vessel)
        _render_alerts_timeline()

    st.markdown("</div>", unsafe_allow_html=True)


# Allow running this page standalone for testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="SeaSentry | Fisherman Dashboard",
        page_icon="⛵",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    from controls import inject_theme_css
    inject_theme_css()
    render_fisherman_dashboard()
