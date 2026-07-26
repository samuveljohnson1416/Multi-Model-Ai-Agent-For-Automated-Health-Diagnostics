"""
Frontend configuration — API URL and settings.
"""

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
APP_TITLE = "🩸 Health Diagnostics AI"
APP_SUBTITLE = "Multi-Model Blood Report Analysis"
POLLING_INTERVAL = 3
MAX_FILE_SIZE_MB = 10
