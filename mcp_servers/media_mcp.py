"""
Media MCP Server
Controls vehicle media system
"""
from fastmcp import FastMCP
import random

mcp = FastMCP("media-control")

from mcp_servers.vehicle_state_mcp import vehicle_state

# Sample music database
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
        # Map moods to genres
        mood_to_genre = {
            "relaxed": "classical",
            "energetic": "rock",
            "happy": "pop",
            "focused": "jazz"
        }
        genre = mood_to_genre.get(mood.lower(), "pop")
        track = random.choice(music_database[genre])
        vehicle_state["media"]["current_track"] = track
        vehicle_state["media"]["is_playing"] = True
        return {"status": "success", "track": track, "mood": mood}
    
    vehicle_state["media"]["is_playing"] = True
    return {
        "status": "success",
        "track": vehicle_state["media"]["current_track"],
        "is_playing": True,
        "message": "Playing current selection",
    }

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
    
    # Play default station
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
    return {
        "current_track": vehicle_state["media"]["current_track"],
        "is_playing": vehicle_state["media"]["is_playing"],
        "volume": vehicle_state["media"]["volume"]
    }

if __name__ == "__main__":
    mcp.run()
