#!/usr/bin/env python3
"""
Blood Report Analysis System - Application Runner
Handles path setup and launches the Streamlit application
"""

import sys
import os
import subprocess

def setup_paths():
    """Setup Python paths for proper imports"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    
    # Add to Python path
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Set environment variable for subprocess
    env = os.environ.copy()
    pythonpath = env.get('PYTHONPATH', '')
    if src_dir not in pythonpath:
        env['PYTHONPATH'] = f"{src_dir}{os.pathsep}{pythonpath}" if pythonpath else src_dir
    
    return env

def main():
    """Main application runner"""
    print("🩺 Blood Report Analysis System")
    print("=" * 50)
    
    # Setup paths
    env = setup_paths()
    
    # Get UI file path
    ui_path = os.path.join('src', 'ui', 'UI.py')
    
    if not os.path.exists(ui_path):
        print(f"❌ Error: UI file not found at {ui_path}")
        return 1
    
    print(f"🚀 Starting Streamlit application...")
    print(f"📁 UI Path: {ui_path}")
    print(f"🌐 Will be available at: http://localhost:8501")
    print()
    
    try:
        # Launch Streamlit with proper environment
        subprocess.run(['streamlit', 'run', ui_path], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    except FileNotFoundError:
        print("❌ Error: Streamlit not found. Please install with: pip install streamlit")
        return 1

if __name__ == "__main__":
    exit(main())