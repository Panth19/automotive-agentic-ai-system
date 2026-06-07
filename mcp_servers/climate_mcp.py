"""
Climate Control MCP Server
Controls vehicle climate settings
"""
from fastmcp import FastMCP

mcp = FastMCP("climate-control")

from mcp_servers.vehicle_state_mcp import vehicle_state

@mcp.tool()
def set_temperature(temp: int, zone: str = "all") -> dict:
    """
    Set cabin temperature
    Args:
        temp: Temperature in Celsius (16-30)
        zone: 'driver', 'passenger', or 'all'
    """
    if temp < 16 or temp > 30:
        return {"error": "Temperature must be between 16°C and 30°C for safety and comfort"}
    
    if zone == "all":
        vehicle_state["cabin_temp"] = temp
    else:
        # In a real car, zones would be separate
        vehicle_state["cabin_temp"] = temp
    
    return {"status": "success", "temperature": temp, "zone": zone}

@mcp.tool()
def toggle_ac(ac_on: bool) -> dict:
    """Turn AC on or off"""
    vehicle_state["ac_on"] = ac_on
    return {"status": "success", "ac_on": ac_on}

@mcp.tool()
def set_fan_speed(speed: int) -> dict:
    """
    Set fan speed
    Args:
        speed: Fan speed 1-5
    """
    if speed < 1 or speed > 5:
        return {"error": "Fan speed must be between 1 and 5"}
    
    vehicle_state["fan_speed"] = speed
    return {"status": "success", "fan_speed": speed}

@mcp.tool()
def set_seat_heating(zone: str, level: int) -> dict:
    """
    Set seat heating level
    Args:
        zone: 'driver', 'passenger', or 'rear'
        level: Heating level 0-3 (0=off, 3=max)
    """
    if level < 0 or level > 3:
        return {"error": "Seat heating level must be between 0 and 3"}
    
    if zone in vehicle_state["seat_heating"]:
        vehicle_state["seat_heating"][zone] = level
        return {"status": "success", "zone": zone, "level": level}
    return {"error": f"Invalid zone: {zone}"}

@mcp.tool()
def toggle_rear_defrost(defrost_on: bool) -> dict:
    """Turn rear window defrost on or off"""
    # In real implementation, this would be a separate state
    return {"status": "success", "rear_defrost": defrost_on, "message": "Rear window defrost toggled"}

if __name__ == "__main__":
    mcp.run()
