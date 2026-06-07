"""
FastAPI Backend - The Central Nervous System
Connects all components together
"""
import asyncio
import copy
import io
import json
import os
import sys

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.langgraph_agent import agent
from database.memory_db import create_session, get_conversation_history
from mcp_servers.vehicle_state_mcp import stop_vehicle, vehicle_state
from utils.speech_service import get_speech_status, transcribe_audio
from utils.vision_simulator import create_dashboard_image

app = FastAPI(title="BMW Automotive AI Assistant", version="1.0.0")

# Allow Streamlit frontend (and other local dev origins) to call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cv2_available = False
try:
    import cv2
    cv2_available = True
except Exception as exc:
    print(f"Warning: OpenCV not available - {exc}")
    print("Vision analysis will use fallback mode")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    vision_context: str | None = None


def _build_agent_state(message: str, session_id: str, vision_context: str | None = None) -> dict:
    create_session(session_id, vehicle_state)
    history = get_conversation_history(session_id)

    return {
        "user_message": message,
        "session_id": session_id,
        "vision_context": vision_context,
        "conversation_history": history,
        "vehicle_state": vehicle_state,
        "intent": None,
        "tools_to_call": [],
        "tool_results": [],
        "response": None,
        "safety_blocked": False,
        "safety_reason": None,
        "tools_called_names": [],
    }


@app.get("/")
async def root():
    return {"message": "BMW Automotive AI Assistant API", "status": "online"}


@app.get("/status")
async def get_status():
    return vehicle_state


def _stop_car_response():
    result = stop_vehicle()
    return {
        "status": "success",
        "message": result.get("message", "Vehicle stopped"),
        "vehicle_state": copy.deepcopy(vehicle_state),
    }


@app.post("/vehicle/stop")
@app.post("/stop")
async def stop_car():
    """Stop the vehicle and set speed to 0 km/h."""
    return _stop_car_response()


@app.get("/dashboard-image")
async def get_dashboard_image(warning: str | None = None):
    """Return a simulated dashboard camera image for vision testing."""
    if not cv2_available:
        raise HTTPException(status_code=503, detail="OpenCV not available")

    warning_type = warning if warning in ("red", "yellow") else None
    img = create_dashboard_image(vehicle_state, warning_type=warning_type)
    success, encoded = cv2.imencode(".jpg", img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode dashboard image")

    return StreamingResponse(io.BytesIO(encoded.tobytes()), media_type="image/jpeg")


@app.get("/speech/status")
async def speech_status():
    """Return speech-to-text engine availability."""
    return get_speech_status()


@app.post("/speech")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech to text using Whisper (local or Groq fallback)."""
    try:
        content = await audio.read()
        text, engine, confidence = transcribe_audio(content, audio.filename)
        if not text:
            status = get_speech_status()
            detail = (
                "Speech recognition unavailable. Set GROQ_API_KEY in .env "
                "or install local Whisper."
            )
            if not status["available"]:
                raise HTTPException(status_code=503, detail=detail)
            raise HTTPException(status_code=400, detail="Could not transcribe audio")

        return {"text": text, "confidence": confidence, "engine": engine}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/voice")
async def voice_command(
    audio: UploadFile = File(...),
    session_id: str = Form("default_session"),
    vision_context: str | None = Form(None),
):
    """Voice-first pipeline: speech-to-text then agent processing."""
    try:
        content = await audio.read()
        transcript, engine, confidence = transcribe_audio(content, audio.filename)
        if not transcript:
            raise HTTPException(
                status_code=400,
                detail="Could not understand audio. Speak clearly and try again.",
            )

        result = agent.invoke(_build_agent_state(transcript, session_id, vision_context))

        return {
            "transcript": transcript,
            "stt_engine": engine,
            "confidence": confidence,
            "response": result["response"],
            "intent": result["intent"],
            "tools_called": result.get("tools_called_names", []),
            "safety_blocked": result.get("safety_blocked", False),
            "safety_reason": result.get("safety_reason"),
            "vehicle_state": copy.deepcopy(vehicle_state),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/vision")
async def vision_analysis(image: UploadFile = File(...)):
    """Analyze dashboard image using OpenCV color detection."""
    try:
        if cv2_available:
            content = await image.read()
            nparr = np.frombuffer(content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise HTTPException(status_code=400, detail="Invalid image file")

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            red_lower = np.array([0, 100, 100])
            red_upper = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower, red_upper)

            red_lower2 = np.array([170, 100, 100])
            red_upper2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            red_detected = np.count_nonzero(red_mask1) + np.count_nonzero(red_mask2)

            yellow_lower = np.array([20, 100, 100])
            yellow_upper = np.array([30, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            yellow_detected = np.count_nonzero(yellow_mask)

            analysis = []
            vehicle_state["warnings"] = [
                w for w in vehicle_state.get("warnings", [])
                if w not in ("red_warning_detected", "yellow_warning_detected")
            ]

            if red_detected > 1000:
                analysis.append("Red warning light detected - possible engine or brake issue")
                vehicle_state["warnings"].append("red_warning_detected")
            if yellow_detected > 1000:
                analysis.append("Yellow warning light detected - check vehicle status")
                vehicle_state["warnings"].append("yellow_warning_detected")

            if not analysis:
                analysis.append("No warning lights detected - dashboard appears normal")

            return {
                "analysis": analysis,
                "analysis_text": "; ".join(analysis),
                "red_pixels": int(red_detected),
                "yellow_pixels": int(yellow_detected),
            }
        return {
            "analysis": ["Vision analysis - OpenCV unavailable"],
            "analysis_text": "Vision analysis - OpenCV unavailable",
            "red_pixels": 0,
            "yellow_pixels": 0,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat message through LangGraph agent."""
    try:
        result = agent.invoke(_build_agent_state(
            request.message,
            request.session_id,
            request.vision_context,
        ))

        return {
            "response": result["response"],
            "intent": result["intent"],
            "tools_called": result.get("tools_called_names", []),
            "safety_blocked": result.get("safety_blocked", False),
            "safety_reason": result.get("safety_reason"),
            "vehicle_state": copy.deepcopy(vehicle_state),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream AI response word by word."""

    async def generate():
        result = agent.invoke(_build_agent_state(
            request.message,
            request.session_id,
            request.vision_context,
        ))

        words = result["response"].split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)

        yield json.dumps({
            "vehicle_state": vehicle_state,
            "safety_blocked": result.get("safety_blocked", False),
            "safety_reason": result.get("safety_reason"),
        }) + "\n"

    return StreamingResponse(generate(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
