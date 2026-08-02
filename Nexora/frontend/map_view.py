"""SeaSentry map component and sidebar panels rendering.

The live map used to be a plain `folium` map re-rendered from scratch (as a
big static HTML blob) on every Streamlit rerun via `st_folium`. That made it
impossible to move the boat smoothly, color the predicted route by boundary
crossing, or show a pulsing risk ring -- folium has no animation model, and
`st_folium` round-trips the whole map object through Python on every rerun.

This version renders a small, self-contained Leaflet map through
`st.components.v1.html`. All animation (boat glide between reruns, flowing
route dashes, pulsing risk ring) runs client-side with CSS transitions /
`requestAnimationFrame`, so it costs nothing on the Streamlit/Python side and
never blocks the rest of the app. The route line is split into a blue
"before border" segment and a red "after crossing" segment by computing the
actual geometric intersection of the predicted track with the boundary line.
"""

from __future__ import annotations

import json
import math
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from controls import COLORS, RISK_STYLES

MAP_HEIGHT = 500

# Risk level -> radius (metres) for the pulsing risk ring around the boat.
_RISK_RADIUS_M = {
    "LOW": 700,
    "MEDIUM": 1000,
    "HIGH": 1400,
    "CRITICAL": 1800,
}

_CARDINALS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
              "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _cardinal(deg: float) -> str:
    """8/16-point compass label for a bearing in degrees."""
    idx = int((deg % 360) / 22.5 + 0.5) % 16
    return _CARDINALS[idx]


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_border_points() -> list[dict[str, float]] | None:
    """Fetches the real boundary line from the backend once per hour of
    Streamlit cache (it never changes at runtime). Returns None if the
    backend isn't reachable, so callers can fall back gracefully."""
    try:
        from api_client import call_border
        return call_border()
    except Exception:  # noqa: BLE001 -- backend not up yet, or network issue
        return None


def _segment_intersection(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
) -> tuple[float, float] | None:
    """Intersection of segment p1->p2 with segment p3->p4, each given as
    (lat, lon). Returns (lat, lon) if the segments actually cross, else
    None. Flat lat/lon math is fine at this scale (a few nm)."""
    x1, y1 = p1[1], p1[0]
    x2, y2 = p2[1], p2[0]
    x3, y3 = p3[1], p3[0]
    x4, y4 = p4[1], p4[0]

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return None  # parallel / collinear

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / denom
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (iy, ix)
    return None


def _find_crossing(
    route_start: tuple[float, float],
    route_end: tuple[float, float],
    boundary_coords: list[list[float]],
) -> tuple[float, float] | None:
    """Finds where the predicted route crosses the boundary polyline (first
    hit along the route), if at all."""
    best: tuple[float, float] | None = None
    best_dist = float("inf")
    for i in range(len(boundary_coords) - 1):
        b1 = tuple(boundary_coords[i])
        b2 = tuple(boundary_coords[i + 1])
        hit = _segment_intersection(route_start, route_end, b1, b2)
        if hit is not None:
            d = (hit[0] - route_start[0]) ** 2 + (hit[1] - route_start[1]) ** 2
            if d < best_dist:
                best_dist = d
                best = hit
    return best


def _build_map_payload(vessel: dict[str, Any]) -> dict[str, Any]:
    lat = float(vessel["latitude"])
    lon = float(vessel["longitude"])
    heading_deg = float(vessel["heading_deg"])
    speed_knots = float(vessel["speed_knots"])
    current_dir = float(vessel.get("current_direction_deg", 312))
    wind_dir = float(vessel.get("wind_direction_deg", 278))

    # ── Boundary line (real if backend reachable, else placeholder) ────────
    real_border = _cached_border_points()
    if real_border:
        boundary_coords = [[p["lat"], p["lon"]] for p in real_border]
    else:
        boundary_coords = [
            [lat - 0.5, lon + 0.05],
            [lat, lon + 0.03],
            [lat + 0.5, lon + 0.01],
        ]

    waters_poly = [
        [lat - 0.5, lon + 0.05],
        [lat, lon + 0.03],
        [lat + 0.5, lon + 0.01],
        [lat + 0.5, lon + 0.8],
        [lat - 0.5, lon + 0.8],
    ]

    # ── Predicted position (real dead-reckoning if available) ─────────────
    if "pred_latitude" in vessel and "pred_longitude" in vessel:
        pred_lat = float(vessel["pred_latitude"])
        pred_lon = float(vessel["pred_longitude"])
    else:
        heading_rad = math.radians(heading_deg)
        pred_lat = lat + 0.12 * math.cos(heading_rad)
        pred_lon = lon + 0.12 * math.sin(heading_rad)

    # ── Split the predicted route into a blue ("before border") segment
    # and a red ("after crossing") segment at the real geometric crossing
    # point, so the color change happens exactly where the boat would
    # actually cross the line -- not at an arbitrary midpoint. ────────────
    already_crossed = bool(vessel.get("already_crossed", False))
    crossing_point: tuple[float, float] | None = None
    blue_route: list[list[float]] = []
    red_route: list[list[float]] = []

    if already_crossed:
        crossing_point = (lat, lon)
        red_route = [[lat, lon], [pred_lat, pred_lon]]
    else:
        crossing_point = _find_crossing((lat, lon), (pred_lat, pred_lon), boundary_coords)
        if crossing_point:
            blue_route = [[lat, lon], [crossing_point[0], crossing_point[1]]]
            red_route = [[crossing_point[0], crossing_point[1]], [pred_lat, pred_lon]]
        else:
            blue_route = [[lat, lon], [pred_lat, pred_lon]]

    # ── Environmental vectors (kept from the original view) ───────────────
    current_rad = math.radians(current_dir)
    curr_end = [lat + 0.05 * math.cos(current_rad), lon + 0.05 * math.sin(current_rad)]
    wind_rad = math.radians(wind_dir)
    wind_end = [lat + 0.05 * math.cos(wind_rad), lon + 0.05 * math.sin(wind_rad)]

    # ── Risk styling ────────────────────────────────────────────────────────
    risk_key = vessel.get("risk_level", "MEDIUM")
    risk = RISK_STYLES.get(risk_key, RISK_STYLES["MEDIUM"])
    risk_radius_m = _RISK_RADIUS_M.get(risk_key, 1000)

    # ── Weather summary for the popup ──────────────────────────────────────
    wind_kn = float(vessel.get("wind_speed_kn", 12.4))
    temp_c = vessel.get("temperature_c", 28)
    rain_pct = vessel.get("rain_chance_pct", 15)
    weather_str = f"{temp_c}°C · Wind {wind_kn:.1f} kn {_cardinal(wind_dir)} · Rain {rain_pct}%"

    # ── Previous boat position (for the glide-in animation) ───────────────
    prev = st.session_state.get("_map_prev_boat_pos", [lat, lon])

    boat_id = vessel.get("vessel_id") or vessel.get("boat_id") or "BOAT-1"
    eta_min = vessel.get("eta_to_boundary_min", 999)
    distance_nm = vessel.get("distance_to_boundary_nm", None)

    payload = {
        # Fixed initial center on the Palk Strait so both India and Sri Lanka
        # coastlines are visible on load, regardless of the boat's position.
        "center": [9.4, 79.55],
        "zoom": 9,
        "boundary": boundary_coords,
        "watersPoly": waters_poly,
        "blueRoute": blue_route,
        "redRoute": red_route,
        "crossing": list(crossing_point) if crossing_point else None,
        "pred": {
            "lat": pred_lat,
            "lon": pred_lon,
            "eta": eta_min,
            "distanceNm": distance_nm,
        },
        "boat": {
            "prev": prev,
            "curr": [lat, lon],
            "heading": heading_deg,
            "headingCardinal": _cardinal(heading_deg),
            "speed": speed_knots,
            "riskColor": risk["color"],
            "riskLabel": risk["label"],
            "riskRadiusM": risk_radius_m,
            "boatId": boat_id,
            "eta": eta_min,
            "weather": weather_str,
        },
        "currentVec": {"line": [[lat, lon], curr_end], "speed": vessel.get("current_speed_kn", 1.8), "dir": current_dir},
        "windVec": {"line": [[lat, lon], wind_end], "speed": wind_kn, "dir": wind_dir},
        "colors": COLORS,
        "sosActive": bool(vessel.get("sos_active", False)),
    }
    st.session_state["_map_prev_boat_pos"] = [lat, lon]
    return payload


_MAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body { margin:0; padding:0; background:transparent; }
  #ss-map { width:100%; height:__HEIGHT__px; border-radius:12px; overflow:hidden;
             box-shadow: 0 0 0 1px rgba(255,255,255,0.08); }
  .leaflet-container { background:#031B34; font-family:'Inter', sans-serif; }

  /* ── Boat marker ─────────────────────────────────────────────────────── */
  .ss-boat-wrap { position:relative; width:0; height:0; }
  .ss-boat-bob { animation: ss-bob 2.6s ease-in-out infinite; }
  @keyframes ss-bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
  .ss-boat-rot { transform-origin: 50% 50%; transition: transform 0.6s ease; }
  .ss-boat-svg { display:block; filter: drop-shadow(0 0 4px rgba(0,0,0,0.55)); }

  /* Pulsing risk ring, purely CSS -- cheap and runs forever without any JS work */
  .ss-risk-ring { position:absolute; left:50%; top:50%; border-radius:50%;
                  transform: translate(-50%,-50%) scale(0.4); opacity:0.9;
                  animation: ss-pulse 2.2s cubic-bezier(0.4,0,0.3,1) infinite; pointer-events:none; }
  .ss-risk-ring.r2 { animation-delay: 0.9s; }
  @keyframes ss-pulse {
    0%   { transform: translate(-50%,-50%) scale(0.35); opacity:0.55; }
    70%  { transform: translate(-50%,-50%) scale(1.15); opacity:0; }
    100% { transform: translate(-50%,-50%) scale(1.15); opacity:0; }
  }

  /* Flowing "marching ants" dash animation for route lines */
  .ss-route-blue, .ss-route-red { animation: ss-dash 1.1s linear infinite; }
  @keyframes ss-dash { to { stroke-dashoffset: -24; } }

  .ss-crossing-icon { display:flex; align-items:center; justify-content:center;
                       width:26px; height:26px; border-radius:50%;
                       background:#E53935; border:2px solid #fff;
                       box-shadow: 0 0 8px rgba(229,57,53,0.9);
                       animation: ss-crossing-pulse 1.4s ease-in-out infinite; font-size:13px; }
  @keyframes ss-crossing-pulse { 0%,100% { box-shadow:0 0 4px rgba(229,57,53,0.7);} 50% { box-shadow:0 0 14px rgba(229,57,53,1);} }

  .ss-popup { font-family:'Inter', sans-serif; font-size:12.5px; color:#111; min-width:190px; }
  .ss-popup h4 { margin:0 0 6px 0; font-size:13.5px; }
  .ss-popup table { border-collapse: collapse; width:100%; }
  .ss-popup td { padding:2px 0; vertical-align:top; }
  .ss-popup td.k { color:#555; padding-right:8px; white-space:nowrap; }
  .ss-popup td.v { font-weight:600; text-align:right; }
  .leaflet-popup-content-wrapper { border-radius:10px; }
</style>
</head>
<body>
<div id="ss-map"></div>
<script>
const DATA = __DATA_JSON__;

const map = L.map('ss-map', { zoomControl: true, attributionControl: false })
  .setView(DATA.center, DATA.zoom);

const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  maxZoom: 19, attribution: '&copy; OpenStreetMap &copy; CARTO'
}).addTo(map);

const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  maxZoom: 19, attribution: 'Esri World Imagery'
});

L.control.layers({ 'Dark Base': darkLayer, 'Satellite': satLayer }, {}, { position: 'topright', collapsed: false }).addTo(map);

// ── Permanent geography: coastlines (coordinates from boundary.geojson) ──
const INDIA_COAST = [
  [10.40,79.00],[10.30,79.35],[10.00,79.50],[9.85,79.30],
  [9.68,79.18],[9.50,79.21],[9.35,79.12],[9.20,79.20],
  [9.05,79.10],[9.05,78.80],[10.40,78.80]
];
const SL_COAST = [
  [9.85,79.70],[9.90,80.10],[9.70,80.35],[8.85,80.35],
  [8.85,79.90],[9.05,79.72],[9.20,79.60],[9.45,79.65],[9.85,79.70]
];
L.polygon(INDIA_COAST, {
  color:'rgba(255,255,255,0.15)', weight:1.5,
  fill:true, fillColor:'#0f3d5c', fillOpacity:0.88
}).addTo(map).bindTooltip('India — Tamil Nadu Coast');
L.polygon(SL_COAST, {
  color:'rgba(255,255,255,0.15)', weight:1.5,
  fill:true, fillColor:'#0f3d2f', fillOpacity:0.88
}).addTo(map).bindTooltip('Sri Lanka — Northern Coast');

// ── Maritime boundary ────────────────────────────────────────────────────
L.polyline(DATA.boundary, {
  color: DATA.colors.red, weight: 3, dashArray: '8, 8'
}).addTo(map).bindTooltip('International Maritime Boundary (EEZ)');

// ── IMBL vertex dots (B1-B6) + midpoint label ─────────────────────────
const IMBL_PTS = [
  [10.0833,80.0500],[9.9500,79.5833],[9.6692,79.3767],
  [9.3633,79.5117],[9.2167,79.5333],[9.1000,79.5333]
];
IMBL_PTS.forEach(([lat,lon],i) => {
  L.circleMarker([lat,lon],{
    radius:4, color:DATA.colors.red, fill:true,
    fillColor:DATA.colors.red, fillOpacity:1, weight:1.5
  }).addTo(map).bindTooltip(`B${i+1} — IMBL Vertex`);
});
const imblMid = IMBL_PTS[Math.floor(IMBL_PTS.length/2)];
L.marker(imblMid,{
  icon:L.divIcon({className:'',
    html:'<div style="font-size:10px;font-weight:800;color:rgba(229,57,53,0.92);letter-spacing:0.08em;text-shadow:0 1px 3px #000;pointer-events:none;">IMBL</div>',
    iconAnchor:[-4,6]}),
  interactive:false,keyboard:false
}).addTo(map);

L.polygon(DATA.watersPoly, {
  color: DATA.colors.red, weight: 1, fill: true, fillColor: DATA.colors.red, fillOpacity: 0.15
}).addTo(map).bindPopup('<b>Zone: International Waters</b><br>High Risk Crossing Zone');

// ── Country labels on either side of the boundary ───────────────────────
if (DATA.boundary && DATA.boundary.length >= 2) {
  const midIdx = Math.floor(DATA.boundary.length / 2);
  const mLat = DATA.boundary[midIdx][0];
  const mLon = DATA.boundary[midIdx][1];
  const labelStyle = 'font-size:13px;font-weight:700;white-space:nowrap;text-shadow:0 1px 4px #000;pointer-events:none;';
  L.marker([mLat, mLon - 0.55], {
    icon: L.divIcon({ className: '',
      html: `<div style="${labelStyle}color:rgba(255,255,255,0.8);">🇮🇳 India</div>`,
      iconAnchor: [42, 10] }),
    interactive: false, keyboard: false
  }).addTo(map);
  L.marker([mLat, mLon + 0.55], {
    icon: L.divIcon({ className: '',
      html: `<div style="${labelStyle}color:rgba(229,57,53,0.92);">🇱🇰 Sri Lanka</div>`,
      iconAnchor: [0, 10] }),
    interactive: false, keyboard: false
  }).addTo(map);
}

// ── Place labels (towns from boundary.geojson) ────────────────────────
const PLACES = [
  {lat:9.2876,lon:79.3129,name:'Rameswaram',side:'india'},
  {lat:9.2748,lon:79.1224,name:'Mandapam',side:'india'},
  {lat:9.2810,lon:79.2116,name:'Pamban',side:'india'},
  {lat:9.1197,lon:79.4177,name:'Dhanushkodi',side:'india'},
  {lat:9.0833,lon:79.7167,name:'Talaimannar',side:'srilanka'},
  {lat:9.6615,lon:80.0255,name:'N. Sri Lanka',side:'srilanka'},
];
PLACES.forEach(p => {
  const c = p.side==='india' ? 'rgba(159,216,255,0.72)' : 'rgba(144,238,144,0.65)';
  L.circleMarker([p.lat,p.lon],{radius:2.5,color:c,fill:true,fillColor:c,fillOpacity:1,weight:0}).addTo(map);
  L.marker([p.lat,p.lon],{
    icon:L.divIcon({className:'',
      html:`<div style="font-size:9px;color:${c};white-space:nowrap;text-shadow:0 1px 2px rgba(0,0,0,0.9);pointer-events:none;padding-left:5px;">${p.name}</div>`,
      iconAnchor:[0,5]}),
    interactive:false,keyboard:false
  }).addTo(map);
});

// ── Predicted route: blue before the border, red after crossing ────────
if (DATA.blueRoute && DATA.blueRoute.length) {
  L.polyline(DATA.blueRoute, {
    color: DATA.colors.sky, weight: 4, opacity: 0.95,
    dashArray: '10, 8', className: 'ss-route-blue'
  }).addTo(map).bindTooltip('Predicted route (before border)');
}
if (DATA.redRoute && DATA.redRoute.length) {
  L.polyline(DATA.redRoute, {
    color: DATA.colors.red, weight: 4, opacity: 0.95,
    dashArray: '10, 8', className: 'ss-route-red'
  }).addTo(map).bindTooltip('Predicted route (after crossing)');
}

// ── Crossing marker ──────────────────────────────────────────────────────
if (DATA.crossing) {
  L.marker(DATA.crossing, {
    icon: L.divIcon({
      className: '', html: '<div class="ss-crossing-icon">&#9888;</div>',
      iconSize: [26, 26], iconAnchor: [13, 13]
    })
  }).addTo(map).bindTooltip('Predicted Boundary Crossing', { direction: 'top' });
}

// ── Predicted end position marker ───────────────────────────────────────
const predPopup = `
  <div class="ss-popup">
    <h4 style="color:${DATA.colors.sky};">Projected Position</h4>
    <table>
      <tr><td class="k">ETA to boundary</td><td class="v">${DATA.pred.eta} min</td></tr>
      <tr><td class="k">Distance remaining</td><td class="v">${DATA.pred.distanceNm ?? '—'} nm</td></tr>
    </table>
  </div>`;
L.circleMarker([DATA.pred.lat, DATA.pred.lon], {
  radius: 6, color: DATA.colors.sky, fill: true, fillColor: DATA.colors.navy,
  fillOpacity: 0.9, weight: 2
}).addTo(map).bindTooltip('Predicted Position (30 min horizon)').bindPopup(predPopup);

// ── Environmental vectors ───────────────────────────────────────────────
L.polyline(DATA.currentVec.line, { color: DATA.colors.teal, weight: 2 })
  .addTo(map).bindTooltip(`Ocean Current (${DATA.currentVec.speed} kn @ ${DATA.currentVec.dir}°)`);
L.polyline(DATA.windVec.line, { color: DATA.colors.sky, weight: 2, dashArray: '3,3' })
  .addTo(map).bindTooltip(`Wind Vector (${DATA.windVec.speed} kn @ ${DATA.windVec.dir}°)`);

// ── Risk circle + boat marker (divIcon so CSS animation is free) ───────
const b = DATA.boat;
function boatIconHtml(headingDeg) {
  return `
    <div class="ss-boat-wrap">
      <div class="ss-risk-ring r1" style="width:34px;height:34px;background:${b.riskColor}22;border:2px solid ${b.riskColor};"></div>
      <div class="ss-risk-ring r2" style="width:34px;height:34px;background:${b.riskColor}22;border:2px solid ${b.riskColor};"></div>
      <div class="ss-boat-bob">
        <div class="ss-boat-rot" style="transform:translate(-50%,-50%) rotate(${headingDeg}deg);position:absolute;left:50%;top:50%;">
          <svg class="ss-boat-svg" width="26" height="26" viewBox="-13 -13 26 26">
            <circle cx="0" cy="0" r="11" fill="${b.riskColor}22"/>
            <path d="M 0,-9 L 6,7 L 0,4 L -6,7 Z" fill="#FFFFFF" stroke="rgba(0,21,34,0.85)" stroke-width="0.9"/>
          </svg>
        </div>
      </div>
    </div>`;
}

const boatMarker = L.marker(b.prev, {
  icon: L.divIcon({ className: '', html: boatIconHtml(b.heading), iconSize: [34, 34], iconAnchor: [17, 17] }),
  zIndexOffset: 1000
}).addTo(map);

const popupHtml = `
  <div class="ss-popup">
    <h4 style="color:${b.riskColor};">&#9875; ${b.boatId}</h4>
    <table>
      <tr><td class="k">Speed</td><td class="v">${b.speed.toFixed(1)} kn</td></tr>
      <tr><td class="k">Heading</td><td class="v">${b.heading}&deg; ${b.headingCardinal}</td></tr>
      <tr><td class="k">ETA</td><td class="v">${b.eta} min</td></tr>
      <tr><td class="k">Risk</td><td class="v" style="color:${b.riskColor};">${b.riskLabel}</td></tr>
      <tr><td class="k">Latitude</td><td class="v">${b.curr[0].toFixed(4)}&deg;</td></tr>
      <tr><td class="k">Longitude</td><td class="v">${b.curr[1].toFixed(4)}&deg;</td></tr>
      <tr><td class="k">Weather</td><td class="v">${b.weather}</td></tr>
    </table>
  </div>`;
boatMarker.bindPopup(popupHtml, { maxWidth: 240 });
boatMarker.bindTooltip('Current Vessel Position (click for telemetry)');

// ── Smoothly glide the boat from its previous rendered position to the
// current one (rAF tween), instead of snapping -- this is what makes the
// icon feel like it's actually moving across reruns. Bounded duration so
// it never keeps looping / never costs anything after ~900ms. ───────────
(function animate() {
  const from = b.prev, to = b.curr;
  const dLat = to[0] - from[0], dLon = to[1] - from[1];
  if (Math.abs(dLat) < 1e-9 && Math.abs(dLon) < 1e-9) return;
  const duration = 900;
  const start = performance.now();
  function ease(t) { return 1 - Math.pow(1 - t, 3); }
  function step(now) {
    const t = Math.min(1, (now - start) / duration);
    const e = ease(t);
    boatMarker.setLatLng([from[0] + dLat * e, from[1] + dLon * e]);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
})();

// ── SOS active marker (shown when vessel has already crossed the line) ───
if (DATA.sosActive) {
  L.marker(b.curr, {
    icon: L.divIcon({
      className: '',
      html: `<div style="position:relative;width:42px;height:42px;">
        <div style="position:absolute;inset:0;border-radius:50%;border:2.5px solid ${DATA.colors.red};animation:ss-crossing-pulse 1.4s ease-in-out infinite;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:10px;height:10px;border-radius:50%;background:${DATA.colors.red};box-shadow:0 0 10px ${DATA.colors.red};"></div>
        <div style="position:absolute;top:100%;left:50%;transform:translateX(-50%);margin-top:4px;font-size:10px;font-weight:800;color:${DATA.colors.red};white-space:nowrap;letter-spacing:0.05em;text-shadow:0 1px 3px #000;">SOS</div>
      </div>`,
      iconSize: [42, 42],
      iconAnchor: [21, 21]
    }),
    zIndexOffset: 2000
  }).addTo(map);
}

// Fit the view to include the boat, its predicted position, and the boundary.
try {
  const bounds = L.latLngBounds([b.curr, [DATA.pred.lat, DATA.pred.lon], ...DATA.boundary]);
  map.fitBounds(bounds.pad(0.35));
} catch (e) { /* fall back to the initial setView above */ }
</script>
</body>
</html>
"""


def create_sea_map(vessel: dict[str, Any]) -> str:
    """Builds the self-contained Leaflet map HTML for the given vessel."""
    payload = _build_map_payload(vessel)
    data_json = json.dumps(payload).replace("</", "<\\/")
    html = _MAP_HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    html = html.replace("__HEIGHT__", str(MAP_HEIGHT))
    return html


def render_map_panel(vessel: dict[str, Any]) -> None:
    """Render original map panel container with enhanced legend."""
    st.markdown(
        """
        <div class="map-header">
            <span class="map-title">🗺️ Live Drift Map</span>
            <span class="status-pill">DEMO · REAL-TIME VECTORING</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    html = create_sea_map(vessel)
    components.html(html, height=MAP_HEIGHT, scrolling=False)

    st.markdown(
        f"""
        <div class="map-legend">
            <div class="legend-item">
                <span class="legend-swatch" style="background:#fff; clip-path:polygon(50% 0%,100% 100%,50% 70%,0% 100%);"></span> Vessel
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:{COLORS['sky']};"></span> Safe Path
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:{COLORS['red']};"></span> After Crossing
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:{COLORS['red']}; opacity:0.35;"></span> Int'l Waters
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:#0f3d5c;border:1px solid rgba(255,255,255,0.25);"></span> India
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:#0f3d2f;border:1px solid rgba(255,255,255,0.25);"></span> Sri Lanka
            </div>
            <div class="legend-item">
                <span class="legend-swatch" style="background:{COLORS['teal']};"></span> Ocean Current
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_layout(vessel: dict[str, Any]) -> None:
    """Main dashboard layout — reference-inspired 2-column with live timeline."""
    from controls import (
        render_alert_panel,
        render_env_conditions,
        render_metrics_row,
        render_prediction_controls,
        render_top_kpi_row,
    )
    from components.timeline import add_event, init_timeline, render_timeline

    init_timeline()

    # ── Timeline: detect risk changes, crossing events, prediction updates ──
    curr_risk = vessel.get("risk_level", "LOW")
    prev_risk = st.session_state.get("_tl_dash_last_risk")
    if prev_risk is not None and prev_risk != curr_risk:
        _risk_icons = {"LOW": "✓", "MEDIUM": "⚠", "HIGH": "⛔", "CRITICAL": "🚨"}
        add_event(
            f"{_risk_icons.get(curr_risk, '⚠')} Risk level changed to {curr_risk}",
            is_sos=curr_risk in ("HIGH", "CRITICAL"),
        )
    st.session_state["_tl_dash_last_risk"] = curr_risk

    crossed = bool(vessel.get("already_crossed", False))
    if crossed and not st.session_state.get("_tl_dash_crossed_logged"):
        add_event("⛔ Boundary crossing detected!", is_sos=True)
        st.session_state["_tl_dash_crossed_logged"] = True
    if not crossed:
        st.session_state["_tl_dash_crossed_logged"] = False

    pred_lat = vessel.get("pred_latitude")
    if pred_lat is not None and pred_lat != st.session_state.get("_tl_dash_last_pred"):
        eta = vessel.get("eta_to_boundary_min", "?")
        add_event(f"📍 Prediction updated · ETA {eta} min to boundary")
        st.session_state["_tl_dash_last_pred"] = pred_lat

    # ── Live input preview: map tracks widget values before "Predict" ───────
    # Streamlit flushes widget state to session_state at the START of every
    # rerun, so we read pc_lat/pc_lon/etc. here before the controls run and
    # pass them to the map — that makes the map update in real time as the
    # user types, without waiting for the next prediction click.
    preview_vessel = dict(vessel)
    preview_vessel["latitude"] = st.session_state.get("pc_lat", vessel["latitude"])
    preview_vessel["longitude"] = st.session_state.get("pc_lon", vessel["longitude"])
    preview_vessel["heading_deg"] = st.session_state.get("pc_heading", vessel["heading_deg"])
    preview_vessel["speed_knots"] = st.session_state.get("pc_speed", vessel["speed_knots"])
    preview_vessel.pop("pred_latitude", None)
    preview_vessel.pop("pred_longitude", None)
    preview_vessel["sos_active"] = crossed

    render_top_kpi_row(vessel)

    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        render_map_panel(preview_vessel)
        render_prediction_controls()

    with col_right:
        render_timeline()
        render_alert_panel(vessel)
        render_metrics_row(vessel)
        render_env_conditions(vessel)
