# Deployment Guide

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
python run_all.py
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8501
CMD ["python", "run_all.py"]
```

### Environment Variables

- `GROQ_API_KEY`: Your Groq API key for LLM inference
- `WHISPER_MODEL_SIZE`: Whisper model size (default: base)
- `TTS_ENABLED`: Enable text-to-speech (default: true)

## Services

- **FastAPI Backend**: Port 8000
- **Streamlit Frontend**: Port 8501
