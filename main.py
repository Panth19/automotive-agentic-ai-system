"""
FastAPI Backend - The Central Nervous System
Connects all components together
"""
import os
import json
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import sys
sys.path.insert(0, '/workspace')

from mcp_servers.vehicle_state_mcp import vehicle_state
from agent.langgraph_agent import agent
from database.memory_db import get_conversation_history

app = FastAPI(title="BMW Automotive AI Assistant", version="1.0.0")

# Lazy load Whisper (may fail on some Windows systems)
whisper_model = None
whisper_available = False

try:
    import whisper
    whisper_model = whisper.load_model("base")
    whisper_available = True
except Exception as e:
    print(f"Warning: Whisper not available - {e}")
    print("Speech-to-text will use fallback mode")

# Lazy load OpenCV
cv2_available = False
try:
    import cv2
    cv2_available = True
except Exception as e:
    print(f"Warning: OpenCV not available - {e}")
    print("Vision analysis will use fallback mode")

# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "BMW Automotive AI Assistant API", "status": "online"}

@app.get("/status")
async def get_status():
    """Get current vehicle state"""
    return vehicle_state

@app.post("/speech")
async def speech_to_text(audio: UploadFile = File(...)):
    """Convert speech to text using Whisper (with fallback)"""
    try:
        if whisper_available:
            # Save audio temporarily
            audio_path = f"temp_{audio.filename}"
            with open(audio_path, "wb") as f:
                content = await audio.read()
                f.write(content)
            
            # Transcribe with Whisper
            result = whisper_model.transcribe(audio_path)
            text = result["text"]
            
            # Clean up
            os.remove(audio_path)
            
            return {"text": text, "confidence": result.get("confidence", 0.9)}
        else:
            # Fallback: return placeholder text
            return {"text": "[Speech detected - Whisper unavailable]", "confidence": 0.5}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision")
async def vision_analysis(image: UploadFile = File(...)):
    """Analyze dashboard image using OpenCV (with fallback)"""
    try:
        if cv2_available:
            # Read image
            content = await image.read()
            nparr = np.frombuffer(content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Detect red warnings (danger)
            red_lower = np.array([0, 100, 100])
            red_upper = np.array([10, 255, 255])
            red_mask1 = cv2.inRange(hsv, red_lower, red_upper)
            
            red_lower2 = np.array([170, 100, 100])
            red_upper2 = np.array([180, 255, 255])
            red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
            
            red_detected = np.count_nonzero(red_mask1) + np.count_nonzero(red_mask2)
            
            # Detect yellow warnings (caution)
            yellow_lower = np.array([20, 100, 100])
            yellow_upper = np.array([30, 255, 255])
            yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
            yellow_detected = np.count_nonzero(yellow_mask)
            
            # Generate analysis text
            analysis = []
            if red_detected > 1000:
                analysis.append("Red warning light detected - possible engine or brake issue")
                vehicle_state["warnings"].append("red_warning_detected")
            if yellow_detected > 1000:
                analysis.append("Yellow warning light detected - check vehicle status")
                vehicle_state["warnings"].append("yellow_warning_detected")
            
            if not analysis:
                analysis.append("No warning lights detected - dashboard appears normal")
            
            return {"analysis": analysis, "red_pixels": int(red_detected), "yellow_pixels": int(yellow_detected)}
        else:
            # Fallback: return placeholder
            return {"analysis": ["Vision analysis - OpenCV unavailable"], "red_pixels": 0, "yellow_pixels": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat message through LangGraph agent"""
    try:
        # Get conversation history
        history = get_conversation_history(request.session_id)
        
        # Run agent
        initial_state = {
            "user_message": request.message,
            "conversation_history": history,
            "vehicle_state": vehicle_state,
            "intent": None,
            "tools_to_call": [],
            "tool_results": [],
            "response": None,
            "safety_blocked": False,
            "safety_reason": None,
            "tools_called_names": []
        }
        
        result = agent.invoke(initial_state)
        
        return {
            "response": result["response"],
            "intent": result["intent"],
            "tools_called": result["tools_called_names"],
            "safety_blocked": result["safety_blocked"],
            "vehicle_state": vehicle_state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream AI response word by word"""
    async def generate():
        # Run agent
        history = get_conversation_history(request.session_id)
        
        initial_state = {
            "user_message": request.message,
            "conversation_history": history,
            "vehicle_state": vehicle_state,
            "intent": None,
            "tools_to_call": [],
            "tool_results": [],
            "response": None,
            "safety_blocked": False,
            "safety_reason": None,
            "tools_called_names": []
        }
        
        result = agent.invoke(initial_state)
        
        # Stream word by word
        words = result["response"].split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.05)
        
        # Send final state
        yield json.dumps({"vehicle_state": vehicle_state}) + "\n"
    
    return StreamingResponse(generate(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
