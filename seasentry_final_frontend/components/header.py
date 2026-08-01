"""App header, footer, and page navigation."""

from __future__ import annotations

import streamlit as st

APP_NAME = "SeaSentry AI"
APP_TAGLINE = "AI-powered maritime safety system for fishermen"

PAGES = {
    "landing": {"label": "🏠 Home", "icon": "🏠"},
    "fisherman": {"label": "⛵ Fisherman", "icon": "⛵"},
    "coastguard": {"label": "🛡️ Coastguard", "icon": "🛡️"},
}


def render_brand_header(*, status_text: str = "Monitoring Active") -> None:
    st.markdown(
        f"""
        <div class="brand-bar animate-in">
            <div class="brand-logo">
                <div class="brand-icon">⚓</div>
                <div>
                    <p class="brand-title">{APP_NAME}</p>
                    <p class="brand-subtitle">{APP_TAGLINE}</p>
                </div>
            </div>
            <div class="status-pill">
                <span class="status-dot"></span>
                {status_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(*, extra: str = "") -> None:
    text = f"SeaSentry AI · Maritime Drift Guard · {extra}".strip(" ·")
    st.markdown(f'<div class="dashboard-footer">{text}</div>', unsafe_allow_html=True)


def navigate_to(page: str) -> None:
    st.session_state.page = page
    st.rerun()


def render_page_nav(*, current: str) -> None:
    """Horizontal page switcher — preserves theme button styles."""
    cols = st.columns([1, 1, 1, 2])
    for idx, (page_id, meta) in enumerate(PAGES.items()):
        with cols[idx]:
            btn_type = "primary" if page_id == current else "secondary"
            if st.button(meta["label"], use_container_width=True, type=btn_type, key=f"nav_{page_id}"):
                if page_id != current:
                    navigate_to(page_id)
