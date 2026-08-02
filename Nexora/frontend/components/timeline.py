"""Scrollable event-feed timeline for the SeaSentry dashboard.

Events are stored in st.session_state["timeline_events"] so they persist
across reruns and accumulate through a session. The list is capped at 30
entries (oldest dropped first) to avoid unbounded growth.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

_MAX_EVENTS = 30


def init_timeline() -> None:
    """Initialise the event list exactly once per browser session."""
    if "timeline_events" not in st.session_state:
        st.session_state.timeline_events = []
        _append("Tracking session started", is_sos=False)


def add_event(label: str, is_sos: bool = False) -> None:
    """Append a new event. Call init_timeline() before the first add_event()."""
    _append(label, is_sos)


def _append(label: str, is_sos: bool) -> None:
    events: list[dict] = st.session_state.get("timeline_events", [])
    events.append({
        "label": label,
        "time": datetime.now().strftime("%H:%M"),
        "is_sos": is_sos,
    })
    st.session_state.timeline_events = events[-_MAX_EVENTS:]


def render_timeline() -> None:
    """Render the timeline as a glassmorphism card using st.markdown."""
    if "timeline_events" not in st.session_state:
        init_timeline()

    events: list[dict] = st.session_state.get("timeline_events", [])

    if not events:
        items_html = '<li style="color:rgba(255,255,255,0.4);font-size:0.85rem;">No active incidents</li>'
    else:
        rows = []
        for e in reversed(events):
            dot_color = "#E53935" if e["is_sos"] else "#4DB6FF"
            glow = "box-shadow:0 0 6px #E53935;" if e["is_sos"] else ""
            rows.append(f"""
              <li>
                <span class="tl-dot" style="background:{dot_color};{glow}"></span>
                <div>
                  <span class="tl-time">{e["time"]}</span>
                  <div class="tl-label">{e["label"]}</div>
                </div>
              </li>""")
        items_html = "".join(rows)

    st.markdown(
        f"""
        <div class="ss-tl-card">
          <div class="tl-hdr">📋 Event Log</div>
          <ul class="tl-list">{items_html}</ul>
        </div>
        <style>
        .ss-tl-card {{
          background:rgba(255,255,255,0.06);
          border:1px solid rgba(255,255,255,0.12);
          border-radius:16px;
          padding:0.9rem 1.05rem;
          margin-bottom:0.85rem;
        }}
        .tl-hdr {{
          font-size:0.72rem;
          text-transform:uppercase;
          letter-spacing:0.07em;
          color:rgba(255,255,255,0.48);
          font-weight:700;
          margin-bottom:0.7rem;
        }}
        .tl-list {{
          list-style:none;
          padding:0;
          margin:0;
          max-height:190px;
          overflow-y:auto;
          display:flex;
          flex-direction:column;
          gap:0.6rem;
          scrollbar-width:thin;
          scrollbar-color:rgba(255,255,255,0.2) transparent;
        }}
        .tl-list li {{
          display:flex;
          gap:0.6rem;
          align-items:flex-start;
        }}
        .tl-dot {{
          width:9px;height:9px;border-radius:50%;
          flex-shrink:0;margin-top:0.28rem;
        }}
        .tl-time {{
          font-size:0.7rem;color:rgba(255,255,255,0.42);
          display:block;margin-bottom:1px;
        }}
        .tl-label {{
          font-size:0.83rem;color:rgba(255,255,255,0.85);
          line-height:1.35;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
