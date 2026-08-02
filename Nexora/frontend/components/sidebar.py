"""Role-based sidebar navigation."""

from __future__ import annotations

import streamlit as st

from components.header import APP_NAME, APP_TAGLINE, PAGES, navigate_to


def render_sidebar(*, current_page: str) -> None:
    """Compact sidebar with role selection — uses Streamlit sidebar, themed via CSS."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding:0.5rem 0 1rem;">
                <div style="font-size:1.8rem;">⚓</div>
                <div style="font-size:1rem; font-weight:700; color:white;">{APP_NAME}</div>
                <div style="font-size:0.65rem; color:rgba(255,255,255,0.5); letter-spacing:0.04em; margin-top:0.25rem;">
                    {APP_TAGLINE}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            '<p class="section-title"><span>📍</span> Navigate</p>',
            unsafe_allow_html=True,
        )

        for page_id, meta in PAGES.items():
            is_active = page_id == current_page
            label = f"{'▸ ' if is_active else ''}{meta['label']}"
            if st.button(label, use_container_width=True, type="primary" if is_active else "secondary", key=f"sb_{page_id}"):
                if not is_active:
                    navigate_to(page_id)

        st.markdown("---")
        st.markdown(
            """
            <div style="font-size:0.68rem; color:rgba(255,255,255,0.4); line-height:1.5; padding:0.5rem;">
                <strong style="color:rgba(255,255,255,0.55);">Fisherman</strong> — drift alerts &amp; voice warnings<br>
                <strong style="color:rgba(255,255,255,0.55);">Coastguard</strong> — fleet priority view
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("coastguard_authenticated"):
            st.markdown("---")
            st.markdown(
                '<div style="font-size:0.62rem; color:rgba(255,255,255,0.35); '
                'text-transform:uppercase; letter-spacing:0.06em; padding:0 0 0.4rem 0; '
                'font-weight:600;">Coastguard Session</div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "🔒 Log Out",
                use_container_width=True,
                type="secondary",
                key="sb_cg_logout",
            ):
                st.session_state.pop("coastguard_authenticated", None)
                st.session_state.pop("coastguard_key", None)
                st.session_state.pop("_cg_auth_error", None)
                navigate_to("landing")
