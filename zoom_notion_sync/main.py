"""
Zoom → Google Calendar → Notion Sync
=====================================
Fetches scheduled Zoom meetings from Google Calendar,
saves them to Notion, and after each call collects
transcript, recording link, attendees, duration, and meeting info.

Run:
    python main.py --sync       # Sync upcoming Zoom meetings to Notion
    python main.py --post-call  # Process completed calls (recordings, transcripts)
    python main.py --all        # Do both
"""

import argparse
import logging
from datetime import datetime

from services.calendar_service import GoogleCalendarService
from services.zoom_service import ZoomService
from services.notion_service import NotionService
from utils.logger import setup_logger

logger = setup_logger(__name__)


def sync_upcoming_meetings():
    """Pull Zoom meetings from Google Calendar → save to Notion."""
    logger.info("=== Syncing upcoming Zoom meetings ===")

    calendar = GoogleCalendarService()
    notion = NotionService()

    meetings = calendar.get_zoom_meetings()
    logger.info(f"Found {len(meetings)} upcoming Zoom meetings in Google Calendar")

    synced = 0
    for meeting in meetings:
        try:
            existing = notion.find_meeting_by_zoom_id(meeting["zoom_meeting_id"])
            if existing:
                notion.update_meeting(existing["id"], meeting)
                logger.info(f"Updated: {meeting['title']}")
            else:
                notion.create_meeting(meeting)
                logger.info(f"Created: {meeting['title']}")
            synced += 1
        except Exception as e:
            logger.error(f"Failed to sync meeting '{meeting.get('title')}': {e}")

    logger.info(f"=== Synced {synced}/{len(meetings)} meetings ===")


def process_completed_calls():
    """For completed Zoom calls, fetch recordings + transcripts → update Notion."""
    logger.info("=== Processing completed Zoom calls ===")

    zoom = ZoomService()
    notion = NotionService()

    # Get meetings from Notion that are in the past and missing recording info
    pending = notion.get_meetings_missing_recordings()
    logger.info(f"Found {len(pending)} completed meetings to process")

    updated = 0
    for page in pending:
        zoom_id = page.get("zoom_meeting_id")
        if not zoom_id:
            continue
        try:
            recording = zoom.get_recording(zoom_id)
            if not recording:
                logger.info(f"No recording yet for meeting {zoom_id}")
                continue

            details = {
                "recording_url": recording.get("share_url", ""),
                "transcript": zoom.get_transcript(zoom_id),
                "duration_minutes": recording.get("duration", 0),
                "attendees": zoom.get_meeting_participants(zoom_id),
                "status": "Completed",
            }

            notion.update_meeting(page["notion_page_id"], details)
            logger.info(f"Updated recording info for meeting {zoom_id}")
            updated += 1
        except Exception as e:
            logger.error(f"Failed to process meeting {zoom_id}: {e}")

    logger.info(f"=== Processed {updated}/{len(pending)} completed calls ===")


def main():
    parser = argparse.ArgumentParser(description="Zoom ↔ Notion Sync Tool")
    parser.add_argument("--sync", action="store_true", help="Sync upcoming Zoom meetings from Google Calendar")
    parser.add_argument("--post-call", action="store_true", help="Process completed calls (recordings, transcripts)")
    parser.add_argument("--all", action="store_true", help="Run both sync and post-call processing")
    args = parser.parse_args()

    if args.all or (not args.sync and not args.post_call):
        sync_upcoming_meetings()
        process_completed_calls()
    elif args.sync:
        sync_upcoming_meetings()
    elif args.post_call:
        process_completed_calls()


if __name__ == "__main__":
    main()
