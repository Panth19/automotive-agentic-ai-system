# BMW Automotive AI Assistant

A comprehensive in-vehicle AI assistant built with FastAPI, LangGraph, MCP (Model Context Protocol), Whisper, OpenCV, and Streamlit.

## Features

- **Voice Input** via OpenAI Whisper (speech-to-text)
- **Vision Analysis** via OpenCV (dashboard warning light detection)
- **6-Node LangGraph Agent** for reasoning and decision making
- **MCP Servers** for vehicle state, climate, navigation, and media control
- **Safety Validation** to block dangerous actions while driving
- **SQLite Memory** for conversation history
- **Streamlit UI** with live dashboard and logs
- **Text-to-Speech** via pyttsx3

## Architecture

```
User → Streamlit UI → FastAPI → LangGraph Agent → MCP Servers → Vehicle State
                                       ↓
                              SQLite Memory DB
```

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # add your GROQ_API_KEY
python run_all.py
```

- API: http://localhost:8000
- UI: http://localhost:8501

## Project Structure

See `all.md` for the complete documentation and file listing.
