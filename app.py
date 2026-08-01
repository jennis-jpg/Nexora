"""SeaSentry main Streamlit application entry point."""

from __future__ import annotations

import streamlit as st

from controls import DEMO_VESSEL, inject_theme_css, render_brand_header, render_footer
from landing import render_landing_page
from map_view import render_dashboard_layout


def init_session_state() -> None:
    """Initialize navigation and session state variables."""
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "vessel_data" not in st.session_state:
        st.session_state.vessel_data = DEMO_VESSEL.copy()


def render_top_navigation() -> None:
    """Top bar navigation toggle across all pages."""
    col_nav_left, col_nav_mid, col_nav_right = st.columns([2, 1, 1])
    with col_nav_mid:
        page = st.session_state.page
        if page != "dashboard":
            if st.button("⛵ Fisherman Dashboard", use_container_width=True, type="primary"):
                st.session_state.page = "dashboard"
                st.rerun()
        else:
            if st.button("🏠 Home", use_container_width=True, type="secondary"):
                st.session_state.page = "landing"
                st.rerun()
    with col_nav_right:
        page = st.session_state.page
        if page != "coastguard":
            if st.button("🛡 Coastguard Center", use_container_width=True, type="secondary"):
                st.session_state.page = "coastguard"
                st.rerun()
        else:
            if st.button("🏠 Home Landing Page", use_container_width=True, type="secondary"):
                st.session_state.page = "landing"
                st.rerun()


def main() -> None:
    """Main application launcher."""
    st.set_page_config(
        page_title="SeaSentry | Maritime Drift Guard",
        page_icon="⚓",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_session_state()
    inject_theme_css()

    page = st.session_state.page

    if page == "landing":
        render_top_navigation()
        render_landing_page()
    elif page == "coastguard":
        render_top_navigation()
        from pages.coastguard_dashboard import render_coastguard_dashboard
        render_coastguard_dashboard()
        render_footer()
    else:
        render_top_navigation()
        render_brand_header()
        render_dashboard_layout(st.session_state.vessel_data)
        render_footer()


if __name__ == "__main__":
    main()
