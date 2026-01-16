

#!/usr/bin/env python3
"""
Blood Report Analysis System
Main entry point for the application
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Start the Blood Report Analysis System"""
    
    print("🩺 Blood Report Analysis System")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("src/ui/UI.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    print("🚀 Starting the application...")
    print("📱 The web interface will open at: http://localhost:8501")
    print("🔄 Press Ctrl+C to stop the application")
    print()
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/ui/UI.py", 
            "--server.port", "8501",
            "--server.headless", "true"
        ], check=True)
    
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()