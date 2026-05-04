"""
services/zoom_service.py
Zoom Server-to-Server OAuth — fetches recordings, transcripts, participants.
"""

import logging
import requests
from datetime import datetime, timezone, timedelta

from config.settings import (
    ZOOM_ACCOUNT_ID,
    ZOOM_CLIENT_ID,
    ZOOM_CLIENT_SECRET,
    ZOOM_BASE_URL,
    ZOOM_OAUTH_URL,
)

logger = logging.getLogger(__name__)


class ZoomService:
    def __init__(self):
        self._access_token = None
        self._token_expires_at = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _get_access_token(self) -> str:
        """Server-to-Server OAuth — auto-refreshes when expired."""
        now = datetime.now(timezone.utc)
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token

        response = requests.post(
            ZOOM_OAUTH_URL,
            params={"grant_type": "account_credentials", "account_id": ZOOM_ACCOUNT_ID},
            auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expires_at = now + timedelta(seconds=expires_in - 60)

        logger.debug("Zoom access token refreshed")
        return self._access_token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._get_access_token()}"}

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{ZOOM_BASE_URL}{path}"
        response = requests.get(url, headers=self._headers(), params=params or {})
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Recordings
    # ------------------------------------------------------------------

    def get_recording(self, meeting_id: str) -> dict | None:
        """
        Returns recording info for a meeting.
        Zoom keeps recordings for 30 days by default.
        """
        data = self._get(f"/meetings/{meeting_id}/recordings")
        if not data or "recording_files" not in data:
            return None

        # Find the share URL and duration
        share_url = data.get("share_url", "")
        duration = data.get("duration", 0)

        # Find the video file URL
        video_url = ""
        for f in data.get("recording_files", []):
            if f.get("file_type") == "MP4" and f.get("status") == "completed":
                video_url = f.get("download_url", "")
                break

        return {
            "share_url": share_url,
            "video_url": video_url,
            "duration": duration,
            "recording_start": data.get("start_time", ""),
            "topic": data.get("topic", ""),
        }

    # ------------------------------------------------------------------
    # Transcripts
    # ------------------------------------------------------------------

    def get_transcript(self, meeting_id: str) -> str:
        """
        Returns the VTT transcript text if available.
        Zoom auto-generates transcripts when cloud recording + transcription is enabled.
        """
        data = self._get(f"/meetings/{meeting_id}/recordings")
        if not data:
            return ""

        # Find the transcript (VTT) file
        transcript_url = ""
        for f in data.get("recording_files", []):
            if f.get("file_type") == "TRANSCRIPT" and f.get("status") == "completed":
                transcript_url = f.get("download_url", "")
                break

        if not transcript_url:
            return ""

        try:
            token = self._get_access_token()
            resp = requests.get(
                transcript_url,
                headers={"Authorization": f"Bearer {token}"},
                params={"access_token": token},
            )
            resp.raise_for_status()
            return self._clean_vtt(resp.text)
        except Exception as e:
            logger.warning(f"Could not download transcript for {meeting_id}: {e}")
            return ""

    @staticmethod
    def _clean_vtt(vtt_text: str) -> str:
        """Strip VTT timing lines, keep only spoken text."""
        lines = []
        for line in vtt_text.splitlines():
            line = line.strip()
            if line.startswith("WEBVTT") or "-->" in line or line.isdigit() or not line:
                continue
            lines.append(line)
        return " ".join(lines)

    # ------------------------------------------------------------------
    # Participants
    # ------------------------------------------------------------------

    def get_meeting_participants(self, meeting_id: str) -> list[dict]:
        """
        Returns list of participants with name, email, join/leave times.
        Requires Reports scope on your Zoom app.
        """
        data = self._get(f"/report/meetings/{meeting_id}/participants", params={"page_size": 300})
        participants = data.get("participants", [])

        result = []
        for p in participants:
            result.append({
                "name": p.get("name", ""),
                "email": p.get("user_email", ""),
                "join_time": p.get("join_time", ""),
                "leave_time": p.get("leave_time", ""),
                "duration_seconds": p.get("duration", 0),
            })
        return result

    # ------------------------------------------------------------------
    # Meeting Info
    # ------------------------------------------------------------------

    def get_meeting_info(self, meeting_id: str) -> dict:
        """Returns basic meeting metadata."""
        return self._get(f"/meetings/{meeting_id}")
