"""
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
    
    # Keyword-based classification (works without LLM)
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
            temp_match = re.search(r'(\d+)', message)
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
        # ... more climate tools
    
    elif intent == "navigation":
        if "navigate" in message or "go to" in message or "destination" in message:
            dest_match = re.search(r'(?:navigate to|go to|destination).*?(?:to\s+)?(.+)', message)
            if dest_match:
                dest = dest_match.group(1).strip()
                tools_called.append({"name": "set_destination", "params": {"place": dest}})
                result = set_destination(dest)
                tool_results.append(result)
        # ... more navigation tools
    
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
        # ... more media tools
    
    elif intent == "vehicle_info":
        if "fuel" in message:
            tools_called.append({"name": "get_fuel_level", "params": {}})
            from mcp_servers.vehicle_state_mcp import get_fuel_level
            result = get_fuel_level()
            tool_results.append(result)
        # ... more vehicle info tools
    
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
    
    temp_match = re.search(r'temperature.*?(\d+)', state['user_message'].lower())
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
            # Use Groq LLM for natural response
            prompt = f"""You are a BMW in-vehicle AI assistant. Generate a natural, conversational response."""
            response = llm.invoke([SystemMessage(content=prompt)]).content
        else:
            # Fallback template response
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
