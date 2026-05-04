import os
import re
import logging
from datetime import datetime, timezone, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import (
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_TOKEN_PATH,
    GOOGLE_CALENDAR_ID,
    DAYS_AHEAD,
)

logger = logging.getLogger(__name__)

# Read-only access to Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Regex to extract Zoom meeting ID and join URL from event description/location
ZOOM_URL_PATTERN = re.compile(
    r"https://[\w.]*zoom\.us/j/(\d+)(?:\?pwd=([\w-]+))?", re.IGNORECASE
)
ZOOM_ID_PATTERN = re.compile(r"Meeting ID[:\s]+(\d[\d\s]+\d)", re.IGNORECASE)


class GoogleCalendarService:
    def __init__(self):
        self._service = self._authenticate()

    def _authenticate(self):
        """OAuth2 flow — opens browser on first run, caches token after."""
        creds = None

        if os.path.exists(GOOGLE_TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Google credentials file not found at '{GOOGLE_CREDENTIALS_PATH}'.\n"
                        "  → Download it from Google Cloud Console → APIs & Services → Credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(GOOGLE_TOKEN_PATH, "w") as token_file:
                token_file.write(creds.to_json())

        return build("calendar", "v3", credentials=creds)

    def get_zoom_meetings(self) -> list[dict]:
        
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=DAYS_AHEAD)

        logger.debug(f"Fetching events from {now.date()} to {end.date()}")

        events_result = (
            self._service.events()
            .list(
                calendarId=GOOGLE_CALENDAR_ID,
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            )
            .execute()
        )

        raw_events = events_result.get("items", [])
        zoom_meetings = []

        for event in raw_events:
            parsed = self._parse_zoom_event(event)
            if parsed:
                zoom_meetings.append(parsed)

        return zoom_meetings

    def _parse_zoom_event(self, event: dict) -> dict | None:
        description = event.get("description", "") or ""
        location = event.get("location", "") or ""
        combined_text = f"{description} {location}"

        url_match = ZOOM_URL_PATTERN.search(combined_text)
        if not url_match:
            return None  # Not a Zoom meeting

        zoom_join_url = url_match.group(0)
        zoom_meeting_id = url_match.group(1).replace(" ", "")

        # Parse start/end time
        start_raw = event.get("start", {})
        end_raw = event.get("end", {})
        start_time = start_raw.get("dateTime") or start_raw.get("date")
        end_time = end_raw.get("dateTime") or end_raw.get("date")

        # Calculate duration
        duration_minutes = 0
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        except Exception:
            pass

        # Parse attendees
        attendees = [
            {
                "email": a.get("email", ""),
                "name": a.get("displayName", a.get("email", "")),
                "response": a.get("responseStatus", "unknown"),
            }
            for a in event.get("attendees", [])
        ]

        return {
            "title": event.get("summary", "Zoom Meeting"),
            "zoom_meeting_id": zoom_meeting_id,
            "zoom_join_url": zoom_join_url,
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration_minutes,
            "attendees": attendees,
            "description": description,
            "google_event_id": event.get("id", ""),
            "organizer_email": event.get("organizer", {}).get("email", ""),
            "status": "Scheduled",
            "recording_url": "",
            "transcript": "",
        }
