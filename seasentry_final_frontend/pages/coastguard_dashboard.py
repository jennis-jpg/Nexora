"""SeaSentry — Coastguard Control Center Dashboard.

Designed for trained coastguard officers who need full situational awareness:
  • Real-time fleet overview with risk-coloured KPI tiles
  • Live multi-vessel map with predicted drift paths and crossing markers
  • Sortable boat table with SOS status
  • Real-time alert feed with category filters
  • Ocean/weather analytics with trend charts
  • Incident report management (PDF download/view)
  • Voice alert controls (language, volume, play/stop)
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any

import folium
import streamlit as st
from streamlit_folium import st_folium

from controls import COLORS, RISK_STYLES

# ── Demo fleet data ─────────────────────────────────────────────────────────

_BASE_LAT = 8.5241
_BASE_LON = 76.9366

DEMO_FLEET: list[dict[str, Any]] = [
    {
        "id": "TN-2847",
        "name": "Kaveri Star",
        "latitude": 8.5241,
        "longitude": 76.9366,
        "heading_deg": 285,
        "speed_knots": 3.2,
        "risk_level": "HIGH",
        "distance_to_boundary_nm": 1.4,
        "eta_to_boundary_min": 38,
        "status": "Drifting",
        "sos_active": False,
        "awake_check_ok": True,
        "last_seen_min": 2,
        "alert_message": "Drift toward international waters. Adjust course starboard.",
    },
    {
        "id": "TN-1193",
        "name": "Surya Prakash",
        "latitude": 8.4980,
        "longitude": 76.8800,
        "heading_deg": 310,
        "speed_knots": 5.8,
        "risk_level": "MEDIUM",
        "distance_to_boundary_nm": 4.2,
        "eta_to_boundary_min": 82,
        "status": "Fishing",
        "sos_active": False,
        "awake_check_ok": True,
        "last_seen_min": 5,
        "alert_message": "Vessel approaching restricted zone at moderate speed.",
    },
    {
        "id": "KL-0571",
        "name": "Dharani",
        "latitude": 8.5600,
        "longitude": 77.0100,
        "heading_deg": 90,
        "speed_knots": 1.1,
        "risk_level": "LOW",
        "distance_to_boundary_nm": 12.7,
        "eta_to_boundary_min": 0,
        "status": "Fishing",
        "sos_active": False,
        "awake_check_ok": True,
        "last_seen_min": 1,
        "alert_message": "",
    },
    {
        "id": "TN-3302",
        "name": "Murugan Kadalvan",
        "latitude": 8.4700,
        "longitude": 76.9800,
        "heading_deg": 260,
        "speed_knots": 0.4,
        "risk_level": "CRITICAL",
        "distance_to_boundary_nm": 0.3,
        "eta_to_boundary_min": 12,
        "status": "SOS",
        "sos_active": True,
        "awake_check_ok": False,
        "last_seen_min": 8,
        "alert_message": "SOS ACTIVATED. Vessel has crossed into restricted waters. Immediate response required.",
    },
    {
        "id": "KL-2210",
        "name": "Veeran",
        "latitude": 8.5900,
        "longitude": 76.8200,
        "heading_deg": 180,
        "speed_knots": 4.5,
        "risk_level": "LOW",
        "distance_to_boundary_nm": 18.3,
        "eta_to_boundary_min": 0,
        "status": "Returning",
        "sos_active": False,
        "awake_check_ok": True,
        "last_seen_min": 3,
        "alert_message": "",
    },
    {
        "id": "TN-4488",
        "name": "Selvi Amman",
        "latitude": 8.5100,
        "longitude": 76.9600,
        "heading_deg": 275,
        "speed_knots": 2.8,
        "risk_level": "HIGH",
        "distance_to_boundary_nm": 2.1,
        "eta_to_boundary_min": 56,
        "status": "Drifting",
        "sos_active": False,
        "awake_check_ok": False,
        "last_seen_min": 14,
        "alert_message": "Awake check failed — no response from crew. Vessel on drift course.",
    },
]

DEMO_ALERTS: list[dict[str, Any]] = [
    {
        "time": datetime.now() - timedelta(minutes=2),
        "type": "SOS",
        "boat": "TN-3302 Murugan Kadalvan",
        "message": "SOS ACTIVATED — vessel has crossed into restricted waters. Immediate intervention required.",
        "severity": "CRITICAL",
    },
    {
        "time": datetime.now() - timedelta(minutes=8),
        "type": "Awake Check",
        "boat": "TN-4488 Selvi Amman",
        "message": "Dead man switch triggered — no crew response for 14 minutes. Vessel drifting toward boundary.",
        "severity": "HIGH",
    },
    {
        "time": datetime.now() - timedelta(minutes=15),
        "type": "Border Crossing",
        "boat": "TN-3302 Murugan Kadalvan",
        "message": "EEZ boundary breached at 8.4720°N 76.9600°E. Vessel now in international waters.",
        "severity": "CRITICAL",
    },
    {
        "time": datetime.now() - timedelta(minutes=22),
        "type": "High Risk",
        "boat": "TN-2847 Kaveri Star",
        "message": "Drift prediction: vessel will cross boundary in ~38 minutes at current heading 285°.",
        "severity": "HIGH",
    },
    {
        "time": datetime.now() - timedelta(minutes=35),
        "type": "High Risk",
        "boat": "TN-4488 Selvi Amman",
        "message": "Wind speed 18 kn from SW pushing vessel toward boundary. Safe heading: 015°.",
        "severity": "HIGH",
    },
    {
        "time": datetime.now() - timedelta(minutes=48),
        "type": "Weather",
        "boat": "Fleet-wide",
        "message": "Sea state elevated — wave height 2.1m. All vessels advised to monitor heading carefully.",
        "severity": "MEDIUM",
    },
    {
        "time": datetime.now() - timedelta(minutes=62),
        "type": "Border Crossing",
        "boat": "TN-1193 Surya Prakash",
        "message": "Vessel approaching EEZ boundary at reduced speed. ETA 82 minutes. Voice alert sent.",
        "severity": "MEDIUM",
    },
    {
        "time": datetime.now() - timedelta(hours=1, minutes=40),
        "type": "Weather",
        "boat": "Fleet-wide",
        "message": "Tropical low pressure forming 200nm offshore. Wind gusts expected 25–30 kn by evening.",
        "severity": "MEDIUM",
    },
    {
        "time": datetime.now() - timedelta(hours=2, minutes=10),
        "type": "Awake Check",
        "boat": "KL-0571 Dharani",
        "message": "Awake check passed after second prompt. Crew confirmed safe.",
        "severity": "LOW",
    },
    {
        "time": datetime.now() - timedelta(hours=3),
        "type": "Weather",
        "boat": "Fleet-wide",
        "message": "Ocean current speed increased to 2.4 kn in sector B-7. Models updated.",
        "severity": "LOW",
    },
]

DEMO_REPORTS: list[dict[str, Any]] = [
    {
        "id": "RPT-2024-0847",
        "time": datetime.now() - timedelta(minutes=2),
        "boat": "TN-3302 Murugan Kadalvan",
        "type": "Border Crossing + SOS",
        "severity": "CRITICAL",
        "pages": 4,
    },
    {
        "id": "RPT-2024-0846",
        "time": datetime.now() - timedelta(minutes=15),
        "boat": "TN-4488 Selvi Amman",
        "type": "Awake Check Failure",
        "severity": "HIGH",
        "pages": 3,
    },
    {
        "id": "RPT-2024-0845",
        "time": datetime.now() - timedelta(hours=1, minutes=20),
        "boat": "TN-2847 Kaveri Star",
        "type": "High Risk Drift",
        "severity": "HIGH",
        "pages": 3,
    },
    {
        "id": "RPT-2024-0844",
        "time": datetime.now() - timedelta(hours=4, minutes=55),
        "boat": "TN-1193 Surya Prakash",
        "type": "Zone Proximity Warning",
        "severity": "MEDIUM",
        "pages": 2,
    },
]

# ── Wave/sea analytics data ──────────────────────────────────────────────────

WAVE_TREND = [1.2, 1.4, 1.5, 1.7, 1.8, 2.0, 2.1, 2.1, 2.0, 1.9, 2.1, 2.3]
SEA_LEVEL_TREND = [0.0, 0.02, 0.05, 0.04, 0.08, 0.11, 0.13, 0.15, 0.14, 0.17, 0.19, 0.21]
WIND_SPEED_TREND = [8.2, 9.4, 10.1, 11.8, 12.4, 13.0, 14.2, 15.1, 14.8, 15.6, 16.2, 18.1]
CURRENT_SPEED_TREND = [1.2, 1.3, 1.4, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2, 2.3, 2.4]
TREND_LABELS = [f"{i*10}min ago" if i > 0 else "Now" for i in range(11, -1, -1)]


# ── CSS ──────────────────────────────────────────────────────────────────────

CG_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

.cg-root {{ font-family: 'Inter', sans-serif; color: #fff; }}

/* ── Header ─────────────────────────────────────────────────────────────── */
.cg-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    margin-bottom: 1.25rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}}
.cg-header-left {{ display: flex; align-items: center; gap: 1rem; }}
.cg-header-icon {{
    width: 52px; height: 52px; border-radius: 14px;
    background: linear-gradient(135deg, {COLORS["red"]}, {COLORS["orange"]});
    display: flex; align-items: center; justify-content: center;
    font-size: 1.6rem;
    box-shadow: 0 4px 18px rgba(229,57,53,0.4);
}}
.cg-header-title {{
    font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fff, {COLORS["sky"]});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1.2;
}}
.cg-header-sub {{
    font-size: 0.72rem; color: rgba(255,255,255,0.5);
    letter-spacing: 0.06em; text-transform: uppercase; margin: 0;
}}
.cg-header-right {{ display: flex; align-items: center; gap: 1rem; }}
.cg-time {{
    font-family: 'JetBrains Mono', monospace; font-size: 1.1rem;
    font-weight: 600; color: {COLORS["sky"]};
}}
.cg-time-label {{
    font-size: 0.6rem; color: rgba(255,255,255,0.4);
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.15rem;
}}
.cg-live-pill {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.4rem 0.9rem; border-radius: 999px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; color: {COLORS["red"]};
    background: rgba(229,57,53,0.15); border: 1px solid rgba(229,57,53,0.45);
}}
.cg-live-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: {COLORS["red"]}; animation: blink-red 1.2s ease-in-out infinite;
}}
@keyframes blink-red {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.2; }} }}

/* ── Stat cards ──────────────────────────────────────────────────────────── */
.cg-stats-row {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}}
.cg-stat-card {{
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 16px;
    padding: 1.1rem 1.15rem;
    display: flex; align-items: center; gap: 0.85rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    animation: fade-slide-up 0.5s ease-out both;
}}
.cg-stat-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    border-color: rgba(255,255,255,0.22);
}}
.cg-stat-card--alert {{ border-color: {COLORS["red"]}55; animation: fade-slide-up 0.5s ease-out both, stat-alert-pulse 2s ease-in-out infinite; }}
@keyframes stat-alert-pulse {{
    0%,100% {{ box-shadow: 0 4px 20px rgba(0,0,0,0.2); }}
    50% {{ box-shadow: 0 4px 28px {COLORS["red"]}44; }}
}}
.cg-stat-icon {{
    width: 46px; height: 46px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.4rem; flex-shrink: 0;
}}
.cg-stat-label {{
    font-size: 0.62rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.07em; color: rgba(255,255,255,0.5); margin-bottom: 0.18rem;
}}
.cg-stat-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.7rem; font-weight: 700; line-height: 1.1;
}}
.cg-stat-sub {{
    font-size: 0.62rem; color: rgba(255,255,255,0.4); margin-top: 0.1rem;
}}

/* ── Section headers ─────────────────────────────────────────────────────── */
.cg-section {{
    background: rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.11);
    border-radius: 18px;
    padding: 1.25rem 1.35rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2);
}}
.cg-section-title {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1rem;
}}
.cg-section-title-left {{
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; color: rgba(255,255,255,0.6);
}}
.cg-section-title-left span {{ color: {COLORS["sky"]}; font-size: 1rem; }}
.cg-section-badge {{
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.05em;
    padding: 0.22rem 0.65rem; border-radius: 6px;
    text-transform: uppercase;
}}
.cg-section-badge--red {{
    background: rgba(229,57,53,0.18); border: 1px solid rgba(229,57,53,0.4);
    color: {COLORS["red"]};
}}
.cg-section-badge--orange {{
    background: rgba(255,152,0,0.18); border: 1px solid rgba(255,152,0,0.4);
    color: {COLORS["orange"]};
}}
.cg-section-badge--teal {{
    background: rgba(0,194,168,0.15); border: 1px solid rgba(0,194,168,0.35);
    color: {COLORS["teal"]};
}}

/* ── Boat table ──────────────────────────────────────────────────────────── */
.cg-table {{
    width: 100%; border-collapse: collapse;
    font-size: 0.84rem;
}}
.cg-table thead tr {{
    border-bottom: 1px solid rgba(255,255,255,0.1);
}}
.cg-table th {{
    text-align: left; padding: 0.5rem 0.75rem;
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; color: rgba(255,255,255,0.45);
}}
.cg-table td {{
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    vertical-align: middle;
}}
.cg-table tbody tr {{
    transition: background 0.18s ease;
}}
.cg-table tbody tr:hover {{
    background: rgba(255,255,255,0.04);
}}
.cg-table tbody tr.row-critical {{
    background: rgba(229,57,53,0.08);
}}
.cg-table tbody tr.row-critical:hover {{
    background: rgba(229,57,53,0.14);
}}
.cg-boat-name {{
    font-weight: 600; font-size: 0.88rem; color: #fff;
    display: block; line-height: 1.2;
}}
.cg-boat-id {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem; color: rgba(255,255,255,0.45); margin-top: 0.1rem;
}}
.cg-mono {{ font-family: 'JetBrains Mono', monospace; }}
.cg-risk-pill {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.25rem 0.65rem; border-radius: 6px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; white-space: nowrap;
}}
.cg-sos-badge {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.25rem 0.65rem; border-radius: 6px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase;
    animation: sos-flash 1s ease-in-out infinite;
}}
@keyframes sos-flash {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.45; }} }}
.cg-status-pill {{
    display: inline-flex; align-items: center; gap: 0.3rem;
    padding: 0.2rem 0.6rem; border-radius: 5px;
    font-size: 0.65rem; font-weight: 600; letter-spacing: 0.03em;
}}

/* ── Alert feed ──────────────────────────────────────────────────────────── */
.cg-alert-filters {{
    display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem;
}}
.cg-alert-item {{
    display: flex; gap: 0.85rem; align-items: flex-start;
    padding: 0.85rem 1rem;
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.07);
    border-left: 3px solid transparent;
    border-radius: 12px;
    margin-bottom: 0.55rem;
    transition: background 0.18s ease;
}}
.cg-alert-item:hover {{ background: rgba(255,255,255,0.04); }}
.cg-alert-item--CRITICAL {{ border-left-color: {COLORS["red"]}; }}
.cg-alert-item--HIGH {{ border-left-color: {COLORS["orange"]}; }}
.cg-alert-item--MEDIUM {{ border-left-color: {COLORS["sky"]}; }}
.cg-alert-item--LOW {{ border-left-color: {COLORS["teal"]}; }}
.cg-alert-icon {{
    width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem;
}}
.cg-alert-type {{
    font-size: 0.62rem; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; margin-bottom: 0.2rem;
}}
.cg-alert-boat {{
    font-size: 0.72rem; font-weight: 600; color: {COLORS["sky"]}; margin-bottom: 0.25rem;
}}
.cg-alert-msg {{
    font-size: 0.83rem; color: rgba(255,255,255,0.78); line-height: 1.5;
}}
.cg-alert-time {{
    font-size: 0.62rem; color: rgba(255,255,255,0.38);
    font-family: 'JetBrains Mono', monospace; margin-top: 0.35rem;
}}

/* ── Analytics charts ───────────────────────────────────────────────────── */
.cg-analytics-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1rem;
}}
.cg-analytics-chart {{
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 1rem;
}}
.cg-chart-title {{
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.07em;
    text-transform: uppercase; color: rgba(255,255,255,0.55);
    margin-bottom: 0.5rem; display: flex; align-items: center;
    justify-content: space-between;
}}
.cg-chart-current-val {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.35rem; font-weight: 600;
}}
.cg-chart-unit {{
    font-size: 0.72rem; color: rgba(255,255,255,0.4);
}}
.cg-chart-trend {{
    font-size: 0.65rem; margin-left: 0.5rem;
}}
.cg-chart-trend--up {{ color: {COLORS["red"]}; }}
.cg-chart-trend--down {{ color: {COLORS["green"]}; }}
.cg-chart-trend--stable {{ color: {COLORS["teal"]}; }}

/* Sparkline SVG */
.cg-sparkline {{ display: block; width: 100%; height: 56px; margin-top: 0.5rem; }}

/* Analytics summary tiles */
.cg-analytics-tiles {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem; margin-top: 1rem;
}}
.cg-analytics-tile {{
    background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 0.85rem 1rem;
    display: flex; align-items: center; gap: 0.75rem;
}}
.cg-analytics-tile-icon {{
    width: 40px; height: 40px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; flex-shrink: 0;
}}
.cg-analytics-tile-label {{
    font-size: 0.6rem; font-weight: 600; letter-spacing: 0.07em;
    text-transform: uppercase; color: rgba(255,255,255,0.45); margin-bottom: 0.15rem;
}}
.cg-analytics-tile-val {{
    font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600;
}}

/* ── Incident reports ────────────────────────────────────────────────────── */
.cg-report-item {{
    display: flex; align-items: center; gap: 1rem;
    padding: 0.85rem 1rem;
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; margin-bottom: 0.55rem;
    transition: background 0.18s ease;
}}
.cg-report-item:hover {{ background: rgba(255,255,255,0.04); }}
.cg-report-icon {{
    width: 42px; height: 42px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
    background: rgba(77,182,255,0.15); border: 1px solid rgba(77,182,255,0.25);
}}
.cg-report-id {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem; font-weight: 600; color: {COLORS["sky"]}; margin-bottom: 0.15rem;
}}
.cg-report-boat {{
    font-size: 0.85rem; font-weight: 600; color: #fff; margin-bottom: 0.1rem;
}}
.cg-report-type {{
    font-size: 0.7rem; color: rgba(255,255,255,0.5);
}}
.cg-report-time {{
    font-size: 0.62rem; font-family: 'JetBrains Mono', monospace;
    color: rgba(255,255,255,0.35); margin-left: auto; flex-shrink: 0;
}}
.cg-report-pages {{
    font-size: 0.62rem; color: rgba(255,255,255,0.35);
}}

/* ── Voice controls ──────────────────────────────────────────────────────── */
.cg-voice-grid {{
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 1rem;
}}
.cg-voice-panel {{
    background: rgba(0,0,0,0.22); border: 1px solid rgba(255,255,255,0.09);
    border-radius: 14px; padding: 1.1rem;
}}
.cg-voice-panel-title {{
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: rgba(255,255,255,0.5); margin-bottom: 0.85rem;
    display: flex; align-items: center; gap: 0.4rem;
}}
.cg-voice-panel-title span {{ color: {COLORS["sky"]}; }}

/* ── Map legend ──────────────────────────────────────────────────────────── */
.cg-map-legend {{
    display: flex; gap: 1.25rem; flex-wrap: wrap;
    font-size: 0.68rem; color: rgba(255,255,255,0.6);
    margin-top: 0.65rem; padding: 0.65rem 0.85rem;
    background: rgba(0,0,0,0.22); border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
}}
.cg-legend-item {{ display: flex; align-items: center; gap: 0.4rem; }}
.cg-legend-dot {{
    width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}}

/* ── Divider ─────────────────────────────────────────────────────────────── */
.cg-divider {{
    border: none; border-top: 1px solid rgba(255,255,255,0.07); margin: 1rem 0;
}}

/* ── Responsive ──────────────────────────────────────────────────────────── */
@media (max-width: 1200px) {{
    .cg-stats-row {{ grid-template-columns: repeat(3, 1fr); }}
    .cg-analytics-grid {{ grid-template-columns: 1fr; }}
    .cg-voice-grid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 768px) {{
    .cg-stats-row {{ grid-template-columns: 1fr 1fr; }}
    .cg-header {{ flex-direction: column; gap: 0.75rem; text-align: center; }}
    .cg-analytics-tiles {{ grid-template-columns: 1fr; }}
}}

@keyframes fade-slide-up {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""


# ── Helper utilities ─────────────────────────────────────────────────────────

def _risk_color(level: str) -> str:
    return {
        "LOW": COLORS["green"],
        "MEDIUM": COLORS["orange"],
        "HIGH": COLORS["red"],
        "CRITICAL": COLORS["red"],
    }.get(level, COLORS["orange"])


def _risk_icon(level: str) -> str:
    return {"LOW": "✓", "MEDIUM": "⚠", "HIGH": "⛔", "CRITICAL": "🚨"}.get(level, "⚠")


def _alert_icon(alert_type: str) -> str:
    return {
        "SOS": "🆘", "Border Crossing": "🚧", "High Risk": "⛔",
        "Awake Check": "😴", "Weather": "🌊",
    }.get(alert_type, "📡")


def _alert_icon_bg(alert_type: str) -> str:
    colors = {
        "SOS": f"rgba(229,57,53,0.2)",
        "Border Crossing": f"rgba(255,152,0,0.18)",
        "High Risk": f"rgba(229,57,53,0.15)",
        "Awake Check": f"rgba(77,182,255,0.15)",
        "Weather": f"rgba(0,194,168,0.15)",
    }
    return colors.get(alert_type, "rgba(255,255,255,0.1)")


def _severity_color(sev: str) -> str:
    return {
        "CRITICAL": COLORS["red"], "HIGH": COLORS["orange"],
        "MEDIUM": COLORS["sky"], "LOW": COLORS["teal"],
    }.get(sev, COLORS["sky"])


def _time_ago(dt: datetime) -> str:
    delta = datetime.now() - dt
    mins = int(delta.total_seconds() / 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins}m ago"
    hrs = mins // 60
    return f"{hrs}h {mins % 60}m ago"


def _sparkline_svg(values: list[float], color: str, width: int = 300, height: int = 56) -> str:
    """Build a simple inline SVG sparkline from a list of values."""
    mn, mx = min(values), max(values)
    rng = mx - mn or 1.0
    n = len(values)
    step_x = width / (n - 1) if n > 1 else width
    pts = [
        f"{i * step_x:.1f},{height - 8 - ((v - mn) / rng) * (height - 16):.1f}"
        for i, v in enumerate(values)
    ]
    polyline = " ".join(pts)
    # Close area fill path
    fill_path = (
        f"M0,{height} L" + " L".join(pts) + f" L{(n - 1) * step_x:.1f},{height} Z"
    )
    grad_id = f"sg{abs(hash(color))}"
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'class="cg-sparkline" preserveAspectRatio="none">'
        f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.02"/>'
        "</linearGradient></defs>"
        f'<path d="{fill_path}" fill="url(#{grad_id})" />'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{(n - 1) * step_x:.1f}" '
        f'cy="{height - 8 - ((values[-1] - mn) / rng) * (height - 16):.1f}" '
        f'r="3.5" fill="{color}" />'
        "</svg>"
    )


def _trend_arrow(values: list[float]) -> tuple[str, str]:
    """Return (symbol, css-class) for trend direction."""
    if len(values) < 2:
        return "→", "stable"
    diff = values[-1] - values[-3] if len(values) >= 3 else values[-1] - values[0]
    if diff > 0.05:
        return "↑", "up"
    if diff < -0.05:
        return "↓", "down"
    return "→", "stable"


# ── Section renderers ────────────────────────────────────────────────────────

def _render_header() -> None:
    now = datetime.now()
    st.markdown(
        f"""
        <div class="cg-header animate-in">
            <div class="cg-header-left">
                <div class="cg-header-icon">🛡</div>
                <div>
                    <p class="cg-header-title">Coastguard Control Center</p>
                    <p class="cg-header-sub">SeaSentry AI · Maritime Surveillance & Rapid Response</p>
                </div>
            </div>
            <div class="cg-header-right">
                <div style="text-align:right;">
                    <div class="cg-time-label">Station Time</div>
                    <div class="cg-time">{now.strftime('%H:%M:%S')} IST</div>
                    <div style="font-size:0.62rem; color:rgba(255,255,255,0.35);">
                        {now.strftime('%d %b %Y')}
                    </div>
                </div>
                <div class="cg-live-pill">
                    <span class="cg-live-dot"></span> Live · Demo
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stats_row(fleet: list[dict]) -> None:
    active = len(fleet)
    high_risk = sum(1 for v in fleet if v["risk_level"] in ("HIGH", "CRITICAL"))
    sos = sum(1 for v in fleet if v["sos_active"])
    crossings = sum(1 for v in fleet if v["distance_to_boundary_nm"] < 1.0)
    awake_fail = sum(1 for v in fleet if not v["awake_check_ok"])

    stats = [
        {
            "icon": "🚢",
            "label": "Active Boats",
            "value": str(active),
            "sub": "Vessels tracked",
            "icon_bg": f"linear-gradient(135deg, {COLORS['ocean']}, {COLORS['teal']})",
            "value_color": COLORS["white"],
            "alert": False,
            "delay": "0.04s",
        },
        {
            "icon": "⛔",
            "label": "High Risk",
            "value": str(high_risk),
            "sub": "Needs attention",
            "icon_bg": f"linear-gradient(135deg, {COLORS['red']}, {COLORS['orange']})",
            "value_color": COLORS["orange"],
            "alert": high_risk > 0,
            "delay": "0.09s",
        },
        {
            "icon": "🆘",
            "label": "SOS Alerts",
            "value": str(sos),
            "sub": "Active distress",
            "icon_bg": f"linear-gradient(135deg, {COLORS['red']}, #c62828)",
            "value_color": COLORS["red"],
            "alert": sos > 0,
            "delay": "0.14s",
        },
        {
            "icon": "🚧",
            "label": "Border Crossings",
            "value": str(crossings),
            "sub": "< 1 nm from line",
            "icon_bg": f"linear-gradient(135deg, {COLORS['orange']}, #e65100)",
            "value_color": COLORS["orange"],
            "alert": crossings > 0,
            "delay": "0.19s",
        },
        {
            "icon": "😴",
            "label": "Awake Check Fails",
            "value": str(awake_fail),
            "sub": "No crew response",
            "icon_bg": f"linear-gradient(135deg, {COLORS['sky']}, {COLORS['ocean']})",
            "value_color": COLORS["sky"],
            "alert": awake_fail > 0,
            "delay": "0.24s",
        },
    ]

    cards_html = ""
    for s in stats:
        alert_cls = "cg-stat-card--alert" if s["alert"] else ""
        cards_html += (
            f'<div class="cg-stat-card {alert_cls}" style="animation-delay:{s["delay"]};">'
            f'<div class="cg-stat-icon" style="background:{s["icon_bg"]};">{s["icon"]}</div>'
            "<div>"
            f'<div class="cg-stat-label">{s["label"]}</div>'
            f'<div class="cg-stat-value" style="color:{s["value_color"]};">{s["value"]}</div>'
            f'<div class="cg-stat-sub">{s["sub"]}</div>'
            "</div>"
            "</div>"
        )

    st.markdown(
        f'<div class="cg-stats-row">{cards_html}</div>',
        unsafe_allow_html=True,
    )


def _render_map(fleet: list[dict]) -> None:
    """Full-width multi-vessel map with risk markers, paths, and boundary line."""
    st.markdown(
        """
        <div class="cg-section-title">
            <div class="cg-section-title-left">
                <span>🗺️</span> Live Vessel Map
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compute center
    avg_lat = sum(v["latitude"] for v in fleet) / len(fleet)
    avg_lon = sum(v["longitude"] for v in fleet) / len(fleet)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=9, tiles=None)

    # Base layers
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap &copy; CARTO",
        name="Dark",
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

    # EEZ boundary (relative to fleet center as placeholder)
    boundary_coords = [
        [avg_lat - 0.6, avg_lon + 0.12],
        [avg_lat, avg_lon + 0.08],
        [avg_lat + 0.6, avg_lon + 0.04],
    ]
    folium.PolyLine(
        locations=boundary_coords,
        color=COLORS["red"],
        weight=3,
        dash_array="10 6",
        tooltip="EEZ Maritime Boundary",
    ).add_to(m)

    # Restricted zone polygon fill near boundary
    folium.Polygon(
        locations=[
            [avg_lat - 0.6, avg_lon + 0.12],
            [avg_lat, avg_lon + 0.08],
            [avg_lat + 0.6, avg_lon + 0.04],
            [avg_lat + 0.6, avg_lon + 0.5],
            [avg_lat - 0.6, avg_lon + 0.5],
        ],
        color=COLORS["red"],
        weight=0,
        fill=True,
        fill_color=COLORS["red"],
        fill_opacity=0.06,
        tooltip="International Waters",
    ).add_to(m)

    risk_colors = {
        "LOW": COLORS["green"],
        "MEDIUM": COLORS["orange"],
        "HIGH": COLORS["red"],
        "CRITICAL": "#ff0000",
    }

    for vessel in fleet:
        lat = float(vessel["latitude"])
        lon = float(vessel["longitude"])
        risk = vessel["risk_level"]
        color = risk_colors.get(risk, COLORS["orange"])
        is_sos = vessel["sos_active"]

        # Predict drift path (simple heading projection)
        heading_rad = math.radians(float(vessel["heading_deg"]))
        speed = float(vessel["speed_knots"])
        nm_per_deg_lat = 60.0
        nm_per_deg_lon = 60.0 * math.cos(math.radians(lat))
        distance_nm = speed * 1.5  # 90-minute projection
        d_lat = (math.cos(heading_rad) * distance_nm) / nm_per_deg_lat
        d_lon = (math.sin(heading_rad) * distance_nm) / nm_per_deg_lon
        pred_lat = lat + d_lat
        pred_lon = lon + d_lon

        # Drift path line
        folium.PolyLine(
            locations=[[lat, lon], [pred_lat, pred_lon]],
            color=color,
            weight=2,
            dash_array="5 4",
            opacity=0.6,
            tooltip=f"{vessel['name']} — predicted path (90 min)",
        ).add_to(m)

        # Predicted endpoint
        folium.CircleMarker(
            location=[pred_lat, pred_lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            weight=1,
            tooltip=f"Predicted position · {vessel['name']}",
        ).add_to(m)

        # If predicted path crosses boundary, mark it
        if vessel["distance_to_boundary_nm"] < 3.0 and risk in ("HIGH", "CRITICAL"):
            mid_lat = (lat + pred_lat) / 2
            mid_lon = (lon + pred_lon) / 2 + 0.02
            folium.Marker(
                location=[mid_lat, mid_lon],
                tooltip=f"⚠ Predicted crossing · {vessel['name']}",
                icon=folium.DivIcon(
                    html=f'<div style="font-size:1.1rem;">⚠</div>',
                    icon_size=(22, 22),
                    icon_anchor=(11, 11),
                ),
            ).add_to(m)

        # Vessel marker
        radius = 12 if is_sos else 9
        pulse = ' class="leaflet-sos-pulse"' if is_sos else ""
        icon_char = "🆘" if is_sos else ("⛔" if risk == "CRITICAL" else "🚢")
        popup_html = f"""
        <div style='font-family:sans-serif; font-size:12px; min-width:180px; padding:4px;'>
            <b style='color:{color};'>{vessel['name']}</b><br>
            ID: {vessel['id']}<br>
            Risk: <b style='color:{color};'>{risk}</b><br>
            Speed: {vessel['speed_knots']} kn · Heading: {vessel['heading_deg']}°<br>
            Dist to border: {vessel['distance_to_boundary_nm']} nm<br>
            {"<b style='color:red;'>🆘 SOS ACTIVE</b><br>" if is_sos else ""}
            {"<span style='color:orange;'>⚠ Awake check failed</span>" if not vessel['awake_check_ok'] else ""}
        </div>
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            weight=2 if is_sos else 1,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{icon_char} {vessel['name']} · {risk}",
        ).add_to(m)

        # Vessel label
        folium.Marker(
            location=[lat + 0.008, lon],
            tooltip=vessel["name"],
            icon=folium.DivIcon(
                html=f"""<div style='font-family:sans-serif; font-size:10px;
                    color:white; font-weight:600; white-space:nowrap;
                    text-shadow: 0 1px 3px #000, 0 0 6px #000;
                    padding:1px 3px;'>{vessel['name']}</div>""",
                icon_size=(120, 20),
                icon_anchor=(60, 10),
            ),
        ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)

    st_folium(m, use_container_width=True, height=480, returned_objects=[])

    # Legend
    st.markdown(
        f"""
        <div class="cg-map-legend">
            <div class="cg-legend-item">
                <div class="cg-legend-dot" style="background:{COLORS['green']};"></div> Low Risk
            </div>
            <div class="cg-legend-item">
                <div class="cg-legend-dot" style="background:{COLORS['orange']};"></div> Medium Risk
            </div>
            <div class="cg-legend-item">
                <div class="cg-legend-dot" style="background:{COLORS['red']};"></div> High / Critical
            </div>
            <div class="cg-legend-item">
                <div style="width:22px; height:2px; background:{COLORS['red']}; border-top: 2px dashed {COLORS['red']};"></div>
                &nbsp;EEZ Boundary
            </div>
            <div class="cg-legend-item">
                <div style="width:22px; height:2px; border-top: 2px dashed rgba(255,255,255,0.45);"></div>
                &nbsp;Predicted Path (90 min)
            </div>
            <div class="cg-legend-item">⚠ Predicted Crossing Point</div>
            <div class="cg-legend-item" style="margin-left:auto; color:rgba(255,255,255,0.4); font-size:0.6rem;">
                Click vessel for details
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_boat_table(fleet: list[dict]) -> None:
    sos_count = sum(1 for v in fleet if v["sos_active"])
    badge_cls = "cg-section-badge--red" if sos_count else "cg-section-badge--teal"
    badge_txt = f"{sos_count} SOS" if sos_count else "All Clear"

    st.markdown(
        f"""
        <div class="cg-section-title">
            <div class="cg-section-title-left"><span>📋</span> Vessel Fleet Table</div>
            <span class="cg-section-badge {badge_cls}">{badge_txt}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    rows_html = ""
    for v in sorted(
        fleet,
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x["risk_level"], 4),
    ):
        color = _risk_color(v["risk_level"])
        icon = _risk_icon(v["risk_level"])
        row_cls = "row-critical" if v["sos_active"] else ""
        eta = f"{v['eta_to_boundary_min']} min" if v["eta_to_boundary_min"] > 0 else "—"
        awake_html = (
            '<span style="color:#ff9800; font-size:0.75rem;">⚠ Failed</span>'
            if not v["awake_check_ok"]
            else '<span style="color:#2ecc71; font-size:0.75rem;">✓ OK</span>'
        )
        sos_html = (
            f'<span class="cg-sos-badge" style="background:rgba(229,57,53,0.2);'
            f'border:1px solid rgba(229,57,53,0.5); color:{COLORS["red"]};">🆘 ACTIVE</span>'
            if v["sos_active"]
            else '<span style="color:rgba(255,255,255,0.3); font-size:0.75rem;">—</span>'
        )
        status_color = {
            "SOS": COLORS["red"], "Drifting": COLORS["orange"],
            "Fishing": COLORS["teal"], "Returning": COLORS["sky"],
        }.get(v["status"], COLORS["white"])
        status_bg = f"{status_color}22"
        status_border = f"{status_color}44"

        rows_html += (
            f'<tr class="{row_cls}">'
            "<td>"
            f'<span class="cg-boat-name">{v["name"]}</span> '
            f'<span class="cg-boat-id">{v["id"]}</span>'
            "</td>"
            f'<td class="cg-mono">{v["speed_knots"]:.1f} kn</td>'
            f'<td class="cg-mono">{v["heading_deg"]}°</td>'
            "<td>"
            f'<span class="cg-risk-pill" style="background:{color}22; border:1px solid {color}55; color:{color};">'
            f"{icon} {v['risk_level']}"
            "</span>"
            "</td>"
            f'<td class="cg-mono" style="color:{COLORS["sky"]};">{eta}</td>'
            "<td>"
            f'<span class="cg-status-pill" style="background:{status_bg}; border:1px solid {status_border}; color:{status_color};">'
            f"{v['status']}"
            "</span>"
            "</td>"
            f"<td>{awake_html}</td>"
            f"<td>{sos_html}</td>"
            "</tr>"
        )

    st.markdown(
        f"""
        <table class="cg-table">
            <thead>
                <tr>
                    <th>Boat</th>
                    <th>Speed</th>
                    <th>Heading</th>
                    <th>Risk</th>
                    <th>ETA to Border</th>
                    <th>Status</th>
                    <th>Awake Check</th>
                    <th>SOS</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def _render_alert_feed(alerts: list[dict]) -> None:
    active_types = sum(1 for a in alerts if a["severity"] in ("CRITICAL", "HIGH"))
    badge_cls = "cg-section-badge--red" if active_types else "cg-section-badge--teal"

    st.markdown(
        f"""
        <div class="cg-section-title">
            <div class="cg-section-title-left"><span>📡</span> Real-Time Alert Feed</div>
            <span class="cg-section-badge {badge_cls}">{active_types} Active</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filter checkboxes
    st.markdown(
        '<div style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.07em; '
        'color:rgba(255,255,255,0.4); margin-bottom:0.35rem; font-weight:700;">Filters</div>',
        unsafe_allow_html=True,
    )
    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([1, 1, 1, 1, 1, 3])
    with col_f1:
        show_sos = st.checkbox("🆘 SOS", value=True, key="af_sos")
    with col_f2:
        show_border = st.checkbox("🚧 Border", value=True, key="af_border")
    with col_f3:
        show_high = st.checkbox("⛔ High Risk", value=True, key="af_high")
    with col_f4:
        show_awake = st.checkbox("😴 Awake", value=True, key="af_awake")
    with col_f5:
        show_weather = st.checkbox("🌊 Weather", value=True, key="af_weather")

    type_map = {
        "SOS": show_sos,
        "Border Crossing": show_border,
        "High Risk": show_high,
        "Awake Check": show_awake,
        "Weather": show_weather,
    }

    filtered = [a for a in alerts if type_map.get(a["type"], True)]

    if not filtered:
        st.markdown(
            '<div style="text-align:center; padding:1.5rem; color:rgba(255,255,255,0.35); font-size:0.85rem;">'
            '✓ No alerts match selected filters</div>',
            unsafe_allow_html=True,
        )
        return

    feed_html = ""
    for alert in filtered:
        sev_color = _severity_color(alert["severity"])
        icon = _alert_icon(alert["type"])
        icon_bg = _alert_icon_bg(alert["type"])
        feed_html += (
            f'<div class="cg-alert-item cg-alert-item--{alert["severity"]}">'
            f'<div class="cg-alert-icon" style="background:{icon_bg};">{icon}</div>'
            '<div style="flex:1; min-width:0;">'
            f'<div class="cg-alert-type" style="color:{sev_color};">{alert["type"]}</div>'
            f'<div class="cg-alert-boat">{alert["boat"]}</div>'
            f'<div class="cg-alert-msg">{alert["message"]}</div>'
            f'<div class="cg-alert-time">{_time_ago(alert["time"])} · {alert["time"].strftime("%H:%M")}</div>'
            "</div>"
            "<div>"
            f'<span class="cg-section-badge" style="background:{sev_color}18; border:1px solid {sev_color}44; '
            f'color:{sev_color}; font-size:0.6rem; padding:0.18rem 0.55rem; border-radius:5px;">{alert["severity"]}</span>'
            "</div>"
            "</div>"
        )

    st.markdown(
        f'<div style="max-height:420px; overflow-y:auto; padding-right:0.25rem;">{feed_html}</div>',
        unsafe_allow_html=True,
    )


def _render_analytics() -> None:
    st.markdown(
        """
        <div class="cg-section-title">
            <div class="cg-section-title-left"><span>📊</span> Water Level & Ocean Analytics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Summary tiles
    wave_arrow, wave_cls = _trend_arrow(WAVE_TREND)
    wind_arrow, wind_cls = _trend_arrow(WIND_SPEED_TREND)
    sea_arrow, sea_cls = _trend_arrow(SEA_LEVEL_TREND)
    cur_arrow, cur_cls = _trend_arrow(CURRENT_SPEED_TREND)

    st.markdown(
        f"""
        <div class="cg-analytics-tiles">
            <div class="cg-analytics-tile">
                <div class="cg-analytics-tile-icon"
                     style="background:linear-gradient(135deg,{COLORS['ocean']}55,{COLORS['teal']}44);">🌊</div>
                <div>
                    <div class="cg-analytics-tile-label">Wave Height</div>
                    <div class="cg-analytics-tile-val">
                        {WAVE_TREND[-1]:.1f} m
                        <span class="cg-chart-trend cg-chart-trend--{wave_cls}">{wave_arrow}</span>
                    </div>
                </div>
            </div>
            <div class="cg-analytics-tile">
                <div class="cg-analytics-tile-icon"
                     style="background:linear-gradient(135deg,{COLORS['sky']}44,{COLORS['ocean']}44);">💨</div>
                <div>
                    <div class="cg-analytics-tile-label">Wind Speed</div>
                    <div class="cg-analytics-tile-val">
                        {WIND_SPEED_TREND[-1]:.1f} kn
                        <span class="cg-chart-trend cg-chart-trend--{wind_cls}">{wind_arrow}</span>
                    </div>
                </div>
            </div>
            <div class="cg-analytics-tile">
                <div class="cg-analytics-tile-icon"
                     style="background:linear-gradient(135deg,{COLORS['teal']}44,{COLORS['sky']}33);">📈</div>
                <div>
                    <div class="cg-analytics-tile-label">Sea Level Anomaly</div>
                    <div class="cg-analytics-tile-val">
                        +{SEA_LEVEL_TREND[-1]:.2f} m
                        <span class="cg-chart-trend cg-chart-trend--{sea_cls}">{sea_arrow}</span>
                    </div>
                </div>
            </div>
            <div class="cg-analytics-tile">
                <div class="cg-analytics-tile-icon"
                     style="background:linear-gradient(135deg,{COLORS['green']}33,{COLORS['teal']}33);">↗️</div>
                <div>
                    <div class="cg-analytics-tile-label">Current Speed</div>
                    <div class="cg-analytics-tile-val">
                        {CURRENT_SPEED_TREND[-1]:.1f} kn
                        <span class="cg-chart-trend cg-chart-trend--{cur_cls}">{cur_arrow}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="cg-divider">', unsafe_allow_html=True)

    # Sparkline charts 2x2 grid
    charts = [
        ("🌊 Wave Height", WAVE_TREND, "m", COLORS["sky"], f"{WAVE_TREND[-1]:.1f}"),
        ("📈 Sea Level Trend", SEA_LEVEL_TREND, "m", COLORS["teal"], f"+{SEA_LEVEL_TREND[-1]:.2f}"),
        ("💨 Wind Speed", WIND_SPEED_TREND, "kn", COLORS["orange"], f"{WIND_SPEED_TREND[-1]:.1f}"),
        ("↗️ Current Speed", CURRENT_SPEED_TREND, "kn", COLORS["green"], f"{CURRENT_SPEED_TREND[-1]:.1f}"),
    ]

    col1, col2 = st.columns(2)
    for idx, (title, data, unit, color, cur_val) in enumerate(charts):
        col = col1 if idx % 2 == 0 else col2
        with col:
            arrow, trend_cls = _trend_arrow(data)
            sparkline = _sparkline_svg(data, color)
            card_html = (
                '<div class="cg-analytics-chart">'
                '<div class="cg-chart-title">'
                f"<span>{title}</span>"
                '<span style="font-size:0.6rem; color:rgba(255,255,255,0.3);">Last 2 hours</span>'
                "</div>"
                "<div>"
                f'<span class="cg-chart-current-val" style="color:{color};">{cur_val}</span>'
                f'<span class="cg-chart-unit"> {unit}</span>'
                f'<span class="cg-chart-trend cg-chart-trend--{trend_cls}"> {arrow}</span>'
                "</div>"
                f"{sparkline}"
                '<div style="display:flex; justify-content:space-between; '
                'font-size:0.58rem; color:rgba(255,255,255,0.3); margin-top:0.3rem;">'
                "<span>120 min ago</span><span>Now</span>"
                "</div>"
                "</div>"
            )
            st.markdown(card_html, unsafe_allow_html=True)


def _render_incident_reports(reports: list[dict]) -> None:
    st.markdown(
        f"""
        <div class="cg-section-title">
            <div class="cg-section-title-left"><span>📄</span> Incident Reports</div>
            <span class="cg-section-badge cg-section-badge--teal">{len(reports)} Generated</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for rep in reports:
        sev_color = _severity_color(rep["severity"])
        time_str = _time_ago(rep["time"])
        st.markdown(
            f"""
            <div class="cg-report-item">
                <div class="cg-report-icon">📄</div>
                <div style="flex:1; min-width:0;">
                    <div class="cg-report-id">{rep['id']}</div>
                    <div class="cg-report-boat">{rep['boat']}</div>
                    <div class="cg-report-type">{rep['type']} · {rep['pages']} pages</div>
                </div>
                <div class="cg-report-time">{time_str}</div>
                <span class="cg-section-badge" style="
                    background:{sev_color}18; border:1px solid {sev_color}44;
                    color:{sev_color}; margin-left:0.5rem;
                ">{rep['severity']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_dl, col_view, col_gap = st.columns([1, 1, 3])
        with col_dl:
            st.download_button(
                f"⬇ Download",
                data=_generate_report_text(rep),
                file_name=f"{rep['id']}.txt",
                mime="text/plain",
                key=f"dl_{rep['id']}",
                use_container_width=True,
            )
        with col_view:
            if st.button(f"👁 View", key=f"view_{rep['id']}", use_container_width=True, type="secondary"):
                st.session_state[f"show_report_{rep['id']}"] = not st.session_state.get(
                    f"show_report_{rep['id']}", False
                )

        if st.session_state.get(f"show_report_{rep['id']}", False):
            st.text_area(
                "Report Preview",
                _generate_report_text(rep),
                height=200,
                key=f"ta_{rep['id']}",
                disabled=True,
            )


def _generate_report_text(rep: dict) -> str:
    return (
        f"SEASENTRY MARITIME INCIDENT REPORT\n"
        f"{'=' * 45}\n"
        f"Report ID : {rep['id']}\n"
        f"Generated : {rep['time'].strftime('%Y-%m-%d %H:%M:%S IST')}\n"
        f"Vessel    : {rep['boat']}\n"
        f"Type      : {rep['type']}\n"
        f"Severity  : {rep['severity']}\n"
        f"Pages     : {rep['pages']}\n"
        f"{'=' * 45}\n\n"
        f"INCIDENT SUMMARY\n"
        f"This report was automatically generated by SeaSentry AI upon detection\n"
        f"of a {rep['type']} event involving vessel {rep['boat']}.\n\n"
        f"ACTION TAKEN\n"
        f"Voice alert dispatched to vessel. Coastguard notified.\n"
        f"Drift prediction model updated with latest telemetry.\n\n"
        f"STATUS\n"
        f"Investigation ongoing. Refer to full dashboard for live updates.\n\n"
        f"--- End of Report {rep['id']} ---\n"
    )


def _render_voice_controls() -> None:
    st.markdown(
        """
        <div class="cg-section-title">
            <div class="cg-section-title-left"><span>🔊</span> Voice Alert Controls</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_lang, col_controls = st.columns([1, 2])

    with col_lang:
        st.markdown(
            '<div class="cg-voice-panel">'
            '<div class="cg-voice-panel-title"><span>🌐</span> Language</div>',
            unsafe_allow_html=True,
        )
        lang = st.selectbox(
            "Alert Language",
            options=["kannada", "english", "tamil", "malayalam"],
            format_func=lambda v: {
                "kannada": "ಕನ್ನಡ · Kannada",
                "english": "English",
                "tamil": "தமிழ் · Tamil",
                "malayalam": "മലയാളം · Malayalam",
            }[v],
            key="cg_voice_lang",
            label_visibility="collapsed",
        )
        target_vessel = st.selectbox(
            "Target Vessel",
            options=["All Vessels"] + [v["name"] for v in DEMO_FLEET],
            key="cg_voice_target",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_controls:
        st.markdown(
            '<div class="cg-voice-panel">'
            '<div class="cg-voice-panel-title"><span>🎛</span> Playback</div>',
            unsafe_allow_html=True,
        )

        vol = st.slider("Volume", min_value=0, max_value=100, value=80, key="cg_voice_vol",
                        format="%d%%")

        col_play, col_stop, col_test = st.columns(3)
        with col_play:
            if st.button("▶ Play Alert", use_container_width=True, key="cg_play"):
                st.toast(f"🔊 Playing alert in {lang.title()} to {target_vessel}")
        with col_stop:
            if st.button("⏹ Stop", use_container_width=True, type="secondary", key="cg_stop"):
                st.toast("⏹ Alert playback stopped")
        with col_test:
            if st.button("🔔 Test Tone", use_container_width=True, type="secondary", key="cg_test"):
                st.toast("🔔 Test tone sent")

        vol_bar_width = vol
        st.markdown(
            f"""
            <div style="margin-top:0.65rem;">
                <div style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.07em;
                     color:rgba(255,255,255,0.4); margin-bottom:0.35rem; font-weight:700;">
                    Volume · {vol}%
                </div>
                <div style="background:rgba(255,255,255,0.08); border-radius:4px; height:6px;">
                    <div style="background:linear-gradient(90deg, {COLORS['teal']}, {COLORS['sky']});
                         width:{vol_bar_width}%; height:100%; border-radius:4px;
                         transition:width 0.3s ease;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)


# ── Main render ──────────────────────────────────────────────────────────────

def render_coastguard_dashboard() -> None:
    """Render the full Coastguard Control Center dashboard."""
    st.markdown(CG_CSS, unsafe_allow_html=True)
    st.markdown('<div class="cg-root">', unsafe_allow_html=True)

    # Header
    _render_header()

    # Stats row
    _render_stats_row(DEMO_FLEET)

    # ── Map ──────────────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="cg-section">', unsafe_allow_html=True)
        _render_map(DEMO_FLEET)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Boat table ───────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="cg-section">', unsafe_allow_html=True)
        _render_boat_table(DEMO_FLEET)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Alert feed + Analytics side by side ─────────────────────────────────
    col_alerts, col_analytics = st.columns([1, 1], gap="medium")

    with col_alerts:
        st.markdown('<div class="cg-section" style="height:100%;">', unsafe_allow_html=True)
        _render_alert_feed(DEMO_ALERTS)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_analytics:
        st.markdown('<div class="cg-section" style="height:100%;">', unsafe_allow_html=True)
        _render_analytics()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Incident reports + Voice controls side by side ───────────────────────
    col_reports, col_voice = st.columns([3, 2], gap="medium")

    with col_reports:
        st.markdown('<div class="cg-section">', unsafe_allow_html=True)
        _render_incident_reports(DEMO_REPORTS)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_voice:
        st.markdown('<div class="cg-section">', unsafe_allow_html=True)
        _render_voice_controls()
        st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown(
        f"""
        <div style="text-align:center; padding:1rem; margin-top:0.5rem;
             font-size:0.65rem; color:rgba(255,255,255,0.28); letter-spacing:0.04em;">
            SeaSentry AI · Coastguard Control Center · Demo Mode ·
            {datetime.now().strftime('%d %b %Y %H:%M IST')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
