import streamlit as st
import streamlit.components.v1 as components

def render_chained_alert_audio(audio_urls: list[str], lang: str = "kannada"):
    """
    Renders audio player with browser autoplay safety and explicit manual controls.
    """
    if not audio_urls:
        st.warning("No audio tracks available.")
        return

    # Fallback visible player for blocked autoplay
    st.markdown(f"**🔊 Audio Notice ({lang.upper()})**")
    for url in audio_urls:
        st.audio(url, format="audio/mp3")

    # Hidden chained Javascript player for auto-play sequence
    js_urls = str(audio_urls).replace("'", '"')
    html_code = f"""
    <script>
        const urls = {js_urls};
        let currentIndex = 0;
        
        function playNext() {{
            if (currentIndex < urls.length) {{
                let audio = new Audio(urls[currentIndex]);
                audio.play().then(() => {{
                    currentIndex++;
                    audio.onended = playNext;
                }}).catch(err => {{
                    console.log("Autoplay blocked by browser. User gesture required.", err);
                }});
            }}
        }}
        playNext();
    </script>
    """
    components.html(html_code, height=0)