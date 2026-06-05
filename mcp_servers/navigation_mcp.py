"""
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
