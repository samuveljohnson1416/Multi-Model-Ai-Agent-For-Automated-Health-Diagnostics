#!/usr/bin/env python3
"""
Blood Report Analysis System - Main Entry Point
Multi-Agent AI System for Medical Report Processing with Phase-2 LLM Analysis
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point for the Blood Report Analysis System"""
    print("🩺 Blood Report Analysis System")
    print("=" * 50)
    print("Available commands:")
    print("1. streamlit run src/ui/UI.py  - Start web interface")
    print("2. python setup_phase2.py     - Setup Phase-2 AI")
    print("3. python tests/test_phase2.py - Run tests")
    print()
    print("For web interface: streamlit run src/ui/UI.py")

if __name__ == "__main__":
    main()