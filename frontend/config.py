"""Frontend configuration — API URL and app constants."""

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

# When the backend has API_KEY set, the frontend must send the same value.
# Leave unset for local development (the backend guard is then off).
API_KEY = os.getenv("API_KEY", "")

APP_TITLE = "Health Diagnostics"
APP_SUBTITLE = "Blood report analysis"

MAX_FILE_SIZE_MB = 10
SUPPORTED_TYPES = ["pdf", "png", "jpg", "jpeg", "json", "csv", "txt"]
