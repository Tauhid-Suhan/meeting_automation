"""
services/notion_service.py
Reads and writes to your Notion database via the Notion API.
"""

import logging
from datetime import datetime, timezone, timedelta

import requests

from config.settings import (
    NOTION_TOKEN,
    NOTION_DATABASE_ID,
    NOTION_BASE_URL,
    NOTION_VERSION,
)

logger = logging.getLogger(__name__)


class NotionService:
    def __init__(self):
        self._headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str) -> dict:
        r = requests.get(f"{NOTION_BASE_URL}{path}", headers=self._headers)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> dict:
        r = requests.post(f"{NOTION_BASE_URL}{path}", headers=self._headers, json=body)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, body: dict) -> dict:
        r = requests.patch(f"{NOTION_BASE_URL}{path}", headers=self._headers, json=body)
        r.raise_for_status()
        return r.json()

    # ------------------------------------------------------------------
    # Database queries
    # ------------------------------------------------------------------

    def find_meeting_by_zoom_id(self, zoom_meeting_id: str) -> dict | None:
        """Returns the Notion page dict if a meeting with this Zoom ID exists."""
        body = {
            "filter": {
                "property": "Zoom Meeting ID",
                "rich_text": {"equals": zoom_meeting_id},
            }
        }
        result = self._post(f"/databases/{NOTION_DATABASE_ID}/query", body)
        pages = result.get("results", [])
        if not pages:
            return None
        page = pages[0]
        return {
            "id": page["id"],
            "notion_page_id": page["id"],
            "zoom_meeting_id": zoom_meeting_id,
        }

    def get_meetings_missing_recordings(self) -> list[dict]:
        """
        Returns Notion pages for past meetings that don't have a recording URL yet.
        """
        now = datetime.now(timezone.utc).isoformat()
        body = {
            "filter": {
                "and": [
                    {
                        "property": "Start Time",
                        "date": {"before": now},
                    },
                    {
                        "property": "Recording URL",
                        "url": {"is_empty": True},
                    },
                    {
                        "property": "Status",
                        "select": {"equals": "Scheduled"},
                    },
                ]
            }
        }
        result = self._post(f"/databases/{NOTION_DATABASE_ID}/query", body)
        pages = result.get("results", [])

        meetings = []
        for page in pages:
            props = page.get("properties", {})
            zoom_id_prop = props.get("Zoom Meeting ID", {})
            zoom_id = ""
            for rt in zoom_id_prop.get("rich_text", []):
                zoom_id += rt.get("plain_text", "")
            meetings.append({
                "notion_page_id": page["id"],
                "zoom_meeting_id": zoom_id,
            })
        return meetings

    # ------------------------------------------------------------------
    # Create / Update
    # ------------------------------------------------------------------

    def create_meeting(self, meeting: dict) -> dict:
        """Creates a new page in the Notion database for a meeting."""
        body = {
            "parent": {"database_id": NOTION_DATABASE_ID},
            "properties": self._build_properties(meeting),
        }
        result = self._post("/pages", body)
        logger.debug(f"Created Notion page {result['id']} for meeting {meeting.get('zoom_meeting_id')}")
        return result

    def update_meeting(self, page_id: str, meeting: dict) -> dict:
        """Updates an existing Notion page with new meeting data."""
        body = {"properties": self._build_properties(meeting)}
        result = self._patch(f"/pages/{page_id}", body)
        logger.debug(f"Updated Notion page {page_id}")
        return result

    # ------------------------------------------------------------------
    # Property builder  (maps Python dict → Notion property format)
    # ------------------------------------------------------------------

    def _build_properties(self, m: dict) -> dict:
        props = {}

        if "title" in m:
            props["Meeting Title"] = {"title": [{"text": {"content": m["title"]}}]}

        if "zoom_meeting_id" in m:
            props["Zoom Meeting ID"] = {"rich_text": [{"text": {"content": m["zoom_meeting_id"]}}]}

        if "zoom_join_url" in m:
            props["Join URL"] = {"url": m["zoom_join_url"] or None}

        if "start_time" in m and m["start_time"]:
            props["Start Time"] = {"date": {"start": m["start_time"]}}

        if "end_time" in m and m["end_time"]:
            # Notion date property supports end date on same property
            if "Start Time" in props:
                props["Start Time"]["date"]["end"] = m["end_time"]

        if "duration_minutes" in m:
            props["Duration (min)"] = {"number": m["duration_minutes"]}

        if "status" in m:
            props["Status"] = {"select": {"name": m["status"]}}

        if "recording_url" in m and m["recording_url"]:
            props["Recording URL"] = {"url": m["recording_url"]}

        if "organizer_email" in m:
            props["Organizer"] = {"email": m["organizer_email"]}

        if "attendees" in m and m["attendees"]:
            attendee_text = self._format_attendees(m["attendees"])
            props["Attendees"] = {"rich_text": [{"text": {"content": attendee_text[:2000]}}]}

        if "transcript" in m and m["transcript"]:
            props["Transcript"] = {"rich_text": [{"text": {"content": m["transcript"][:2000]}}]}

        if "description" in m and m["description"]:
            props["Notes"] = {"rich_text": [{"text": {"content": m["description"][:2000]}}]}

        if "google_event_id" in m:
            props["Google Event ID"] = {"rich_text": [{"text": {"content": m["google_event_id"]}}]}

        return props

    @staticmethod
    def _format_attendees(attendees: list[dict]) -> str:
        lines = []
        for a in attendees:
            name = a.get("name") or a.get("email", "Unknown")
            email = a.get("email", "")
            duration = a.get("duration_seconds", 0)
            if duration:
                mins = duration // 60
                lines.append(f"{name} ({email}) — {mins} min")
            else:
                lines.append(f"{name} ({email})")
        return "\n".join(lines)
