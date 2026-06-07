"""
Run script to start all services
"""
import subprocess
import sys
import time
import os

def main():
    print("🚀 Starting BMW Automotive AI Assistant...")
    
    # Start FastAPI in background
    print("Starting FastAPI backend...")
    api_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    time.sleep(4)  # Wait for API to start
    
    # Start Streamlit
    print("Starting Streamlit frontend...")
    ui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    
    print("\n✅ System started!")
    print("API: http://localhost:8000")
    print("UI: http://localhost:8501")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Keep running
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api_process.terminate()
        ui_process.terminate()

if __name__ == "__main__":
    main()
