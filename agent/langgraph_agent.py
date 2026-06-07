"""
LangGraph Agent - The Brain of the Automotive AI System
Implements a 7-node graph with pre-execution safety guardrails and MCP tool routing.
"""
import os
import re
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph

from agent.safety_guardrails import format_conversation_context, validate_planned_tools
from database.memory_db import create_session, save_conversation
from mcp_servers.mcp_client import call_tool
from mcp_servers.vehicle_state_mcp import vehicle_state

llm = None
try:
    from langchain_groq import ChatGroq

    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key and api_key.startswith("gsk_"):
        llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.3)
except Exception as exc:
    print(f"Warning: Groq LLM not available - {exc}")
    print("Using keyword-based intent classification and template responses")


class AgentState(TypedDict, total=False):
    user_message: str
    session_id: str
    vision_context: Optional[str]
    conversation_history: List[Dict]
    vehicle_state: Dict
    enriched_message: str
    intent: str
    tools_to_call: List[Dict]
    tool_results: List[Dict]
    response: str
    safety_blocked: bool
    safety_reason: Optional[str]
    tools_called_names: List[str]


def input_processor_node(state: AgentState) -> AgentState:
    """Enrich input with vehicle context, vision, and conversation history."""
    vision_note = ""
    if state.get("vision_context"):
        vision_note = f"\nDashboard/camera analysis: {state['vision_context']}"

    history_note = format_conversation_context(state.get("conversation_history", []))

    state["enriched_message"] = f"""
User message: {state['user_message']}
{vision_note}

Current vehicle state:
- Speed: {state['vehicle_state']['speed']} km/h
- Fuel level: {state['vehicle_state']['fuel_level']}%
- Cabin temperature: {state['vehicle_state']['cabin_temp']}°C
- AC status: {'ON' if state['vehicle_state']['ac_on'] else 'OFF'}
- Fan speed: {state['vehicle_state']['fan_speed']}
- Current location: {state['vehicle_state']['location']}
- Destination: {state['vehicle_state']['destination']}
- Media: {state['vehicle_state']['media']['current_track']}
- Active warnings: {state['vehicle_state'].get('warnings', [])}

Recent conversation:
{history_note}
"""
    return state


def intent_classifier_node(state: AgentState) -> AgentState:
    """Classify user intent using LLM with conversation context or keyword fallback."""
    message = state["user_message"].lower()
    context = state.get("enriched_message", state["user_message"])

    if llm:
        prompt = f"""
Classify the user's intent into exactly one category:
- navigation: directions, destinations, routes, POIs, ETA, location
- climate: temperature, AC, fan, seat heating, defrost
- media: music, radio, volume, tracks, pause, resume
- vehicle_info: fuel, speed, warnings, doors, battery, odometer
- general: greetings, general conversation, non-vehicle questions

Respond with only the category name.

Context:
{context}
"""
        try:
            response = llm.invoke([SystemMessage(content=prompt)])
            intent = response.content.strip().lower()
            if intent in ("navigation", "climate", "media", "vehicle_info", "general"):
                state["intent"] = intent
            else:
                state["intent"] = _keyword_intent_classifier(message)
        except Exception:
            state["intent"] = _keyword_intent_classifier(message)
    else:
        state["intent"] = _keyword_intent_classifier(message)

    return state


def _keyword_intent_classifier(message: str) -> str:
    if any(kw in message for kw in ("navigate", "destination", "go to", "nearby", "nearest", "coffee", "gas station", "route", "eta", "location")):
        return "navigation"
    if any(kw in message for kw in ("temperature", "temp", "ac", "fan", "seat heat", "defrost", "cold", "warm")):
        return "climate"
    if any(kw in message for kw in ("play", "music", "radio", "volume", "song", "track", "pause", "resume", "stop", "next", "previous")):
        return "media"
    if any(kw in message for kw in ("fuel", "speed", "warning", "alert", "door", "lock", "unlock", "battery", "odometer", "stop the car", "stop car", "park")):
        return "vehicle_info"
    return "general"


def tool_planner_node(state: AgentState) -> AgentState:
    """Plan MCP tool calls without executing them (safety runs next)."""
    planned: List[Dict[str, Any]] = []
    intent = state["intent"]
    message = state["user_message"].lower()

    if intent == "climate":
        if "temperature" in message or "temp" in message or "warm" in message or "cold" in message:
            temp_match = re.search(r"(\d+)", message)
            if temp_match:
                planned.append({"name": "set_temperature", "params": {"temp": int(temp_match.group(1))}})

        if "ac" in message or "air conditioning" in message:
            ac_on = "on" in message or "enable" in message or "turn on" in message
            if "off" in message or "disable" in message:
                ac_on = False
            planned.append({"name": "toggle_ac", "params": {"ac_on": ac_on}})

        if "fan" in message:
            fan_match = re.search(r"fan.*?(\d+)", message)
            if fan_match:
                planned.append({"name": "set_fan_speed", "params": {"speed": int(fan_match.group(1))}})

        if "seat" in message and "heat" in message:
            seat_match = re.search(r"(driver|passenger|rear).*?(\d+)", message)
            if seat_match:
                planned.append({
                    "name": "set_seat_heating",
                    "params": {"zone": seat_match.group(1), "level": int(seat_match.group(2))},
                })

        if "defrost" in message:
            defrost_on = "on" in message or "enable" in message
            if "off" in message:
                defrost_on = False
            planned.append({"name": "toggle_rear_defrost", "params": {"defrost_on": defrost_on}})

    elif intent == "navigation":
        if any(kw in message for kw in ("navigate", "go to", "destination", "drive to")):
            dest_match = re.search(r"(?:navigate to|go to|destination|drive to)\s+(.+)", message)
            if dest_match:
                planned.append({"name": "set_destination", "params": {"place": dest_match.group(1).strip()}})

        if "nearby" in message or "nearest" in message:
            poi_match = re.search(r"(?:nearby|nearest)\s+(gas station|coffee shop|restaurant|parking)", message)
            if poi_match:
                poi_type = poi_match.group(1).replace(" ", "_")
                planned.append({"name": "get_nearby_poi", "params": {"poi_type": poi_type}})

        if "where am i" in message or "current location" in message or "my location" in message:
            planned.append({"name": "get_current_location", "params": {}})

        if "eta" in message or "arrival" in message or "how long" in message:
            planned.append({"name": "get_eta", "params": {}})

        if "toll" in message:
            avoid = "avoid" in message or "no toll" in message
            planned.append({"name": "avoid_tolls", "params": {"avoid": avoid}})

    elif intent == "media":
        if any(kw in message for kw in ("stop", "pause")):
            planned.append({"name": "pause_media", "params": {}})
        elif "resume" in message or "unpause" in message:
            planned.append({"name": "resume_media", "params": {}})
        elif "radio" in message and any(kw in message for kw in ("play", "start", "turn on")):
            planned.append({"name": "play_radio", "params": {}})
        elif "play" in message or "start" in message or "music" in message:
            genre_planned = False
            for genre in ("rock", "jazz", "classical", "pop", "electronic"):
                if genre in message:
                    planned.append({"name": "play_music", "params": {"genre": genre}})
                    genre_planned = True
                    break
            if not genre_planned:
                for mood in ("relaxed", "energetic", "happy", "focused"):
                    if mood in message:
                        planned.append({"name": "play_music", "params": {"mood": mood}})
                        genre_planned = True
                        break
            if not genre_planned:
                planned.append({"name": "resume_media", "params": {}})

        if "volume" in message:
            vol_match = re.search(r"(\d+)", message)
            if vol_match:
                planned.append({"name": "set_volume", "params": {"volume": int(vol_match.group(1))}})

        if "next" in message:
            planned.append({"name": "next_track", "params": {}})
        if "previous" in message or "last track" in message:
            planned.append({"name": "previous_track", "params": {}})

        if "what's playing" in message or "current track" in message or "now playing" in message:
            planned.append({"name": "get_current_track", "params": {}})

    elif intent == "vehicle_info":
        if "fuel" in message:
            planned.append({"name": "get_fuel_level", "params": {}})
        if any(kw in message for kw in ("stop the car", "stop car", "park the car", "park")):
            planned.append({"name": "stop_vehicle", "params": {}})
        elif "speed" in message and any(kw in message for kw in ("set", "to", "reduce", "slow")):
            speed_match = re.search(r"(\d+)", message)
            if speed_match:
                planned.append({"name": "set_speed", "params": {"speed": int(speed_match.group(1))}})
        elif "speed" in message:
            planned.append({"name": "get_current_speed", "params": {}})
        if "warning" in message or "alert" in message:
            planned.append({"name": "get_active_warnings", "params": {}})
        if "door" in message or ("lock" in message and "unlock" not in message) or "unlock" in message:
            if any(kw in message for kw in ("unlock", "open")):
                planned.append({"name": "set_doors_locked", "params": {"locked": False}})
            elif any(kw in message for kw in ("lock", "close")):
                planned.append({"name": "set_doors_locked", "params": {"locked": True}})
            elif any(kw in message for kw in ("status", "check", "are my")):
                planned.append({"name": "get_door_status", "params": {}})
        if "battery" in message:
            planned.append({"name": "get_battery_status", "params": {}})
        if "odometer" in message or "mileage" in message:
            planned.append({"name": "get_odometer_reading", "params": {}})
        if "status" in message or "everything" in message:
            planned.append({"name": "get_full_vehicle_state", "params": {}})

    state["tools_to_call"] = planned
    state["tool_results"] = []
    state["tools_called_names"] = []
    return state


def safety_validator_node(state: AgentState) -> AgentState:
    """Validate planned commands before any vehicle state is mutated."""
    blocked, reason = validate_planned_tools(
        state["user_message"],
        state["intent"],
        state.get("tools_to_call", []),
        state["vehicle_state"],
    )
    state["safety_blocked"] = blocked
    state["safety_reason"] = reason
    return state


def route_after_safety(state: AgentState) -> str:
    if state.get("safety_blocked"):
        return "response_generator"
    if state.get("tools_to_call"):
        return "tool_executor"
    return "response_generator"


def tool_executor_node(state: AgentState) -> AgentState:
    """Execute planned MCP tools via the unified MCP client."""
    results = []
    called_names = []

    for tool in state.get("tools_to_call", []):
        name = tool["name"]
        params = tool.get("params", {})
        result = call_tool(name, params)
        results.append(result)
        called_names.append(name)

    state["tool_results"] = results
    state["tools_called_names"] = called_names
    return state


def response_generator_node(state: AgentState) -> AgentState:
    """Generate natural language response with multi-turn memory context."""
    history_context = format_conversation_context(state.get("conversation_history", []))

    if state.get("safety_blocked"):
        state["response"] = state["safety_reason"]
        return state

    if state.get("tool_results"):
        results_text = ", ".join(str(r) for r in state["tool_results"])
        if llm:
            prompt = f"""
You are a BMW in-vehicle AI assistant. Generate a natural, conversational response
based on the tool results. Reference prior conversation when relevant.

Recent conversation:
{history_context}

User request: {state['user_message']}
Intent: {state['intent']}
Tool results: {results_text}

Keep it friendly, professional, and concise.
"""
            state["response"] = llm.invoke([SystemMessage(content=prompt)]).content
        else:
            state["response"] = _template_response(state)
    else:
        if llm:
            prompt = f"""
You are a BMW in-vehicle AI assistant. Respond conversationally.
Use prior conversation context when the user refers to earlier topics.

Recent conversation:
{history_context}

Context:
{state.get('enriched_message', state['user_message'])}

Keep it friendly, professional, and concise.
"""
            state["response"] = llm.invoke([SystemMessage(content=prompt)]).content
        else:
            state["response"] = "I'm your BMW AI assistant. How can I help you today?"

    return state


def _template_response(state: AgentState) -> str:
    names = state.get("tools_called_names", [])
    results = state.get("tool_results", [])

    if "set_temperature" in names:
        idx = names.index("set_temperature")
        temp = results[idx].get("temperature", "N/A")
        return f"I've set the cabin temperature to {temp}°C."
    if "set_destination" in names:
        idx = names.index("set_destination")
        dest = results[idx].get("destination", "N/A")
        return f"Navigation set to {dest}. ETA: {results[idx].get('eta', 'updated')}."
    if "play_music" in names or "play_radio" in names:
        idx = 0
        track = results[idx].get("track") or results[idx].get("station", "unknown")
        return f"Now playing: {track}"
    if "set_volume" in names:
        idx = names.index("set_volume")
        return f"Volume set to {results[idx].get('volume', 'N/A')}."
    if "set_doors_locked" in names:
        idx = names.index("set_doors_locked")
        return results[idx].get("message", "Door status updated.")
    if "pause_media" in names:
        return "Media playback paused."
    if "resume_media" in names:
        return "Media playback resumed."
    if results:
        return f"Done. {results[0]}"
    return f"Command processed. Intent: {state['intent']}"


def memory_update_node(state: AgentState) -> AgentState:
    """Persist conversation turn to SQLite memory."""
    session_id = state.get("session_id", "default_session")
    create_session(session_id, state["vehicle_state"])
    save_conversation(
        session_id=session_id,
        user_message=state["user_message"],
        intent=state["intent"],
        tools_called=state.get("tools_called_names", []),
        response=state["response"],
        safety_blocked=state.get("safety_blocked", False),
        safety_reason=state.get("safety_reason"),
    )
    return state


def build_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("input_processor", input_processor_node)
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("tool_planner", tool_planner_node)
    workflow.add_node("safety_validator", safety_validator_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("response_generator", response_generator_node)
    workflow.add_node("memory_update", memory_update_node)

    workflow.set_entry_point("input_processor")
    workflow.add_edge("input_processor", "intent_classifier")
    workflow.add_edge("intent_classifier", "tool_planner")
    workflow.add_edge("tool_planner", "safety_validator")
    workflow.add_conditional_edges(
        "safety_validator",
        route_after_safety,
        {"tool_executor": "tool_executor", "response_generator": "response_generator"},
    )
    workflow.add_edge("tool_executor", "response_generator")
    workflow.add_edge("response_generator", "memory_update")
    workflow.add_edge("memory_update", END)

    return workflow.compile()


agent = build_agent()
