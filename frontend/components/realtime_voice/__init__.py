"""Real-time microphone voice input using the browser Web Speech API."""
import os

import streamlit.components.v1 as components

_PARENT = os.path.dirname(os.path.abspath(__file__))
_realtime_voice = components.declare_component(
    "realtime_voice",
    path=os.path.join(_PARENT, "frontend"),
)


def realtime_voice_input(
    key: str | None = None,
    continuous: bool = False,
    button_label: str = "Start listening",
) -> dict | None:
    """
    Live microphone speech recognition in the browser.
    Returns dict like {"transcript": "...", "done": true} or None.
    """
    return _realtime_voice(
        continuous=continuous,
        button_label=button_label,
        key=key,
        default=None,
    )
