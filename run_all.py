"""
Run script to start all services
"""
import subprocess
import sys
import time

def main():
    print("🚀 Starting BMW Automotive AI Assistant...")
    
    api_process = subprocess.Popen([sys.executable, "main.py"])
    time.sleep(2)
    
    ui_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py"])
    
    print("\n✅ System started!")
    print("API: http://localhost:8000")
    print("UI: http://localhost:8501")
    print("\nPress Ctrl+C to stop...")
    
    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api_process.terminate()
        ui_process.terminate()

if __name__ == "__main__":
    main()
