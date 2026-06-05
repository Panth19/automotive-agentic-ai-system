"""
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
