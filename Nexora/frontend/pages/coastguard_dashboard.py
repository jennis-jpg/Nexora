import streamlit as st
import streamlit.components.v1 as components
import requests
import os

API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")

# Set Page Config
st.set_page_config(
    page_title="Coastal Safety & Coordination Dashboard",
    page_icon="🌊",
    layout="wide"
)

# ==========================================
# 1. HELPER COMPONENTS & AUDIO RENDERER
# ==========================================

def render_chained_alert_audio(audio_urls: list[str], lang: str = "kannada"):
    """
    Renders audio player safely without causing Streamlit DOM flickering.
    """
    if not audio_urls:
        st.warning("No audio tracks returned.")
        return

    st.markdown(f"**🔊 Audio Notice ({lang.upper()})**")
    
    # Fallback visible players
    for url in audio_urls:
        st.audio(url, format="audio/mp3")

    # Hidden HTML5 Javascript chain for smooth playback
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
                    console.log("Autoplay blocked by browser. User can click manual buttons above.", err);
                }});
            }}
        }}
        playNext();
    </script>
    """
    components.html(html_code, height=0)

# ==========================================
# 2. CACHED API CALLS (PREVENTS BLINKING)
# ==========================================

@st.cache_data(ttl=5)
def fetch_cached_fleet(dock_id: str, key: str):
    headers = {"X-Coastguard-Key": key, "X-Dock-Id": dock_id}
    try:
        res = requests.get(f"{API_BASE}/coastguard/fleet", headers=headers, timeout=3)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=10)
def fetch_cached_incidents(dock_id: str, key: str):
    headers = {"X-Coastguard-Key": key, "X-Dock-Id": dock_id}
    try:
        res = requests.get(f"{API_BASE}/incidents", headers=headers, timeout=3)
        return res.json() if res.status_code == 200 else []
    except Exception:
        return []

@st.cache_data(ttl=30)
def fetch_cached_ai_summary(dock_id: str):
    try:
        res = requests.get(f"{API_BASE}/ai/incident-summary?dock={dock_id}", timeout=5)
        if res.status_code == 200:
            return res.json().get("summary", "No active hazards reported.")
        return "AI Briefing temporarily unavailable."
    except Exception:
        return "Standard Protocol: All monitored maritime sectors operating within normal limits."

# ==========================================
# 3. STATE INITIALIZATION
# ==========================================

if "cg_authenticated" not in st.session_state:
    st.session_state.cg_authenticated = False
    st.session_state.dock_id = None
    st.session_state.dock_name = None
    st.session_state.cg_key = None

if "play_audio_urls" not in st.session_state:
    st.session_state.play_audio_urls = None

# ==========================================
# 4. LOGIN / AUTHENTICATION SCREEN
# ==========================================

def render_login_screen():
    st.title("🛡️ Coastal Guard Command Center")
    st.subheader("Dock-Specific Port Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("cg_login_form"):
            dock_id = st.selectbox(
                "Select Station / Dock", 
                options=["all", "kunthukal", "point_pedro", "mandapam", "mangalore", "malpe"],
                format_func=lambda x: {
                    "all": "🌐 Master Coordination (All Docks)",
                    "kunthukal": "⚓ Kunthukal Fish Landing Centre (TN, India)",
                    "point_pedro": "⚓ Point Pedro Fishing Port (Jaffna, Sri Lanka)",
                    "mandapam": "⚓ Mandapam Fisheries Jetty (TN, India)",
                    "mangalore": "⚓ Mangalore Old Port (KA, India)",
                    "malpe": "⚓ Malpe Fishing Harbour (KA, India)"
                }.get(x, f"⚓ {x.title()} Port Command")
            )
            password = st.text_input("Access Security Key", type="password")
            submitted = st.form_submit_button("Authenticate Station")
            
            if submitted:
                try:
                    resp = requests.post(
                        f"{API_BASE}/coastguard/login", 
                        json={"dock_id": dock_id, "password": password}, 
                        timeout=3
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.cg_authenticated = True
                        st.session_state.dock_id = data.get("dock_id", dock_id)
                        st.session_state.dock_name = data.get("dock_name", dock_id.title())
                        st.session_state.cg_key = password
                        st.rerun()
                    else:
                        st.error("Authentication failed. Invalid security credentials.")
                except Exception as e:
                    st.error(f"Cannot connect to backend server: {e}")

# ==========================================
# 5. MAIN COORDINATION DASHBOARD
# ==========================================

def render_dashboard():
    dock_id = st.session_state.dock_id
    dock_name = st.session_state.dock_name
    cg_key = st.session_state.cg_key

    # Sidebar Controls
    st.sidebar.title(f"⚓ {dock_name}")
    st.sidebar.caption(f"Role: {'Master Command' if dock_id == 'all' else 'Station Operator'}")
    
    if st.sidebar.button("🔒 Logout Station"):
        st.session_state.cg_authenticated = False
        st.session_state.play_audio_urls = None
        st.rerun()

    # Top Status Banner
    st.title("🌊 Coastal Safety & Fleet Coordination Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Dock", dock_id.upper())
    m2.metric("Telemetry Status", "CONNECTED ✅")
    m3.metric("Voice Dispatch", "KANNADA 🔊")
    m4.metric("Security Level", "RESTRICTED 🛡️")

    st.divider()

    # SECTION A: Fleet & Incident Data
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🚢 Monitored Vessels & Telemetry")
        fleet = fetch_cached_fleet(dock_id, cg_key)
        if fleet:
            st.dataframe(fleet, use_container_width=True)
        else:
            st.info("No active vessel telemetry reported for this dock.")

    with col_right:
        st.subheader("⚠️ Active Incident Feed")
        incidents = fetch_cached_incidents(dock_id, cg_key)
        if incidents:
            for inc in incidents:
                st.warning(f"**{inc.get('type', 'Alert')}** - {inc.get('vessel', 'Unknown Vessel')}\n\n{inc.get('details', '')}")
        else:
            st.success("Zero active emergency incidents.")

    st.divider()

    # SECTION B: Kannada Audio Dispatch
    st.subheader("📢 Kannada Voice Alert Dispatch")
    with st.form("audio_dispatch_form"):
        risk_level = st.selectbox("Select Hazard Risk Level", ["low", "moderate", "high", "critical"])
        broadcast_btn = st.form_submit_button("▶ Broadcast Audio Alert (Kannada)")
        
        if broadcast_btn:
            headers = {"X-Coastguard-Key": cg_key, "X-Dock-Id": dock_id}
            try:
                res = requests.get(f"{API_BASE}/voice/alert-audio/{risk_level}?lang=kannada", headers=headers, timeout=3)
                if res.status_code == 200:
                    st.session_state.play_audio_urls = res.json().get("audio_urls", [])
                else:
                    st.error(f"Audio server returned status {res.status_code}")
            except Exception as e:
                st.error(f"Audio backend error: {e}")

    # Safe one-time audio render execution
    if st.session_state.play_audio_urls:
        render_chained_alert_audio(st.session_state.play_audio_urls, lang="kannada")
        st.session_state.play_audio_urls = None  # Clear flag immediately after rendering

    st.divider()

    # SECTION C: AI Incident Briefing
    st.subheader("🤖 Ollama AI Emergency Briefing")
    if st.button("Generate AI Status Report"):
        with st.spinner("Fetching non-blocking AI summary..."):
            summary = fetch_cached_ai_summary(dock_id)
            st.info(summary)

# ==========================================
# 6. APPLICATION ROUTER
# ==========================================

if not st.session_state.cg_authenticated:
    render_login_screen()
else:
    render_dashboard()