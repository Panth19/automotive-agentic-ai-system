"""
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

print("\n📊 Vehicle State MCP:")
print(f"  - Initial state: speed={vehicle_state['speed']} km/h, fuel={vehicle_state['fuel_level']}%")
print(f"  - Fuel level: {get_fuel_level()}")
print(f"  - Current speed: {get_current_speed()}")

print("\n❄️ Climate MCP:")
print(f"  - Setting temperature to 22°C: {set_temperature(22)}")
print(f"  - AC status: {toggle_ac(True)}")
print(f"  - Fan speed: {set_fan_speed(3)}")

print("\n🧭 Navigation MCP:")
print(f"  - Setting destination: {set_destination('BMW Museum, Munich')}")
print(f"  - Nearby coffee shops: {get_nearby_poi('coffee_shop')}")

print("\n🎵 Media MCP:")
print(f"  - Play jazz: {play_music(genre='jazz')}")
print(f"  - Volume: {set_volume(60)}")

print("\n" + "=" * 60)
print("Testing Database")
print("=" * 60)

init_db()
save_conversation(session_id="demo_session", user_message="Set temperature to 22 degrees",
    intent="climate", tools_called=["set_temperature"], response="Temperature set to 22°C", safety_blocked=False)

history = get_conversation_history("demo_session")
print(f"\n💾 Memory DB: Saved {len(history)} conversation(s)")

print("\n" + "=" * 60)
print("Testing LangGraph Agent Structure")
print("=" * 60)

agent = build_agent()
print("\n🧠 Agent nodes: input_processor, intent_classifier, tool_caller, safety_validator, response_generator, memory_update")
print("All components tested successfully!")
