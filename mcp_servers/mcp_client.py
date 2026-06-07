"""
MCP Client - Unified interface connecting the LangGraph agent to automotive MCP tools.

In production this would use the MCP protocol over stdio/HTTP. For the prototype,
tools are invoked in-process via their registered Python callables while preserving
the same discovery and execution API.
"""
from typing import Any, Callable, Dict, List, Optional

from mcp_servers.climate_mcp import (
    set_temperature,
    toggle_ac,
    set_fan_speed,
    set_seat_heating,
    toggle_rear_defrost,
)
from mcp_servers.navigation_mcp import (
    set_destination,
    get_current_location,
    get_eta,
    avoid_tolls,
    get_nearby_poi,
)
from mcp_servers.media_mcp import (
    play_music,
    set_volume,
    next_track,
    previous_track,
    play_radio,
    pause_media,
    resume_media,
    get_current_track,
)
from mcp_servers.vehicle_state_mcp import (
    get_fuel_level,
    get_current_speed,
    set_speed,
    stop_vehicle,
    get_active_warnings,
    get_odometer_reading,
    get_battery_status,
    get_door_status,
    set_doors_locked,
    get_full_vehicle_state,
)

ToolCallable = Callable[..., dict]

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "set_temperature": {"fn": set_temperature, "server": "climate-control", "mutates": True},
    "toggle_ac": {"fn": toggle_ac, "server": "climate-control", "mutates": True},
    "set_fan_speed": {"fn": set_fan_speed, "server": "climate-control", "mutates": True},
    "set_seat_heating": {"fn": set_seat_heating, "server": "climate-control", "mutates": True},
    "toggle_rear_defrost": {"fn": toggle_rear_defrost, "server": "climate-control", "mutates": True},
    "set_destination": {"fn": set_destination, "server": "navigation", "mutates": True},
    "get_current_location": {"fn": get_current_location, "server": "navigation", "mutates": False},
    "get_eta": {"fn": get_eta, "server": "navigation", "mutates": False},
    "avoid_tolls": {"fn": avoid_tolls, "server": "navigation", "mutates": False},
    "get_nearby_poi": {"fn": get_nearby_poi, "server": "navigation", "mutates": False},
    "play_music": {"fn": play_music, "server": "media-control", "mutates": True},
    "set_volume": {"fn": set_volume, "server": "media-control", "mutates": True},
    "next_track": {"fn": next_track, "server": "media-control", "mutates": True},
    "previous_track": {"fn": previous_track, "server": "media-control", "mutates": True},
    "play_radio": {"fn": play_radio, "server": "media-control", "mutates": True},
    "pause_media": {"fn": pause_media, "server": "media-control", "mutates": True},
    "resume_media": {"fn": resume_media, "server": "media-control", "mutates": True},
    "get_current_track": {"fn": get_current_track, "server": "media-control", "mutates": False},
    "get_fuel_level": {"fn": get_fuel_level, "server": "vehicle-state", "mutates": False},
    "get_current_speed": {"fn": get_current_speed, "server": "vehicle-state", "mutates": False},
    "set_speed": {"fn": set_speed, "server": "vehicle-state", "mutates": True},
    "stop_vehicle": {"fn": stop_vehicle, "server": "vehicle-state", "mutates": True},
    "get_active_warnings": {"fn": get_active_warnings, "server": "vehicle-state", "mutates": False},
    "get_odometer_reading": {"fn": get_odometer_reading, "server": "vehicle-state", "mutates": False},
    "get_battery_status": {"fn": get_battery_status, "server": "vehicle-state", "mutates": False},
    "get_door_status": {"fn": get_door_status, "server": "vehicle-state", "mutates": False},
    "set_doors_locked": {"fn": set_doors_locked, "server": "vehicle-state", "mutates": True},
    "get_full_vehicle_state": {"fn": get_full_vehicle_state, "server": "vehicle-state", "mutates": False},
}


def list_tools() -> List[Dict[str, str]]:
    """List all available MCP tools (MCP discovery equivalent)."""
    return [
        {"name": name, "server": meta["server"], "mutates": meta["mutates"]}
        for name, meta in TOOL_REGISTRY.items()
    ]


def call_tool(name: str, params: Optional[Dict[str, Any]] = None) -> dict:
    """Execute an MCP tool by name with parameters."""
    if name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {name}"}

    params = params or {}
    try:
        return TOOL_REGISTRY[name]["fn"](**params)
    except TypeError as exc:
        return {"error": f"Invalid parameters for {name}: {exc}"}
    except Exception as exc:
        return {"error": f"Tool execution failed: {exc}"}
