"""
Streamlit Frontend - Visual Interface for BMW Automotive AI Assistant
"""
import streamlit as st
import requests
from datetime import datetime

# Initialize session state
if 'session_id' not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'vehicle_state' not in st.session_state:
    st.session_state.vehicle_state = {
        "speed": 60, "fuel_level": 75, "engine_temp": 90, "cabin_temp": 22,
        "ac_on": True, "fan_speed": 3, "seat_heating": {"driver": 1, "passenger": 0, "rear": 0},
        "location": "Munich, Germany", "destination": "BMW HQ, Munich", "eta": "15 minutes",
        "odometer": 45230, "battery_status": "Good", "doors_locked": True, "warnings": [],
        "media": {"current_track": "Blinding Lights - The Weeknd", "volume": 50, "is_playing": True}
    }

try:
    import pyttsx3
    engine = pyttsx3.init()
    tts_available = True
except Exception:
    tts_available = False

API_URL = "http://localhost:8000"
st.set_page_config(page_title="BMW AI Assistant", layout="wide")
st.title("🚗 BMW Automotive AI Assistant")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.header("📊 Vehicle Dashboard")
    st.metric("Speed", f"{st.session_state.vehicle_state['speed']} km/h")
    st.progress(st.session_state.vehicle_state['fuel_level'] / 100)
    st.metric("Cabin Temp", f"{st.session_state.vehicle_state['cabin_temp']}°C")
    st.markdown(f"**AC Status:** {'ON ✅' if st.session_state.vehicle_state['ac_on'] else 'OFF ❌'}")
    st.markdown(f"**Fan Speed:** {st.session_state.vehicle_state['fan_speed']}/5")
    st.markdown(f"**Location:** {st.session_state.vehicle_state['location']}")
    st.markdown(f"**Destination:** {st.session_state.vehicle_state['destination']}")
    st.markdown("### 🎵 Media")
    st.markdown(f"**Now Playing:** {st.session_state.vehicle_state['media']['current_track']}")

with col2:
    st.header("💬 Conversation")
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**BMW AI:** {msg['content']}")
            if msg.get("tools"):
                st.caption(f"Tools used: {', '.join(msg['tools'])}")
    
    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_input("Type your message...", key="user_input_widget")
        submitted = st.form_submit_button("Send")
    
    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.logs.append(f"📝 Processing: '{user_input}'")
        
        try:
            with st.spinner("Thinking..."):
                response = requests.post(f"{API_URL}/chat",
                    json={"message": user_input, "session_id": st.session_state.session_id})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.messages.append({"role": "assistant", "content": data["response"], "tools": data.get("tools_called", [])})
                    st.session_state.vehicle_state = data["vehicle_state"]
                    st.session_state.logs.append(f"🎯 Intent: {data['intent']}")
                    if data.get("tools_called"):
                        st.session_state.logs.append(f"🔧 Tools: {', '.join(data['tools_called'])}")
                    if data.get("safety_blocked"):
                        st.session_state.logs.append(f"⚠️ Safety blocked: {data['safety_reason']}")
                    else:
                        st.session_state.logs.append("✅ Safety check passed")
                    if tts_available:
                        try:
                            engine.say(data["response"])
                            engine.runAndWait()
                        except Exception:
                            pass
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col3:
    st.header("📋 System Logs")
    for log in st.session_state.logs[-20:]:
        if "⚠️" in log or "blocked" in log.lower():
            st.markdown(f":red[{log}]")
        elif "✅" in log:
            st.markdown(f":green[{log}]")
        else:
            st.markdown(log)
