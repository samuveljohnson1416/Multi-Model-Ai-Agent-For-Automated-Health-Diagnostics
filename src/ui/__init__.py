"""
UI module for Streamlit interface.
Contains main UI and chat interface components.
"""

from .chat_interface import create_medical_chat_interface

__all__ = [
    'create_medical_chat_interface',
]
