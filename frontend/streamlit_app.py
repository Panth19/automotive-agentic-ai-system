"""
Streamlit Frontend - Voice-first multimodal interface for BMW Automotive AI Assistant
"""
import copy
import io
import os
import sys
from datetime import datetime

import requests
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_URL = "http://localhost:8000"

VOICE_EXAMPLES = [
    "Set temperature to 22 degrees",
    "Play jazz music",
    "Stop music",
    "Navigate to BMW Museum",
    "What's my fuel level?",
    "Lock the doors",
    "Stop the car",
]

st.set_page_config(page_title="BMW AI Assistant", layout="wide", page_icon="🚗")
st.title("🚗 BMW Automotive AI Assistant")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "logs" not in st.session_state:
    st.session_state.logs = []
if "vision_context" not in st.session_state:
    st.session_state.vision_context = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "last_voice_transcript" not in st.session_state:
    st.session_state.last_voice_transcript = None
if "continuous_listen" not in st.session_state:
    st.session_state.continuous_listen = False
if "voice_responses_enabled" not in st.session_state:
    st.session_state.voice_responses_enabled = True
if "vehicle_state" not in st.session_state:
    st.session_state.vehicle_state = {
        "speed": 60,
        "fuel_level": 75,
        "engine_temp": 90,
        "cabin_temp": 22,
        "ac_on": True,
        "fan_speed": 3,
        "seat_heating": {"driver": 1, "passenger": 0, "rear": 0},
        "location": "Munich, Germany",
        "destination": "BMW HQ, Munich",
        "eta": "15 minutes",
        "odometer": 45230,
        "battery_status": "Good",
        "doors_locked": True,
        "warnings": [],
        "media": {"current_track": "Blinding Lights - The Weeknd", "volume": 50, "is_playing": True},
    }

try:
    import pyttsx3
    tts_engine = pyttsx3.init()
    tts_available = True
except Exception:
    tts_available = False

try:
    from streamlit_mic_recorder import mic_recorder
    mic_recorder_available = True
except ImportError:
    mic_recorder_available = False


def is_api_online() -> bool:
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def api_connection_error_message() -> str:
    return (
        "**API backend is not running.** Voice and chat need the FastAPI server on port 8000.\n\n"
        "Open a **second terminal** in the project folder and run:\n"
        "```\npython main.py\n```\n"
        "Or start both together with:\n"
        "```\npython run_all.py\n```"
    )


def sync_vehicle_state():
    try:
        response = requests.get(f"{API_URL}/status", timeout=3)
        if response.status_code == 200:
            st.session_state.vehicle_state = copy.deepcopy(response.json())
    except Exception:
        pass


def get_speech_status() -> dict:
    try:
        response = requests.get(f"{API_URL}/speech/status", timeout=3)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {"available": False, "engine": "unavailable"}


def speak_response(text: str):
    if tts_available and st.session_state.voice_responses_enabled:
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception:
            pass


def apply_agent_response(data: dict, user_label: str):
    st.session_state.messages.append({"role": "user", "content": user_label})
    st.session_state.messages.append({
        "role": "assistant",
        "content": data["response"],
        "tools": data.get("tools_called", []),
    })
    st.session_state.vehicle_state = copy.deepcopy(data["vehicle_state"])
    st.session_state.logs.append(f"🎯 Intent: {data['intent']}")
    if data.get("tools_called"):
        st.session_state.logs.append(f"🔧 Tools: {', '.join(data['tools_called'])}")
    if data.get("safety_blocked"):
        st.session_state.logs.append(f"⚠️ Safety blocked: {data.get('safety_reason', 'Unknown reason')}")
    else:
        st.session_state.logs.append("✅ Safety check passed")
    speak_response(data["response"])


def process_live_transcript(transcript: str, source: str = "live-mic") -> bool:
    """Process a real-time voice transcript through the agent (no audio file upload)."""
    if not transcript.strip():
        return False

    payload = {
        "message": transcript.strip(),
        "session_id": st.session_state.session_id,
        "vision_context": st.session_state.vision_context,
    }

    try:
        with st.spinner("Processing voice command..."):
            response = requests.post(f"{API_URL}/chat", json=payload, timeout=60)
        if response.status_code == 200:
            st.session_state.logs.append(f"🎙️ Live voice ({source}): '{transcript.strip()}'")
            apply_agent_response(response.json(), f"🎤 {transcript.strip()}")
            return True
        st.error(f"Voice command failed: {response.text}")
    except requests.ConnectionError:
        st.error(api_connection_error_message())
    except Exception as exc:
        st.error(f"Voice error: {exc}")
    return False


def process_live_mic_audio(audio_bytes: bytes) -> bool:
    """Fallback: stream live mic audio to server STT when browser speech API is unavailable."""
    if not audio_bytes:
        return False

    files = {"audio": ("live-mic.wav", io.BytesIO(audio_bytes), "audio/wav")}
    form = {
        "session_id": st.session_state.session_id,
        "vision_context": st.session_state.vision_context or "",
    }

    try:
        with st.spinner("Processing live microphone audio..."):
            response = requests.post(f"{API_URL}/voice", files=files, data=form, timeout=90)
        if response.status_code == 200:
            data = response.json()
            transcript = data.get("transcript", "")
            engine = data.get("stt_engine", "unknown")
            st.session_state.logs.append(f"🎙️ Live mic STT ({engine}): '{transcript}'")
            apply_agent_response(data, f"🎤 {transcript}")
            return True
        st.error(f"Voice command failed: {response.text}")
    except requests.ConnectionError:
        st.error(api_connection_error_message())
    except Exception as exc:
        st.error(f"Voice error: {exc}")
    return False


def stop_car_via_api() -> bool:
    for path in ("/vehicle/stop", "/stop"):
        try:
            response = requests.post(f"{API_URL}{path}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                st.session_state.vehicle_state = copy.deepcopy(data["vehicle_state"])
                st.session_state.logs.append("🛑 Vehicle stopped — speed set to 0 km/h")
                return True
        except Exception:
            continue

    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "message": "stop the car",
                "session_id": st.session_state.session_id,
                "vision_context": st.session_state.vision_context,
            },
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.vehicle_state = copy.deepcopy(data["vehicle_state"])
            st.session_state.logs.append("🛑 Vehicle stopped via chat command")
            return True
    except Exception:
        pass
    return False


def send_chat_message(message: str):
    if not message.strip():
        return

    st.session_state.messages.append({"role": "user", "content": message})
    st.session_state.logs.append(f"📝 Processing: '{message}'")

    payload = {
        "message": message,
        "session_id": st.session_state.session_id,
        "vision_context": st.session_state.vision_context,
    }

    try:
        with st.spinner("Thinking..."):
            response = requests.post(f"{API_URL}/chat", json=payload, timeout=60)
        if response.status_code == 200:
            apply_agent_response(response.json(), message)
        else:
            st.error(f"API error: {response.status_code} - {response.text}")
    except requests.ConnectionError:
        st.error(api_connection_error_message())
    except Exception as exc:
        st.error(f"Error: {exc}")


api_online = is_api_online()
if api_online:
    sync_vehicle_state()
speech_status = get_speech_status() if api_online else {"available": False, "engine": "unavailable"}

if not api_online:
    st.error("API backend offline — start it with `python main.py` in a separate terminal (port 8000).")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.header("📊 Vehicle Dashboard")

    speed = st.session_state.vehicle_state["speed"]
    st.metric("Speed", f"{speed} km/h", delta=None if speed == 0 else "moving")
    if speed > 0:
        if st.button("🛑 Stop car", type="primary", use_container_width=True):
            if stop_car_via_api():
                st.rerun()
            else:
                st.error(
                    "Could not stop vehicle. Restart the API server: "
                    "press Ctrl+C in the API terminal, then run `python main.py`."
                )
    else:
        st.success("Vehicle stopped")

    st.progress(st.session_state.vehicle_state["fuel_level"] / 100)
    st.caption(f"Fuel Level: {st.session_state.vehicle_state['fuel_level']}%")
    st.metric("Cabin Temp", f"{st.session_state.vehicle_state['cabin_temp']}°C")

    ac_status = "ON ✅" if st.session_state.vehicle_state["ac_on"] else "OFF ❌"
    st.markdown(f"**AC Status:** {ac_status}")
    st.markdown(f"**Fan Speed:** {st.session_state.vehicle_state['fan_speed']}/5")

    seat_heat = st.session_state.vehicle_state.get("seat_heating", {})
    st.markdown(
        f"**Seat Heating:** Driver: {seat_heat.get('driver', 0)}/3, "
        f"Passenger: {seat_heat.get('passenger', 0)}/3"
    )

    doors_locked = st.session_state.vehicle_state.get("doors_locked", True)
    st.markdown(f"**Doors:** {'🔒 Locked' if doors_locked else '🔓 Unlocked'}")
    st.markdown(f"**Location:** {st.session_state.vehicle_state['location']}")
    st.markdown(f"**Destination:** {st.session_state.vehicle_state['destination']}")
    st.markdown(f"**ETA:** {st.session_state.vehicle_state['eta']}")

    warnings = st.session_state.vehicle_state.get("warnings", [])
    if warnings:
        st.warning(f"⚠️ Warnings: {', '.join(warnings)}")

    st.markdown("---")
    st.markdown("### 🎵 Media")
    media = st.session_state.vehicle_state.get("media", {})
    play_status = "▶️ Playing" if media.get("is_playing", False) else "⏸️ Paused"
    st.markdown(f"**Status:** {play_status}")
    st.markdown(f"**Now Playing:** {media.get('current_track', 'N/A')}")
    st.markdown(f"**Volume:** {media.get('volume', 0)}/100")

    st.markdown("---")
    st.markdown("### 📷 Vision / Camera")
    warning_sim = st.selectbox("Simulate dashboard warning", ["none", "red", "yellow"])
    if st.button("Generate dashboard image"):
        try:
            params = {} if warning_sim == "none" else {"warning": warning_sim}
            img_response = requests.get(f"{API_URL}/dashboard-image", params=params, timeout=10)
            if img_response.status_code == 200:
                st.image(img_response.content, caption="Simulated dashboard camera")
                st.session_state.logs.append("📷 Generated simulated dashboard image")
        except Exception as exc:
            st.error(f"Dashboard image error: {exc}")

    uploaded_image = st.file_uploader("Upload dashboard/camera image", type=["jpg", "jpeg", "png"])
    if uploaded_image and st.button("Analyze image"):
        try:
            files = {"image": (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)}
            vision_response = requests.post(f"{API_URL}/vision", files=files, timeout=30)
            if vision_response.status_code == 200:
                vision_data = vision_response.json()
                st.session_state.vision_context = vision_data.get("analysis_text", "")
                for item in vision_data.get("analysis", []):
                    st.info(item)
                st.session_state.logs.append(f"👁️ Vision: {st.session_state.vision_context}")
                sync_vehicle_state()
        except Exception as exc:
            st.error(f"Vision analysis error: {exc}")

    if st.session_state.vision_context:
        st.caption(f"Active vision context: {st.session_state.vision_context}")

with col2:
    st.header("🎤 Voice Commands")

    st.caption("Real-time microphone — speak live, no file upload needed. Best in Chrome or Edge.")

    st.session_state.voice_responses_enabled = st.toggle(
        "Speak assistant responses aloud",
        value=st.session_state.voice_responses_enabled,
    )
    st.session_state.continuous_listen = st.toggle(
        "Continuous listening (speak longer commands)",
        value=st.session_state.continuous_listen,
    )

    voice_processed = False

    if not api_online:
        st.info("Start `python main.py` first, then use voice commands here.")
    else:
        st.markdown("### 🎙️ Microphone Input")
        st.caption("Use live microphone recording or upload an audio file to send speech to the chat agent.")

        if mic_recorder_available:
            st.markdown("#### Record audio from your browser")
            if speech_status.get("available"):
                engine_label = speech_status.get("engine", "unknown").replace("-", " ").title()
                st.info(f"Server speech engine: {engine_label}")
            else:
                st.warning("Server speech fallback needs `GROQ_API_KEY` in `.env`.")

            audio = mic_recorder(
                start_prompt="🎤 Hold & speak",
                stop_prompt="⏹ Release",
                just_once=True,
                use_container_width=True,
                key="bmw_live_mic_fallback",
            )
            if audio and audio.get("bytes"):
                audio_hash = hash(audio["bytes"])
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    voice_processed = process_live_mic_audio(audio["bytes"])
        else:
            st.warning("Microphone recording component is unavailable. Use the audio file upload below.")

        st.markdown("---")
        st.markdown("#### Upload audio file")
        uploaded_audio = st.file_uploader(
            "Upload a recorded audio file", type=["wav", "mp3", "m4a", "ogg"], key="audio_upload"
        )
        if uploaded_audio:
            try:
                audio_bytes = uploaded_audio.getvalue()
                audio_hash = hash(audio_bytes)
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    voice_processed = process_live_mic_audio(audio_bytes)
            except Exception as exc:
                st.error(f"Audio upload error: {exc}")

                st.markdown("---")
                st.markdown("#### Browser recorder (no Python component required)")
                session_id_js = str(st.session_state.session_id).replace("'", "\\'")
                vision_context_js = str(st.session_state.vision_context or '').replace("'", "\\'")
                api_url_js = API_URL

                recorder_html = """
                <div>
                    <button id='recBtn'>Start Recording</button>
                    <button id='stopBtn' disabled>Stop</button>
                    <div id='status'></div>
                    <pre id='result' style='white-space:pre-wrap; max-height:200px; overflow:auto;'></pre>
                </div>
                <script>
                const recBtn = document.getElementById('recBtn');
                const stopBtn = document.getElementById('stopBtn');
                const status = document.getElementById('status');
                const result = document.getElementById('result');
                let mediaRecorder; let chunks = [];

                recBtn.onclick = async () => {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();
                        status.innerText = 'Recording...';
                        recBtn.disabled = true; stopBtn.disabled = false; chunks = [];
                        mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
                    } catch (err) {
                        status.innerText = 'Microphone access denied or unavailable.';
                    }
                };

                stopBtn.onclick = async () => {
                    if (!mediaRecorder) return;
                    mediaRecorder.stop();
                    status.innerText = 'Processing...';
                    recBtn.disabled = false; stopBtn.disabled = true;
                    mediaRecorder.onstop = async () => {
                        const blob = new Blob(chunks, { type: 'audio/webm' });
                        const form = new FormData();
                        form.append('audio', blob, 'recorded.webm');
                        form.append('session_id', '%s');
                        form.append('vision_context', '%s');
                        try {
                            const resp = await fetch('%s/voice', { method: 'POST', body: form });
                            const data = await resp.json();
                            result.innerText = JSON.stringify(data, null, 2);
                        } catch (e) {
                            result.innerText = 'Upload failed: ' + e;
                        }
                        status.innerText = 'Ready';
                    };
                };
                </script>
                """ % (session_id_js, vision_context_js, api_url_js)
                try:
                        import streamlit.components.v1 as components
                        components.html(recorder_html, height=320)
                except Exception:
                        st.info('Embedded browser recorder unavailable in this environment.')
    if voice_processed:
        st.rerun()

    with st.expander("Example voice commands"):
        for example in VOICE_EXAMPLES:
            st.markdown(f"- *\"{example}\"*")

    st.markdown("---")
    st.header("💬 Conversation")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**BMW AI:** {msg['content']}")
            if msg.get("tools"):
                st.caption(f"Tools used: {', '.join(msg['tools'])}")

    st.markdown("---")
    st.caption("Or type a message below.")

    with st.form(key="message_form", clear_on_submit=True):
        user_input = st.text_input("Type your message...")
        submitted = st.form_submit_button("Send")

    if submitted and user_input:
        send_chat_message(user_input)
        st.rerun()

with col3:
    st.header("📋 System Logs")
    st.caption(f"Session: {st.session_state.session_id}")

    for log in st.session_state.logs[-25:]:
        if "⚠️" in log or "blocked" in log.lower():
            st.markdown(f":red[{log}]")
        elif "✅" in log:
            st.markdown(f":green[{log}]")
        elif "🎙️" in log:
            st.markdown(f":blue[{log}]")
        else:
            st.markdown(log)

    api_status = "🟢 Online" if is_api_online() else "🔴 Offline (run `python main.py`)"
    st.markdown(f"**API:** {api_status}")

    if st.button("Refresh vehicle state"):
        if is_api_online():
            sync_vehicle_state()
            st.session_state.logs.append("🔄 Vehicle state synced from API")
        else:
            st.session_state.logs.append("❌ API offline — start `python main.py` on port 8000")
        st.rerun()

    if st.button("Clear vision context"):
        st.session_state.vision_context = None
        st.session_state.logs.append("👁️ Vision context cleared")
        st.rerun()
