"""
Speech-to-text service for voice commands.
Uses local Whisper when available, otherwise Groq Whisper API.
"""
import os
import tempfile
from typing import Tuple

_whisper_model = None
_whisper_available = False

try:
    import whisper
    _whisper_model = whisper.load_model("base")
    _whisper_available = True
except Exception as exc:
    print(f"Warning: Local Whisper not available - {exc}")


def _extension_for_filename(filename: str | None) -> str:
    if not filename or "." not in filename:
        return ".wav"
    ext = "." + filename.rsplit(".", 1)[-1].lower()
    return ext if ext in (".wav", ".webm", ".mp3", ".m4a", ".ogg", ".flac", ".mp4") else ".wav"


def _transcribe_with_local_whisper(audio_path: str) -> Tuple[str, float]:
    result = _whisper_model.transcribe(audio_path)
    text = (result.get("text") or "").strip()
    confidence = float(result.get("confidence", 0.9) or 0.9)
    return text, confidence


def _transcribe_with_groq(audio_path: str) -> Tuple[str, float]:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or not api_key.startswith("gsk_"):
        raise RuntimeError("Groq API key not configured for speech fallback")

    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            response_format="verbose_json",
        )

    text = (getattr(transcription, "text", None) or "").strip()
    confidence = 0.92
    return text, confidence


def get_speech_status() -> dict:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    groq_available = bool(groq_key and groq_key.startswith("gsk_"))
    if _whisper_available:
        engine = "whisper-local"
    elif groq_available:
        engine = "groq-whisper"
    else:
        engine = "unavailable"

    return {
        "available": _whisper_available or groq_available,
        "engine": engine,
        "whisper_local": _whisper_available,
        "groq_whisper": groq_available,
    }


def transcribe_audio(audio_bytes: bytes, filename: str | None = None) -> Tuple[str, str, float]:
    """
    Transcribe audio bytes to text.
    Returns (text, engine_name, confidence).
    """
    if not audio_bytes:
        return "", "unavailable", 0.0

    suffix = _extension_for_filename(filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        audio_path = tmp.name

    try:
        status = get_speech_status()
        if not status["available"]:
            return "", "unavailable", 0.0

        if _whisper_available:
            text, confidence = _transcribe_with_local_whisper(audio_path)
            return text, "whisper-local", confidence

        text, confidence = _transcribe_with_groq(audio_path)
        return text, "groq-whisper", confidence
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            pass
