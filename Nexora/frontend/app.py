"""SeaSentry | Maritime Drift Guard — main Streamlit entry point.

Page routing
------------
  landing    → landing.render_landing_page()
  fisherman  → pages/fisherman_dashboard.render_fisherman_dashboard()
  coastguard → pages/coastguard_dashboard.render_coastguard_dashboard()
  dashboard  → map_view.render_dashboard_layout()  (operator / fallback)

SOS email configuration (optional)
------------------------------------
Set these environment variables (or add them to frontend/.env) to enable
real email dispatch when the fisherman triggers an SOS:

    SMTP_HOST        SMTP server hostname  (e.g. smtp.gmail.com)
    SMTP_PORT        Port number           (default: 587)
    SMTP_USER        Sender email address
    SMTP_PASS        Sender password / app-specific password
    COASTGUARD_EMAIL Recipient address     (default: coastguard@seasentry.example.com)
    TRACKING_URL     Live dashboard URL    (default: http://localhost:8501)

When SMTP vars are absent the SOS still activates, the PDF is generated,
and the UI shows "Email Simulated" so the demo works without any config.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# Load frontend/.env before any module reads os.environ
load_dotenv(Path(__file__).parent / ".env", override=False)

import streamlit as st

from controls import DEMO_VESSEL, inject_theme_css, render_brand_header, render_footer
from landing import render_landing_page
from map_view import render_dashboard_layout


# ══════════════════════════════════════════════════════════════════════════════
# Session state
# ══════════════════════════════════════════════════════════════════════════════

def _init_session_state() -> None:
    """Seed top-level navigation and vessel data once per session."""
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "vessel_data" not in st.session_state:
        st.session_state.vessel_data = DEMO_VESSEL.copy()


# ══════════════════════════════════════════════════════════════════════════════
# Navigation bar
# ══════════════════════════════════════════════════════════════════════════════

def _render_top_navigation() -> None:
    """Persistent top-bar with Fisherman and Coastguard navigation buttons.

    Button logic:
      • "Fisherman Dashboard" is shown on every page EXCEPT the fisherman page.
        Clicking it sets page = "fisherman" (previously it set "dashboard" —
        that was the bug that caused fishermen to see the operator view).
      • "Coastguard Center" / "Home" toggle for the right column.
    """
    _, col_mid, col_right = st.columns([2, 1, 1])

    with col_mid:
        page = st.session_state.page
        if page != "fisherman":
            if st.button("⛵ Fisherman Dashboard",
                         use_container_width=True, type="primary",
                         key="nav_fisherman"):
                st.session_state.page = "fisherman"
                st.rerun()
        else:
            if st.button("🏠 Home",
                         use_container_width=True, type="secondary",
                         key="nav_home_from_fisherman"):
                st.session_state.page = "landing"
                st.rerun()

    with col_right:
        page = st.session_state.page
        if page != "coastguard":
            if st.button("🛡 Coastguard Center",
                         use_container_width=True, type="secondary",
                         key="nav_coastguard"):
                st.session_state.page = "coastguard"
                st.rerun()
        else:
            if st.button("🏠 Home",
                         use_container_width=True, type="secondary",
                         key="nav_home_from_cg"):
                st.session_state.page = "landing"
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    st.set_page_config(
        page_title="SeaSentry | Maritime Drift Guard",
        page_icon="⚓",
        layout="wide",
        # Sidebar starts collapsed on all pages; the fisherman dashboard's
        # simulation controls expand it automatically via user interaction.
        initial_sidebar_state="collapsed",
    )

    _init_session_state()
    inject_theme_css()

    page = st.session_state.page

    if page == "landing":
        _render_top_navigation()
        render_landing_page()

    elif page == "fisherman":
        # Sidebar will contain simulation controls + voice toggle rendered
        # by render_fisherman_dashboard → _render_sidebar()
        _render_top_navigation()
        from pages.fisherman_dashboard import render_fisherman_dashboard
        render_fisherman_dashboard(st.session_state.vessel_data)
        render_footer()

    elif page == "coastguard":
        _render_top_navigation()
        from pages.coastguard_dashboard import render_coastguard_dashboard
        render_coastguard_dashboard()
        render_footer()

    else:
        # "dashboard" and any unknown page → operator / main view
        _render_top_navigation()
        render_brand_header()
        render_dashboard_layout(st.session_state.vessel_data)
        render_footer()


if __name__ == "__main__":
    main()
