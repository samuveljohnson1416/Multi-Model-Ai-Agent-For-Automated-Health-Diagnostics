#!/usr/bin/env python3
"""
Blood Report Analysis System - Entry Point
Starts the Streamlit application for blood report analysis.
"""

import subprocess
import sys
import os


def main():
    """Start the Blood Report Analysis application"""
    print("🩺 Blood Report Analysis System")
    print("=" * 50)
    print("🚀 Starting the application...")
    print("📱 The web interface will open at: http://localhost:8501")
    print("🔄 Press Ctrl+C to stop the application\n")
    
    # Get the path to UI.py
    ui_path = os.path.join(os.path.dirname(__file__), "src", "ui", "UI.py")
    
    try:
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", ui_path,
            "--server.port", "8501",
            "--server.headless", "true"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
