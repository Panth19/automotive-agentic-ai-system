"""
Safety guardrails - validate planned vehicle commands before execution.
"""
import re
from typing import Dict, List, Optional, Tuple

DANGEROUS_WHILE_MOVING = [
    "turn off engine",
    "unlock all doors",
    "disable warning",
    "open trunk",
    "disable brakes",
]

TEMP_MIN = 16
TEMP_MAX = 30
VOLUME_MIN = 0
VOLUME_MAX = 100
FAN_MIN = 1
FAN_MAX = 5
SEAT_HEAT_MAX = 3
COMPLEX_NAV_SPEED_LIMIT = 80


def validate_planned_tools(
    user_message: str,
    intent: str,
    planned_tools: List[Dict],
    vehicle_state: Dict,
) -> Tuple[bool, Optional[str]]:
    """
    Validate planned tool calls before execution.
    Returns (is_blocked, reason).
    """
    message = user_message.lower()
    speed = vehicle_state.get("speed", 0)

    if speed > 0:
        for dangerous in DANGEROUS_WHILE_MOVING:
            if dangerous in message:
                return True, (
                    f"I can't {dangerous} while driving at {speed} km/h. "
                    "Please stop the vehicle first."
                )

    if speed > COMPLEX_NAV_SPEED_LIMIT and intent == "navigation":
        if any(kw in message for kw in ("search", "find", "look for")):
            return True, (
                f"I can't perform complex navigation searches while driving at "
                f"{speed} km/h. Please focus on the road."
            )

    for tool in planned_tools:
        name = tool.get("name", "")
        params = tool.get("params", {})

        if name == "set_temperature":
            temp = params.get("temp")
            if temp is not None and (temp < TEMP_MIN or temp > TEMP_MAX):
                return True, (
                    f"Temperature {temp}°C is outside the safe range "
                    f"({TEMP_MIN}-{TEMP_MAX}°C). Please choose a comfortable temperature."
                )

        if name == "set_volume":
            volume = params.get("volume")
            if volume is not None and (volume < VOLUME_MIN or volume > VOLUME_MAX):
                return True, (
                    f"Volume {volume} is outside the safe range "
                    f"({VOLUME_MIN}-{VOLUME_MAX})."
                )

        if name == "set_fan_speed":
            fan = params.get("speed")
            if fan is not None and (fan < FAN_MIN or fan > FAN_MAX):
                return True, f"Fan speed must be between {FAN_MIN} and {FAN_MAX}."

        if name == "set_seat_heating":
            level = params.get("level")
            if level is not None and (level < 0 or level > SEAT_HEAT_MAX):
                return True, f"Seat heating level must be between 0 and {SEAT_HEAT_MAX}."

        if name == "set_destination" and speed > 100:
            dest = params.get("place", "")
            if len(dest) > 50:
                return True, (
                    "Please set a shorter destination name while driving at high speed."
                )

        if name == "set_doors_locked" and speed > 0:
            locked = params.get("locked", True)
            if not locked:
                return True, (
                    f"I can't unlock or open doors while driving at {speed} km/h. "
                    "Please stop the vehicle first."
                )

    return False, None


def format_conversation_context(history: List[Dict], limit: int = 6) -> str:
    """Format recent conversation history for LLM context."""
    if not history:
        return "No prior conversation in this session."

    recent = history[-limit:]
    lines = []
    for turn in recent:
        lines.append(f"User: {turn.get('user_message', '')}")
        if turn.get("response"):
            lines.append(f"Assistant: {turn['response']}")
    return "\n".join(lines)
