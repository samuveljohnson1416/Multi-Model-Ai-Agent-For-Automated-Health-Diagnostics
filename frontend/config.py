"""Frontend configuration — API URL and app constants."""

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

APP_TITLE = "Health Diagnostics"
APP_SUBTITLE = "Blood report analysis"

MAX_FILE_SIZE_MB = 10
SUPPORTED_TYPES = ["pdf", "png", "jpg", "jpeg", "json", "csv", "txt"]
