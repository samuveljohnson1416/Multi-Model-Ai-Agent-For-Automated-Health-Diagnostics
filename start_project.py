#!/usr/bin/env python3
"""
Blood Report Analysis System - Project Launcher
Automatically starts Ollama and launches the Streamlit application
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.ollama_manager import auto_start_ollama


def main():
    """Main launcher function"""
    print("🩺 Blood Report Analysis System - Starting...")
    print("=" * 50)
    
    # Step 1: Setup Ollama
    print("🚀 Setting up Ollama AI service...")
    setup_result = auto_start_ollama()
    
    # Display setup results
    for message in setup_result["messages"]:
        print(f"   {message}")
    
    if not setup_result["ready"]:
        print("\n⚠️  Warning: Ollama setup incomplete")
        print("   - AI analysis will be limited")
        print("   - You can still use Phase-1 analysis")
        
        response = input("\nContinue anyway? (y/n): ").lower().strip()
        if response != 'y':
            print("Exiting...")
            return
    else:
        print("\n✅ Ollama fully ready for AI analysis!")
    
    # Step 2: Launch Streamlit
    print("\n🌐 Launching Streamlit application...")
    print("   Opening in your default browser...")
    
    try:
        # Launch Streamlit
        ui_path = Path(__file__).parent / "src" / "ui" / "UI.py"
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(ui_path),
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        print("   Ollama will continue running in background")
        print("   Use 'ollama stop' to stop it manually if needed")
    except Exception as e:
        print(f"\n❌ Error launching Streamlit: {e}")
        print("   You can manually run: streamlit run src/ui/UI.py")


if __name__ == "__main__":
    main()