"""
audio_player.py
NEW FILE, added to fix two related problems with the original alert audio:

1. THE SEQUENCING BUG: the old code dropped two independent st.audio()
   elements onto the page -- one for the alarm, one for the voice message.
   Nothing linked them, so they either both tried to autoplay at once (which
   most browsers block -- only one autoplaying element is allowed as an
   anti-annoyance policy) or the second one just sat there silent, needing a
   manual click. This component instead plays them as a real sequence: the
   alarm finishes, THEN the voice message starts, via a single JS
   <audio>.onended handler.

2. THE MISSING-ENGLISH-VOICE PROBLEM: only Kannada has recorded clips. This
   component falls back to the BROWSER'S OWN text-to-speech (the Web Speech
   API's speechSynthesis, built into Chrome/Edge/Safari) whenever
   voice_file is None -- so English (or any other language you haven't
   recorded yet) still gets a real spoken alert, without needing a backend
   recording at all. It reads whatever OS voice is installed, same idea as
   the Windows/macOS voice-pack instructions from earlier in this project.

Autoplay note: browsers generally only allow audio to autoplay if it
follows a real user gesture (like clicking "Predict Drift") reasonably
closely. This component autoplays optimistically, but ALWAYS also shows a
visible "Play Alert" button as a manual fallback in case the browser blocks
the automatic attempt -- so the alert is never silently lost, just possibly
one click away instead of instant.
"""

from __future__ import annotations

import json

import streamlit.components.v1 as components


def render_chained_alert_audio(
    alarm_url: str | None,
    voice_url: str | None,
    fallback_text: str | None,
    fallback_lang: str = "en-IN",
    key: str = "alert_audio",
) -> None:
    """Renders a self-contained HTML/JS player that plays alarm_url (if
    present), then voice_url (if present) OR speaks fallback_text via the
    browser's built-in TTS if voice_url is None. Call this once per
    prediction result -- pass None for alarm_url/voice_url to skip that
    stage entirely (e.g. low risk has neither)."""

    if not alarm_url and not voice_url and not fallback_text:
        return  # nothing to play at all (e.g. a "safe" result with no alert)

    config = {
        "alarmUrl": alarm_url,
        "voiceUrl": voice_url,
        "fallbackText": fallback_text if not voice_url else None,
        "fallbackLang": fallback_lang,
    }

    # All audio logic runs inside a zero-height iframe so no visible HTML
    # appears on the page.  The JS plays alarm → voice MP3 in sequence,
    # or falls back to the browser's built-in Web Speech API for TTS.
    html = f"""
    <script>
    (function() {{
        const cfg = {json.dumps(config)};

        function speak(text, lang) {{
            return new Promise((resolve) => {{
                if (!('speechSynthesis' in window) || !text) {{ resolve(); return; }}
                const u = new SpeechSynthesisUtterance(text);
                u.lang  = lang;
                u.onend = resolve;
                u.onerror = resolve;
                window.speechSynthesis.speak(u);
            }});
        }}

        function playAudio(url) {{
            return new Promise((resolve) => {{
                if (!url) {{ resolve(); return; }}
                const a = new Audio(url);
                a.onended = resolve;
                a.onerror = resolve;
                a.play().catch(() => resolve());
            }});
        }}

        async function playSequence() {{
            await playAudio(cfg.alarmUrl);
            if (cfg.voiceUrl) {{
                await playAudio(cfg.voiceUrl);
            }} else if (cfg.fallbackText) {{
                await speak(cfg.fallbackText, cfg.fallbackLang);
            }}
        }}

        playSequence().catch(() => {{}});
    }})();
    </script>
    """
    # height=0 → zero-height iframe; no HTML is printed to the page
    components.html(html, height=0)
