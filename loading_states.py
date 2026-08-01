"""Loading state helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import streamlit as st


LOADING_CSS = """
.loading-skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.04) 75%);
    background-size: 200% 100%;
    animation: skeleton-shimmer 1.4s ease-in-out infinite;
    border-radius: 12px;
    height: 48px;
    margin-bottom: 0.5rem;
}
@keyframes skeleton-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
.loading-banner {
    display: flex; align-items: center; gap: 0.65rem;
    padding: 0.75rem 1rem; border-radius: 14px;
    background: rgba(77, 182, 255, 0.1);
    border: 1px solid rgba(77, 182, 255, 0.25);
    font-size: 0.82rem; color: rgba(255,255,255,0.75);
    margin-bottom: 0.85rem;
}
"""


def inject_loading_css() -> None:
    st.markdown(f"<style>{LOADING_CSS}</style>", unsafe_allow_html=True)


def render_loading_banner(message: str = "Loading data…") -> None:
    inject_loading_css()
    st.markdown(
        f'<div class="loading-banner"><span>⏳</span> {message}</div>',
        unsafe_allow_html=True,
    )


def render_skeleton_rows(count: int = 3) -> None:
    inject_loading_css()
    st.markdown("".join('<div class="loading-skeleton"></div>' for _ in range(count)), unsafe_allow_html=True)


@contextmanager
def loading_spinner(message: str = "Contacting backend…") -> Generator[None, None, None]:
    with st.spinner(message):
        yield
