#!/usr/bin/env python3
"""
Blood Report Analysis System - Main Entry Point
Multi-Agent AI System for Medical Report Processing with Phase-2 LLM Analysis
"""

import sys
import os
import subprocess

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.ollama_manager import auto_start_ollama

def main():
    """Main entry point for the Blood Report Analysis System"""
    print("🩺 Blood Report Analysis System")
    print("=" * 50)
    
    # Auto-start Ollama
    print("🚀 Initializing AI services...")
    setup_result = auto_start_ollama()
    
    for message in setup_result["messages"]:
        print(f"   {message}")
    
    if setup_result["ready"]:
        print("\n✅ System fully ready with AI analysis!")
    else:
        print("\n⚠️  AI analysis limited - Phase-1 analysis available")
    
    print("\nAvailable commands:")
    print("1. streamlit run src/ui/UI.py  - Start web interface")
    print("2. python setup_phase2.py     - Setup Phase-2 AI")
    print("3. python tests/test_phase2.py - Run tests")
    print("4. python start_project.py    - Auto-start with Ollama")
    print()
    print("Recommended: python start_project.py")

if __name__ == "__main__":
    main()