"""Reusable metric / status tile components."""

from __future__ import annotations

import streamlit as st


def render_metric_grid(items: list[tuple[str, str, str]]) -> None:
    """Render a 2-column grid of metric tiles. Each item: (label, value, unit)."""
    tiles = "".join(
        '<div class="metric-tile">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>'
        "</div>"
        for label, value, unit in items
    )
    st.markdown(f'<div class="metric-grid">{tiles}</div>', unsafe_allow_html=True)


def render_section_title(icon: str, title: str, *, margin_top: str = "0") -> None:
    st.markdown(
        f'<p class="section-title" style="margin-top:{margin_top};"><span>{icon}</span> {title}</p>',
        unsafe_allow_html=True,
    )
