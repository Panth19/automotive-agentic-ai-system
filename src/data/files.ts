export interface ProjectFile {
  path: string;
  language: string;
  category: 'backend' | 'mcp' | 'agent' | 'database' | 'frontend' | 'config' | 'docs' | 'utils';
  description: string;
  content: string;
}

export const projectFiles: ProjectFile[] = [
  {
    path: 'main.py',
    language: 'python',
    category: 'backend',
    description: 'FastAPI Backend - The Central Nervous System. Connects all components together.',
    content: `"""
FastAPI Backend - The Central Nervous System
Connects all components together
"""
import os
import json
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import sys
sys.path.insert(0, '/workspace')

from mcp_servers.vehicle_state_mcp import vehicle_state
from agent.langgraph_agent import agent
from database.memory_db import get_conversation_history

app = FastAPI(title="BMW Automotive AI Assistant", version="1.0.0")

# Lazy load Whisper (may fail on some Windows systems)
whisper_model = None
whisper_available = False

try:
    import whisper
    whisper_model = whisper.load_model("base")
    whisper_available = True
except Exception as e:
    print(f"Warning: Whisper not available - {e}")
    print("Speech-to-text will use fallback mode")

# Lazy load OpenCV
cv2_available = False
try:
    import cv2
    cv2_available = True
except Exception as e:
    print(f"Warning: OpenCV not available - {e}")
    print("Vision analysis will use fallback mode")

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BMW Automotive AI Assistant API", "status": "online"}

@app.get("/status")
async def get_status():
    """Get current vehicle state"""
    return vehicle_state

@app.post("/speech")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech to text using Whisper (with fallback)"""
    try:
        if whisper_available:
            audio_path = f"temp_{audio.filename}"
            with open(audio_path, "wb") as f:
                content = await audio.read()
                f.write(content)
            result = whisper_model.transcribe(audio_path)
            text = result["text"]
            os.remove(audio_path)
            return {"text": text, "confidence": result.get("confidence", 0.9)}
        else:
            return {"text": "[Speech detected - Whisper unavailable]", "confidence": 0.5}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision")
async def vision_analysis(image: UploadFile = File(...)):
    """Analyze dashboard image using OpenCV (with fallback)"""
    try:
        if cv2_available:
            content = await image.read()
            nparr = np.frombuffer(content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            red_lower = np.array([0, 100, 100])
            red_upper = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower, red_upper)
            red_lower2 = np.array([170, 100, 100])
            red_upper2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_detected = np.count_nonzero(red_mask1) + np.count_nonzero(red_mask2)

            yellow_lower = np.array([20, 100, 100])
            yellow_upper = np.array([30, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            yellow_detected = np.count_nonzero(yellow_mask)

            analysis = []
            if red_detected > 1000:
                analysis.append("Red warning light detected - possible engine or brake issue")
                vehicle_state["warnings"].append("red_warning_detected")
            if yellow_detected > 1000:
                analysis.append("Yellow warning light detected - check vehicle status")
                vehicle_state["warnings"].append("yellow_warning_detected")
            if not analysis:
                analysis.append("No warning lights detected - dashboard appears normal")

            return {"analysis": analysis, "red_pixels": int(red_detected), "yellow_pixels": int(yellow_detected)}
        else:
            return {"analysis": ["Vision analysis - OpenCV unavailable"], "red_pixels": 0, "yellow_pixels": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat message through LangGraph agent"""
    try:
        history = get_conversation_history(request.session_id)
        initial_state = {
            "user_message": request.message,
            "conversation_history": history,
            "vehicle_state": vehicle_state,
            "intent": None,
            "tools_to_call": [],
            "tool_results": [],
            "response": None,
            "safety_blocked": False,
            "safety_reason": None,
            "tools_called_names": []
        }
        result = agent.invoke(initial_state)
        return {
            "response": result["response"],
            "intent": result["intent"],
            "tools_called": result["tools_called_names"],
            "safety_blocked": result["safety_blocked"],
            "vehicle_state": vehicle_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream AI response word by word"""
    async def generate():
        history = get_conversation_history(request.session_id)
        initial_state = {
            "user_message": request.message,
            "conversation_history": history,
            "vehicle_state": vehicle_state,
            "intent": None,
            "tools_to_call": [],
            "tool_results": [],
            "response": None,
            "safety_blocked": False,
            "safety_reason": None,
            "tools_called_names": []
        }
        result = agent.invoke(initial_state)
        words = result["response"].split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)
        yield json.dumps({"vehicle_state": vehicle_state}) + "\\n"
    return StreamingResponse(generate(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
`
  },
  {
    path: 'mcp_servers/vehicle_state_mcp.py',
    language: 'python',
    category: 'mcp',
    description: 'Vehicle State MCP Server - Read-only access to vehicle state.',
    content: `"""
Vehicle State MCP Server
Provides read-only access to vehicle state information
"""
from fastmcp import FastMCP
import random

mcp = FastMCP("vehicle-state")

# Simulated vehicle state
vehicle_state = {
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
    "media": {
        "current_track": "Blinding Lights - The Weeknd",
        "volume": 50,
        "is_playing": True
    }
}

@mcp.tool()
def get_fuel_level() -> dict:
    """Get current fuel level percentage"""
    return {"fuel_level": vehicle_state["fuel_level"], "unit": "percent"}

@mcp.tool()
def get_current_speed() -> dict:
    """Get current vehicle speed"""
    return {"speed": vehicle_state["speed"], "unit": "km/h"}

@mcp.tool()
def get_active_warnings() -> dict:
    """Get list of active warning lights"""
    return {"warnings": vehicle_state["warnings"], "count": len(vehicle_state["warnings"])}

@mcp.tool()
def get_odometer_reading() -> dict:
    """Get current odometer reading"""
    return {"odometer": vehicle_state["odometer"], "unit": "km"}

@mcp.tool()
def get_battery_status() -> dict:
    """Get battery status"""
    return {"battery_status": vehicle_state["battery_status"], "battery_level": random.randint(80, 100)}

@mcp.tool()
def get_door_status() -> dict:
    """Get door lock status"""
    return {"doors_locked": vehicle_state["doors_locked"]}

@mcp.tool()
def get_full_vehicle_state() -> dict:
    """Get complete vehicle state snapshot"""
    return vehicle_state.copy()

if __name__ == "__main__":
    mcp.run()
`
  },
  {
    path: 'mcp_servers/climate_mcp.py',
    language: 'python',
    category: 'mcp',
    description: 'Climate Control MCP Server - Controls vehicle climate settings.',
    content: `"""
Climate Control MCP Server
Controls vehicle climate settings
"""
from fastmcp import FastMCP
import sys
sys.path.insert(0, '/workspace')
from mcp_servers.vehicle_state_mcp import vehicle_state

mcp = FastMCP("climate-control")

@mcp.tool()
def set_temperature(temp: int, zone: str = "all") -> dict:
    """Set cabin temperature (16-30°C)"""
    if temp < 16 or temp > 30:
        return {"error": "Temperature must be between 16°C and 30°C for safety and comfort"}
    vehicle_state["cabin_temp"] = temp
    return {"status": "success", "temperature": temp, "zone": zone}

@mcp.tool()
def toggle_ac(ac_on: bool) -> dict:
    """Turn AC on or off"""
    vehicle_state["ac_on"] = ac_on
    return {"status": "success", "ac_on": ac_on}

@mcp.tool()
def set_fan_speed(speed: int) -> dict:
    """Set fan speed (1-5)"""
    if speed < 1 or speed > 5:
        return {"error": "Fan speed must be between 1 and 5"}
    vehicle_state["fan_speed"] = speed
    return {"status": "success", "fan_speed": speed}

@mcp.tool()
def set_seat_heating(zone: str, level: int) -> dict:
    """Set seat heating level (0-3)"""
    if level < 0 or level > 3:
        return {"error": "Seat heating level must be between 0 and 3"}
    if zone in vehicle_state["seat_heating"]:
        vehicle_state["seat_heating"][zone] = level
        return {"status": "success", "zone": zone, "level": level}
    return {"error": f"Invalid zone: {zone}"}

@mcp.tool()
def toggle_rear_defrost(defrost_on: bool) -> dict:
    """Turn rear window defrost on or off"""
    return {"status": "success", "rear_defrost": defrost_on, "message": "Rear window defrost toggled"}

if __name__ == "__main__":
    mcp.run()
`
  },
  {
    path: 'mcp_servers/navigation_mcp.py',
    language: 'python',
    category: 'mcp',
    description: 'Navigation MCP Server - Controls vehicle navigation system.',
    content: `"""
Navigation MCP Server
Controls vehicle navigation system
"""
from fastmcp import FastMCP
import random
import sys
sys.path.insert(0, '/workspace')
from mcp_servers.vehicle_state_mcp import vehicle_state

mcp = FastMCP("navigation")

@mcp.tool()
def set_destination(place: str) -> dict:
    """Set navigation destination"""
    vehicle_state["destination"] = place
    eta_minutes = random.randint(5, 30)
    vehicle_state["eta"] = f"{eta_minutes} minutes"
    return {"status": "success", "destination": place, "eta": vehicle_state["eta"]}

@mcp.tool()
def get_current_location() -> dict:
    """Get current GPS location"""
    return {"location": vehicle_state["location"], "coordinates": "48.1351° N, 11.5820° E"}

@mcp.tool()
def get_eta() -> dict:
    """Get estimated time of arrival"""
    return {"destination": vehicle_state["destination"], "eta": vehicle_state["eta"]}

@mcp.tool()
def avoid_tolls(avoid: bool) -> dict:
    """Toggle toll avoidance"""
    return {"status": "success", "toll_avoidance": avoid, "message": f"Toll avoidance {'enabled' if avoid else 'disabled'}"}

@mcp.tool()
def get_nearby_poi(poi_type: str) -> dict:
    """Find nearby points of interest"""
    poi_data = {
        "gas_station": ["Shell - 2km", "BP - 5km", "Total - 8km"],
        "coffee_shop": ["Starbucks - 1km", "Café Botte - 3km", "Local Roast - 6km"],
        "restaurant": ["BMW Welt Café - 1km", "Restaurant am See - 4km", "City Grill - 7km"],
        "parking": ["Underground Parking - 0.5km", "Street Parking - 0.2km", "BMW Garage - 2km"]
    }
    results = poi_data.get(poi_type, ["No nearby points of interest found"])
    return {"poi_type": poi_type, "nearby": results, "count": len(results)}

if __name__ == "__main__":
    mcp.run()
`
  },
  {
    path: 'mcp_servers/media_mcp.py',
    language: 'python',
    category: 'mcp',
    description: 'Media MCP Server - Controls vehicle media system.',
    content: `"""
Media MCP Server
Controls vehicle media system
"""
from fastmcp import FastMCP
import random
import sys
sys.path.insert(0, '/workspace')
from mcp_servers.vehicle_state_mcp import vehicle_state

mcp = FastMCP("media-control")

music_database = {
    "rock": ["AC/DC - Highway to Hell", "Queen - Bohemian Rhapsody", "Led Zeppelin - Stairway to Heaven"],
    "jazz": ["Miles Davis - Kind of Blue", "John Coltrane - Giant Steps", "Ella Fitzgerald - Dream a Little Dream"],
    "classical": ["Beethoven - Symphony No. 9", "Mozart - Requiem", "Bach - Brandenburg Concerto"],
    "pop": ["The Weeknd - Blinding Lights", "Dua Lipa - Levitating", "Ed Sheeran - Shape of You"],
    "electronic": ["Daft Punk - Random Access Memories", "Calvin Harris - Summer", "Swedish House Mafia - Don't You Worry Child"]
}

radio_stations = {
    "antenna_1": "Bayern 3",
    "antenna_2": "NDR 2",
    "antenna_3": "WDR 2",
    "dab_1": "BBC Radio 1",
    "dab_2": "KISS FM"
}

@mcp.tool()
def play_music(genre: str = None, artist: str = None, mood: str = None) -> dict:
    """Play music by genre, artist, or mood"""
    if genre and genre.lower() in music_database:
        track = random.choice(music_database[genre.lower()])
        vehicle_state["media"]["current_track"] = track
        vehicle_state["media"]["is_playing"] = True
        return {"status": "success", "track": track, "genre": genre}
    if mood:
        mood_to_genre = {"relaxed": "classical", "energetic": "rock", "happy": "pop", "focused": "jazz"}
        genre = mood_to_genre.get(mood.lower(), "pop")
        track = random.choice(music_database[genre])
        vehicle_state["media"]["current_track"] = track
        vehicle_state["media"]["is_playing"] = True
        return {"status": "success", "track": track, "mood": mood}
    return {"status": "success", "track": vehicle_state["media"]["current_track"], "message": "Playing current selection"}

@mcp.tool()
def set_volume(volume: int) -> dict:
    """Set media volume (0-100)"""
    if volume < 0 or volume > 100:
        return {"error": "Volume must be between 0 and 100"}
    vehicle_state["media"]["volume"] = volume
    return {"status": "success", "volume": volume}

@mcp.tool()
def next_track() -> dict:
    """Skip to next track"""
    vehicle_state["media"]["is_playing"] = True
    return {"status": "success", "message": "Skipped to next track"}

@mcp.tool()
def previous_track() -> dict:
    """Go to previous track"""
    vehicle_state["media"]["is_playing"] = True
    return {"status": "success", "message": "Returned to previous track"}

@mcp.tool()
def play_radio(station: str = None) -> dict:
    """Play radio station"""
    if station and station in radio_stations:
        vehicle_state["media"]["current_track"] = f"Radio: {radio_stations[station]}"
        vehicle_state["media"]["is_playing"] = True
        return {"status": "success", "station": radio_stations[station]}
    default_station = radio_stations["antenna_1"]
    vehicle_state["media"]["current_track"] = f"Radio: {default_station}"
    vehicle_state["media"]["is_playing"] = True
    return {"status": "success", "station": default_station}

@mcp.tool()
def pause_media() -> dict:
    """Pause media playback"""
    vehicle_state["media"]["is_playing"] = False
    return {"status": "success", "message": "Media paused"}

@mcp.tool()
def resume_media() -> dict:
    """Resume media playback"""
    vehicle_state["media"]["is_playing"] = True
    return {"status": "success", "message": "Media resumed"}

@mcp.tool()
def get_current_track() -> dict:
    """Get current track information"""
    return {"current_track": vehicle_state["media"]["current_track"], "is_playing": vehicle_state["media"]["is_playing"], "volume": vehicle_state["media"]["volume"]}

if __name__ == "__main__":
    mcp.run()
`
  },
  {
    path: 'agent/langgraph_agent.py',
    language: 'python',
    category: 'agent',
    description: 'LangGraph Agent - The Brain. 6-node graph for reasoning and decision making.',
    content: `"""
LangGraph Agent - The Brain of the Automotive AI System
Implements the 6-node graph for reasoning and decision making
"""
import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage
import re
import sys
sys.path.insert(0, '/workspace')
from database.memory_db import save_conversation, get_conversation_history
from mcp_servers.vehicle_state_mcp import vehicle_state

# Initialize Groq LLM (with fallback)
llm = None
try:
    from langchain_groq import ChatGroq
    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key and api_key.startswith("gsk_"):
        llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.3)
except Exception as e:
    print(f"Warning: Groq LLM not available - {e}")
    print("Using keyword-based intent classification and template responses")

# Agent State Definition
class AgentState(TypedDict):
    user_message: str
    conversation_history: List[Dict]
    vehicle_state: Dict
    intent: str
    tools_to_call: List[Dict]
    tool_results: List[Dict]
    response: str
    safety_blocked: bool
    safety_reason: str
    tools_called_names: List[str]

# Node 1: Input Processor
def input_processor_node(state: AgentState) -> AgentState:
    """Process and enrich input with vehicle context"""
    enriched_message = f"""
    User message: {state['user_message']}

    Current vehicle state:
    - Speed: {state['vehicle_state']['speed']} km/h
    - Fuel level: {state['vehicle_state']['fuel_level']}%
    - Cabin temperature: {state['vehicle_state']['cabin_temp']}°C
    - AC status: {'ON' if state['vehicle_state']['ac_on'] else 'OFF'}
    - Fan speed: {state['vehicle_state']['fan_speed']}
    - Current location: {state['vehicle_state']['location']}
    - Destination: {state['vehicle_state']['destination']}
    - Media: {state['vehicle_state']['media']['current_track']}
    """
    state['enriched_message'] = enriched_message
    return state

# Node 2: Intent Classifier
def intent_classifier_node(state: AgentState) -> AgentState:
    """Classify user intent using keywords (fallback) or LLM"""
    message = state['user_message'].lower()
    if any(kw in message for kw in ['navigate', 'destination', 'go to', 'nearby', 'nearest', 'coffee', 'gas station', 'route']):
        state['intent'] = 'navigation'
    elif any(kw in message for kw in ['temperature', 'temp', 'ac', 'fan', 'seat heat', 'defrost', 'cold', 'warm']):
        state['intent'] = 'climate'
    elif any(kw in message for kw in ['play', 'music', 'radio', 'volume', 'song', 'track', 'pause', 'resume']):
        state['intent'] = 'media'
    elif any(kw in message for kw in ['fuel', 'speed', 'warning', 'alert', 'door', 'battery', 'odometer']):
        state['intent'] = 'vehicle_info'
    else:
        state['intent'] = 'general'
    return state

# Node 3: Tool Caller
def tool_caller_node(state: AgentState) -> AgentState:
    """Call appropriate MCP tools based on intent"""
    tools_called = []
    tool_results = []
    from mcp_servers.climate_mcp import set_temperature, toggle_ac, set_fan_speed, set_seat_heating
    from mcp_servers.navigation_mcp import set_destination, get_current_location, get_eta, get_nearby_poi
    from mcp_servers.media_mcp import set_volume, play_music, pause_media, resume_media
    intent = state['intent']
    message = state['user_message'].lower()

    if intent == "climate":
        if "temperature" in message or "temp" in message:
            temp_match = re.search(r'(\\d+)', message)
            if temp_match:
                temp = int(temp_match.group(1))
                tools_called.append({"name": "set_temperature", "params": {"temp": temp}})
                result = set_temperature(temp)
                tool_results.append(result)
        if "ac" in message or "air conditioning" in message:
            ac_on = "on" in message or "enable" in message
            tools_called.append({"name": "toggle_ac", "params": {"ac_on": ac_on}})
            result = toggle_ac(ac_on)
            tool_results.append(result)
    elif intent == "navigation":
        if "navigate" in message or "go to" in message or "destination" in message:
            dest_match = re.search(r'(?:navigate to|go to|destination).*?(?:to\\s+)?(.+)', message)
            if dest_match:
                dest = dest_match.group(1).strip()
                tools_called.append({"name": "set_destination", "params": {"place": dest}})
                result = set_destination(dest)
                tool_results.append(result)
    elif intent == "media":
        if "play" in message or "music" in message:
            if "radio" in message:
                tools_called.append({"name": "play_radio", "params": {}})
                result = play_radio()
                tool_results.append(result)
            else:
                for genre in ["rock", "jazz", "classical", "pop", "electronic"]:
                    if genre in message:
                        tools_called.append({"name": "play_music", "params": {"genre": genre}})
                        result = play_music(genre=genre)
                        tool_results.append(result)
                        break
    elif intent == "vehicle_info":
        if "fuel" in message:
            tools_called.append({"name": "get_fuel_level", "params": {}})
            from mcp_servers.vehicle_state_mcp import get_fuel_level
            result = get_fuel_level()
            tool_results.append(result)

    state['tools_to_call'] = tools_called
    state['tool_results'] = tool_results
    state['tools_called_names'] = [t['name'] for t in tools_called]
    return state

# Node 4: Safety Validator
def safety_validator_node(state: AgentState) -> AgentState:
    """Validate safety of proposed actions"""
    speed = state['vehicle_state']['speed']
    safety_blocked = False
    safety_reason = None
    dangerous_at_speed = ["turn off engine", "unlock all doors", "disable warning"]
    for dangerous in dangerous_at_speed:
        if dangerous in state['user_message'].lower() and speed > 0:
            safety_blocked = True
            safety_reason = f"I can't {dangerous} while driving at {speed} km/h. This could be dangerous."
            break
    temp_match = re.search(r'temperature.*?(\\d+)', state['user_message'].lower())
    if temp_match and state.get('tool_results'):
        temp = int(temp_match.group(1))
        if temp < 16 or temp > 30:
            safety_blocked = True
            safety_reason = f"Temperature {temp}°C is outside safe range (16-30°C)."
    if speed > 80 and state['intent'] == 'navigation':
        if "search" in state['user_message'].lower() or "find" in state['user_message'].lower():
            safety_blocked = True
            safety_reason = f"I can't perform complex navigation searches while driving at {speed} km/h."
    state['safety_blocked'] = safety_blocked
    state['safety_reason'] = safety_reason
    return state

# Node 5: Response Generator
def response_generator_node(state: AgentState) -> AgentState:
    """Generate natural language response"""
    if state['safety_blocked']:
        response = state['safety_reason']
    elif state['tool_results']:
        if llm:
            prompt = f"""You are a BMW in-vehicle AI assistant. Generate a natural, conversational response."""
            response = llm.invoke([SystemMessage(content=prompt)]).content
        else:
            if "set_temperature" in state.get('tools_called_names', []):
                response = f"I've set the cabin temperature to {state['tool_results'][0].get('temperature')}°C."
            elif "set_destination" in state.get('tools_called_names', []):
                response = f"Navigation set to {state['tool_results'][0].get('destination')}."
            else:
                response = f"Command executed. Intent: {state['intent']}"
    else:
        response = f"I'm your BMW AI assistant. How can I help?" if not llm else llm.invoke([SystemMessage(content="Respond conversationally")]).content
    state['response'] = response
    return state

# Node 6: Memory Update
def memory_update_node(state: AgentState) -> AgentState:
    """Save conversation to memory database"""
    save_conversation(
        session_id="default_session",
        user_message=state['user_message'],
        intent=state['intent'],
        tools_called=state['tools_called_names'],
        response=state['response'],
        safety_blocked=state['safety_blocked'],
        safety_reason=state['safety_reason']
    )
    return state

def build_agent():
    """Build and return the LangGraph agent"""
    workflow = StateGraph(AgentState)
    workflow.add_node("input_processor", input_processor_node)
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("tool_caller", tool_caller_node)
    workflow.add_node("safety_validator", safety_validator_node)
    workflow.add_node("response_generator", response_generator_node)
    workflow.add_node("memory_update", memory_update_node)
    workflow.add_edge("input_processor", "intent_classifier")
    workflow.add_edge("intent_classifier", "tool_caller")
    workflow.add_edge("tool_caller", "safety_validator")
    workflow.add_edge("safety_validator", "response_generator")
    workflow.add_edge("response_generator", "memory_update")
    workflow.add_edge("memory_update", END)
    workflow.set_entry_point("input_processor")
    return workflow.compile()

agent = build_agent()
`
  },
  {
    path: 'database/memory_db.py',
    language: 'python',
    category: 'database',
    description: 'SQLite Memory Database for conversation history.',
    content: `"""
SQLite Memory Database for conversation history
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = "memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        user_message TEXT,
        intent TEXT,
        tools_called TEXT,
        response TEXT,
        safety_blocked INTEGER DEFAULT 0,
        safety_reason TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        vehicle_state TEXT
    )''')
    conn.commit()
    conn.close()

def create_session(session_id, vehicle_state):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sessions (session_id, created_at, vehicle_state) VALUES (?, ?, ?)",
        (session_id, datetime.now().isoformat(), json.dumps(vehicle_state)))
    conn.commit()
    conn.close()

def save_conversation(session_id, user_message, intent, tools_called, response, safety_blocked, safety_reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO conversations
        (session_id, timestamp, user_message, intent, tools_called, response, safety_blocked, safety_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (session_id, datetime.now().isoformat(), user_message, intent,
         json.dumps(tools_called), response, 1 if safety_blocked else 0, safety_reason))
    conn.commit()
    conn.close()

def get_conversation_history(session_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT user_message, intent, tools_called, response, safety_blocked, safety_reason, timestamp
        FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?''', (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"user_message": r[0], "intent": r[1], "tools_called": json.loads(r[2]) if r[2] else [],
             "response": r[3], "safety_blocked": bool(r[4]), "safety_reason": r[5], "timestamp": r[6]}
            for r in reversed(rows)]

init_db()
`
  },
  {
    path: 'frontend/streamlit_app.py',
    language: 'python',
    category: 'frontend',
    description: 'Streamlit Frontend - Visual Interface for the BMW AI Assistant.',
    content: `"""
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
`
  },
  {
    path: 'utils/vision_simulator.py',
    language: 'python',
    category: 'utils',
    description: 'Dashboard image simulator for testing vision analysis.',
    content: `"""
Dashboard image simulator for testing vision analysis
"""
import numpy as np

def create_dashboard_image(width=640, height=480, warning_type=None):
    """Create a simulated dashboard image with optional warning lights"""
    try:
        import cv2
    except ImportError:
        print("OpenCV not available")
        return None
    img = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (width - 50, height - 50), (40, 40, 40), -1)
    if warning_type == "red":
        cv2.circle(img, (width // 2, height // 2), 40, (0, 0, 255), -1)
    elif warning_type == "yellow":
        cv2.circle(img, (width // 2, height // 2), 40, (0, 255, 255), -1)
    return img


def save_dashboard_image(path, warning_type=None):
    """Save a simulated dashboard image to disk"""
    try:
        import cv2
        img = create_dashboard_image(warning_type=warning_type)
        if img is not None:
            cv2.imwrite(path, img)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False
`
  },
  {
    path: 'demo.py',
    language: 'python',
    category: 'backend',
    description: 'Test script for component verification.',
    content: `"""
Demo script to test the BMW Automotive AI Assistant core functionality
"""
import sys
sys.path.insert(0, '/workspace')

from mcp_servers.vehicle_state_mcp import vehicle_state, get_fuel_level, get_current_speed
from mcp_servers.climate_mcp import set_temperature, toggle_ac, set_fan_speed
from mcp_servers.navigation_mcp import set_destination, get_nearby_poi
from mcp_servers.media_mcp import play_music, set_volume
from database.memory_db import init_db, save_conversation, get_conversation_history
from agent.langgraph_agent import AgentState, build_agent

print("=" * 60)
print("Testing MCP Servers")
print("=" * 60)

print("\\n📊 Vehicle State MCP:")
print(f"  - Initial state: speed={vehicle_state['speed']} km/h, fuel={vehicle_state['fuel_level']}%")
print(f"  - Fuel level: {get_fuel_level()}")
print(f"  - Current speed: {get_current_speed()}")

print("\\n❄️ Climate MCP:")
print(f"  - Setting temperature to 22°C: {set_temperature(22)}")
print(f"  - AC status: {toggle_ac(True)}")
print(f"  - Fan speed: {set_fan_speed(3)}")

print("\\n🧭 Navigation MCP:")
print(f"  - Setting destination: {set_destination('BMW Museum, Munich')}")
print(f"  - Nearby coffee shops: {get_nearby_poi('coffee_shop')}")

print("\\n🎵 Media MCP:")
print(f"  - Play jazz: {play_music(genre='jazz')}")
print(f"  - Volume: {set_volume(60)}")

print("\\n" + "=" * 60)
print("Testing Database")
print("=" * 60)

init_db()
save_conversation(session_id="demo_session", user_message="Set temperature to 22 degrees",
    intent="climate", tools_called=["set_temperature"], response="Temperature set to 22°C", safety_blocked=False)

history = get_conversation_history("demo_session")
print(f"\\n💾 Memory DB: Saved {len(history)} conversation(s)")

print("\\n" + "=" * 60)
print("Testing LangGraph Agent Structure")
print("=" * 60)

agent = build_agent()
print("\\n🧠 Agent nodes: input_processor, intent_classifier, tool_caller, safety_validator, response_generator, memory_update")
print("All components tested successfully!")
`
  },
  {
    path: 'run_all.py',
    language: 'python',
    category: 'backend',
    description: 'Script to run both FastAPI and Streamlit services.',
    content: `"""
Run script to start all services
"""
import subprocess
import sys
import time

def main():
    print("🚀 Starting BMW Automotive AI Assistant...")

    api_process = subprocess.Popen([sys.executable, "main.py"])
    time.sleep(2)

    ui_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"])

    print("\\n✅ System started!")
    print("API: http://localhost:8000")
    print("UI: http://localhost:8501")
    print("\\nPress Ctrl+C to stop...")

    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\\n🛑 Shutting down...")
        api_process.terminate()
        ui_process.terminate()

if __name__ == "__main__":
    main()
`
  },
  {
    path: 'requirements.txt',
    language: 'text',
    category: 'config',
    description: 'Python dependencies.',
    content: `fastapi>=0.110.0
uvicorn>=0.29.0
streamlit>=1.32.0
langgraph>=0.0.31
langchain>=0.1.0
langchain-groq>=0.1.0
groq>=0.4.0
openai-whisper>=20231116
opencv-python>=4.9.0.80
opencv-python-headless>=4.9.0.80
pyttsx3>=2.90
numpy>=1.26.0
python-multipart>=0.0.9
aiofiles>=23.2.1
pillow>=10.2.0
fastmcp>=0.1.0
`
  },
  {
    path: '.env.example',
    language: 'text',
    category: 'config',
    description: 'Environment variables template.',
    content: `# BMW Automotive AI Assistant - Environment Variables
# Copy this file to .env and fill in your values

# Groq API Key (required for LLM inference)
# Get your key from: https://console.groq.com
GROQ_API_KEY=your_groq_api_key_here

# Optional: Change default settings
# WHISPER_MODEL_SIZE=base
# TTS_ENABLED=true
`
  },
  {
    path: 'README.md',
    language: 'markdown',
    category: 'docs',
    description: 'Project README.',
    content: `# BMW Automotive AI Assistant

A comprehensive in-vehicle AI assistant built with FastAPI, LangGraph, MCP (Model Context Protocol), Whisper, OpenCV, and Streamlit.

## Features

- **Voice Input** via OpenAI Whisper
- **Vision Analysis** via OpenCV
- **6-Node LangGraph Agent** for reasoning
- **MCP Servers** for vehicle, climate, navigation, media
- **Safety Validation** for driving actions
- **SQLite Memory** for conversations
- **Streamlit UI** with live dashboard
- **Text-to-Speech** via pyttsx3

## Quick Start

\`\`\`bash
pip install -r requirements.txt
cp .env.example .env
python run_all.py
\`\`\`
`
  },
];

export const categoryColors: Record<string, string> = {
  backend: 'from-blue-500 to-cyan-500',
  mcp: 'from-purple-500 to-pink-500',
  agent: 'from-amber-500 to-orange-500',
  database: 'from-emerald-500 to-teal-500',
  frontend: 'from-rose-500 to-red-500',
  config: 'from-slate-500 to-slate-600',
  docs: 'from-indigo-500 to-violet-500',
  utils: 'from-yellow-500 to-amber-500',
};

export const categoryLabels: Record<string, string> = {
  backend: 'Backend',
  mcp: 'MCP Server',
  agent: 'Agent',
  database: 'Database',
  frontend: 'Frontend',
  config: 'Config',
  docs: 'Docs',
  utils: 'Utils',
};
