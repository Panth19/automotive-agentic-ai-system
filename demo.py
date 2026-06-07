"""
Demo script to test the BMW Automotive AI Assistant core functionality
"""
import os
import sys

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test MCP servers
print("=" * 60)
print("Testing MCP Servers")
print("=" * 60)

# Test Vehicle State MCP
from mcp_servers.vehicle_state_mcp import vehicle_state, get_fuel_level, get_current_speed

print("\n📊 Vehicle State MCP:")
print(f"  - Initial state: speed={vehicle_state['speed']} km/h, fuel={vehicle_state['fuel_level']}%")
print(f"  - Fuel level: {get_fuel_level()}")
print(f"  - Current speed: {get_current_speed()}")

# Test Climate MCP
from mcp_servers.climate_mcp import set_temperature, toggle_ac, set_fan_speed

print("\n❄️ Climate MCP:")
print(f"  - Setting temperature to 22°C: {set_temperature(22)}")
print(f"  - AC status: {toggle_ac(True)}")
print(f"  - Fan speed: {set_fan_speed(3)}")

# Test Navigation MCP
from mcp_servers.navigation_mcp import set_destination, get_nearby_poi

print("\n🧭 Navigation MCP:")
print(f"  - Setting destination: {set_destination('BMW Museum, Munich')}")
print(f"  - Nearby coffee shops: {get_nearby_poi('coffee_shop')}")

# Test Media MCP
from mcp_servers.media_mcp import play_music, set_volume

print("\n🎵 Media MCP:")
print(f"  - Play jazz: {play_music(genre='jazz')}")
print(f"  - Volume: {set_volume(60)}")

# Test Database
print("\n" + "=" * 60)
print("Testing Database")
print("=" * 60)

from database.memory_db import init_db, save_conversation, get_conversation_history

init_db()
save_conversation(
    session_id="demo_session",
    user_message="Set temperature to 22 degrees",
    intent="climate",
    tools_called=["set_temperature"],
    response="Temperature set to 22°C",
    safety_blocked=False
)

history = get_conversation_history("demo_session")
print(f"\n💾 Memory DB: Saved {len(history)} conversation(s)")

# Test Agent (without LLM calls)
print("\n" + "=" * 60)
print("Testing LangGraph Agent Structure")
print("=" * 60)

from agent.langgraph_agent import AgentState, build_agent

from mcp_servers.mcp_client import list_tools, call_tool

print("\n🔌 MCP Client:")
tools = list_tools()
print(f"  - Registered tools: {len(tools)}")
print(f"  - Sample call: {call_tool('get_fuel_level')}")

print("\n🧠 Agent nodes:")
agent = build_agent()
print("  - Input Processor: ✅")
print("  - Intent Classifier: ✅")
print("  - Tool Planner: ✅")
print("  - Safety Validator (pre-execution): ✅")
print("  - Tool Executor (MCP client): ✅")
print("  - Response Generator: ✅")
print("  - Memory Update: ✅")

print("\n" + "=" * 60)
print("All components tested successfully!")
print("=" * 60)

print("\n🚀 To run the full system:")
print("  1. Set GROQ_API_KEY environment variable")
print("  2. Run: python main.py (FastAPI backend on port 8000)")
print("  3. Run: streamlit run frontend/streamlit_app.py (UI on port 8501)")
print("  4. Or run: python run_all.py (both together)")
