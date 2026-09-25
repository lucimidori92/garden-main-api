"""Runtime configuration for the garden-main-api."""

import os

WATERING_API_URL = os.getenv("WATERING_API_URL", "http://localhost:8001")
