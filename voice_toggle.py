"""Voice alert language selector."""

from __future__ import annotations

import streamlit as st

LANGUAGE_OPTIONS = ["kannada", "english"]
LANGUAGE_LABELS = {"kannada": "ಕನ್ನಡ · Kannada", "english": "English"}


def render_voice_toggle(*, key: str = "pc_language", default: str = "kannada") -> str:
    if key not in st.session_state:
        st.session_state[key] = default

    language = st.selectbox(
        "🔊 Voice Alert Language",
        options=LANGUAGE_OPTIONS,
        format_func=lambda v: LANGUAGE_LABELS[v],
        key=key,
        help=(
            "Kannada plays a recorded human voice clip. English uses "
            "browser text-to-speech when no recording is available."
        ),
    )

    if language == "english":
        st.markdown(
            '<div class="pred-field-ok" style="opacity:0.75;">'
            "ℹ using browser text-to-speech (no recorded clip for English yet)"
            "</div>",
            unsafe_allow_html=True,
        )

    return language
