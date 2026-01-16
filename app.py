"""
Blood Report Analysis System - Hugging Face Spaces Entry Point
This file serves as the main entry point for Hugging Face Spaces deployment.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set environment for HF Spaces (use HF API by default if no Ollama)
if not os.getenv("LLM_PROVIDER_PRIORITY"):
    os.environ["LLM_PROVIDER_PRIORITY"] = "ollama_first"

# Import and run the main UI
from ui.UI import *

if __name__ == "__main__":
    # This is handled by Streamlit
    pass
