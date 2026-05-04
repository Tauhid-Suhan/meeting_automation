"""
config/settings.py
Loads all environment variables with validation.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"  → Copy .env.example to .env and fill in your values."
        )
    return val


# Google Calendar
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Zoom (Server-to-Server OAuth)
ZOOM_ACCOUNT_ID = _require("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = _require("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = _require("ZOOM_CLIENT_SECRET")
ZOOM_BASE_URL = "https://api.zoom.us/v2"
ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"

# Notion
NOTION_TOKEN = _require("NOTION_TOKEN")
NOTION_DATABASE_ID = _require("NOTION_DATABASE_ID")
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# App
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "14"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
