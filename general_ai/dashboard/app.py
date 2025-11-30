"""
Mobile Command Center (Dashboard)
---------------------------------
PLATFORM: Streamlit (Host on Raspberry Pi, access via LAN/VPN).
THEME: Sci-Fi / Future Tech (Glassmorphism).

USAGE:
    streamlit run general_ai/dashboard/app.py --server.address 0.0.0.0
"""

import streamlit as st
import pandas as pd
import sys
import asyncio
from pathlib import Path
import time
import nest_asyncio

# Apply nest_asyncio to allow nested event loops (Fixes RuntimeError in Streamlit)
nest_asyncio.apply()

# Add Project Root to Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Import Backend Modules
from general_ai.scripts.gamification_engine import GamificationEngine
from beacon_ai.main_agent import BeaconAgent # Use the Manager Agent

# Initialize Engine
engine = GamificationEngine()

def init_agents():
    """Lazy loads the main BeaconAgent into session state."""
    if "beacon_agent" not in st.session_state:
        with st.spinner("Initializing BEACON AI Systems..."):
            agent = BeaconAgent()
            # Hack for sync loop in Streamlit
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(agent.initialize()) 
            st.session_state.beacon_agent = agent
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

def run_async(coro):
    """Helper to run async code within Streamlit using the current loop."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def main():
    st.set_page_config(page_title="BEACON OS", page_icon="📡", layout="wide", initial_sidebar_state="collapsed")
    
    # --- MODERN SCI-FI THEME INJECTION ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;800&family=Inter:wght@300;600&display=swap');

    /* GLOBAL THEME */
    .stApp {
        background-color: #050505;
        background-image: radial-gradient(circle at 50% 50%, #111111 0%, #000000 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE STREAMLIT CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* NEON TYPOGRAPHY */
    h1, h2, h3, h4 {
        font-family: 'JetBrains Mono', monospace !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #00ff41 !important;
        text-shadow: 0 0 15px rgba(0, 255, 65, 0.4);
    }
    
    p, div, label, span {
        color: #e0e0e0;
    }

    /* GLASS CARD COMPONENT */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        transition: all 0.3s ease;
    }
    
    /* AGENT CARD SPECIFIC */
    .agent-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .agent-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: #111;
        border: 2px solid #00ff41;
        box-shadow: 0 0 10px #00ff41;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #00ff41;
        font-family: 'JetBrains Mono';
    }
    .progress-bg {
        background: #222;
        border-radius: 10px;
        height: 8px;
        width: 100%;
        margin-top: 10px;
        overflow: hidden;
    }
    .progress-fill {
        background: #00ff41;
        height: 100%;
        border-radius: 10px;
        box-shadow: 0 0 10px #00ff41;
        transition: width 0.5s ease-in-out;
    }

    /* CUSTOM TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255,255,255,0.02);
        padding: 10px;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        flex: 1;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        color: #888;
        font-family: 'JetBrains Mono';
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 255, 65, 0.15) !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
    }

    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
    }
    [data-testid="stChatMessageAvatarUser"] {
        background-color: #00ff41;
        color: black;
    }
    
    /* INPUT & BUTTONS */
    .stTextInput input {
        background-color: rgba(0,0,0,0.6) !important;
        color: #00ff41 !important;
        border: 1px solid #333 !important;
        border-radius: 10px;
        font-family: 'JetBrains Mono';
    }
    .stButton button {
        background: #00ff41;
        color: #000;
        font-family: 'JetBrains Mono';
        font-weight: 800;
        border: none;
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton button:hover {
        box-shadow: 0 0 20px #00ff41;
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)

    # st.title("📡 BEACON OS") # Hidden for cleaner mobile look
    
    init_agents()

    # --- Navigation ---
    tab_squad, tab_comms, tab_supply = st.tabs(["🛡️ SQUAD", "💬 COMMS", "🛒 SUPPLY"])

    # ==========================
    # VIEW 1: SQUAD (LifeRPG)
    # ==========================
    with tab_squad:
        st.markdown("### ACTIVE AGENTS")
        
        users = ["Micheal", "Hunter", "Fiona"]
        # Initials for avatars
        initials = {"Micheal": "M", "Hunter": "H", "Fiona": "F"}
        
        cols = st.columns(len(users))
        
        for i, user in enumerate(users):
            stats = engine.get_user_stats(user)
            xp = stats.get("xp", 0)
            level = stats.get("level", 1)
            role = stats.get("role", "Agent")
            threshold = engine.calculate_level_threshold(level)
            
            # Safe math for progress bar width
            if threshold > 0:
                pct = min((xp / threshold) * 100, 100)
            else:
                pct = 0
            
            with cols[i]:
                # Custom HTML Card
                st.markdown(f"""
                <div class="glass-card">
                    <div class="agent-header">
                        <div class="agent-avatar">{initials[user]}</div>
                        <div style="text-align:right;">
                            <div style="font-size:1.8em; color:#00ff41; font-weight:800;">LVL {level}</div>
                            <div style="font-size:0.7em; color:#888; letter-spacing:1px;">{role.upper()}</div>
                        </div>
                    </div>
                    <div style="font-family:'JetBrains Mono'; font-size:1.1em; font-weight:bold;">{user.upper()}</div>
                    <div class="progress-bg">
                        <div class="progress-fill" style="width: {pct}%;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.7em; color:#666; margin-top:5px;">
                        <span>XP: {xp}</span>
                        <span>NEXT: {threshold}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### ⚡ QUICK COMMAND")
        with st.expander("GRANT XP (OVERRIDE)", expanded=False):
            t_user = st.selectbox("Operative", users)
            t_xp = st.number_input("Amount", 50, 500, 50)
            t_task = st.text_input("Reason")
            if st.button("TRANSMIT REWARD"):
                msg = engine.award_xp(t_user, t_xp, t_task)
                st.success(msg)
                time.sleep(1)
                st.rerun()

    # ==========================
    # VIEW 2: COMMS (Chat + Vision)
    # ==========================
    with tab_comms:
        st.markdown("### SECURE CHANNEL")
        
        # Mode Toggle in a glass pill
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            mode = st.radio("Encryption Level:", ["Auto-Detect", "Force Biblical", "Force General"], horizontal=True, label_visibility="collapsed")
        with col_m2:
            if st.button("CLR", help="Clear History"):
                st.session_state.chat_history = []
                st.rerun()

        # Status Indicator
        status_color = "#00ff41" if "General" in str(mode) or "Auto" in str(mode) else "#0070dd"
        st.markdown(f"<div style='font-size:0.8em; color:{status_color}; margin-bottom:10px; font-family:JetBrains Mono;'>● SYSTEM ONLINE // MODE: {mode.upper()}</div>", unsafe_allow_html=True)

        # Chat History Container
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Vision Input (Hidden in Expander for cleanliness)
        with st.expander("👁️ ACTIVATE VISION SENSOR"):
            img = st.camera_input("SCAN TARGET")
            if img:
                st.info("Visual Data Acquired. Processing...")
                # TODO: Connect to VisionProcessor

        # Chat Input
        if prompt := st.chat_input("TRANSMIT COMMAND..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("`DECRYPTING...`")
                
                try:
                    # Map Radio to Force Mode string
                    force_arg = None
                    if mode == "Force Biblical": force_arg = "BIBLICAL"
                    if mode == "Force General": force_arg = "GENERAL"

                    # Ensure using sync wrapper to prevent loop errors
                    response = st.session_state.beacon_agent.respond_to_query_sync(prompt, force_mode=force_arg)
                    placeholder.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    placeholder.error(f"TRANSMISSION ERROR: {e}")

    # ==========================
    # VIEW 3: SUPPLY (Inventory)
    # ==========================
    with tab_supply:
        st.markdown("### LOGISTICS & VAULT")
        
        sub_t1, sub_t2 = st.tabs(["📦 INVENTORY", "🗄️ THE VAULT"])
        
        with sub_t1:
            st.markdown("""
            <div class="glass-card">
                <h4 style="margin:0;">PANTRY MONITOR</h4>
                <p style="font-size:0.8em; color:#888;">STATUS: PENDING SCAN</p>
                <hr style="border-color:#333;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span>🥛 MILK</span>
                    <span style="color:#00ff41;">OK</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span>🥚 EGGS</span>
                    <span style="color:red;">LOW</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.button("INITIATE RESUPPLY (WALMART BOT)")

        with sub_t2:
            st.info("Local 5TB Vault Access Ready.")
            # Placeholder for file browser
            st.code("Y:\\BEACON_DATA\\Library\\...", language="text")

if __name__ == "__main__":
    main()
