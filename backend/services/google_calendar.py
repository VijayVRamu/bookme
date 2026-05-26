"""
Google Calendar service — reads busy times and creates/deletes events.

To use:
1. Enable the Google Calendar API in Google Cloud Console
2. Create OAuth 2.0 credentials (Web application)
3. Add the scopes below to your OAuth consent screen
4. Store access/refresh tokens in the User model after OAuth flow
"""

from datetime import datetime, timedelta
from typing import Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import get_settings

settings = get_settings()

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _build_service(access_token: str, refresh_token: str):
    """Build an authenticated Google Calendar client."""
    creds = Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=creds)


def get_busy_times(
    access_token: str,
    refresh_token: str,
    start: datetime,
    end: datetime,
    timezone: str = "UTC",
) -> list[dict]:
    """
    Return a list of busy intervals from the user's primary calendar.
    Each item: {"start": datetime, "end": datetime}
    """
    service = _build_service(access_token, refresh_token)
    body = {
        "timeMin": start.isoformat() + "Z",
        "timeMax": end.isoformat() + "Z",
        "timeZone": timezone,
        "items": [{"id": "primary"}],
    }
    result = service.freebusy().query(body=body).execute()
    busy_raw = result.get("calendars", {}).get("primary", {}).get("busy", [])
    return [
        {
            "start": datetime.fromisoformat(b["start"].replace("Z", "")),
            "end": datetime.fromisoformat(b["end"].replace("Z", "")),
        }
        for b in busy_raw
    ]


def create_event(
    access_token: str,
    refresh_token: str,
    summary: str,
    description: str,
    start: datetime,
    end: datetime,
    attendee_email: str,
    timezone: str = "UTC",
    add_meet_link: bool = True,
) -> dict:
    """
    Create a Google Calendar event and optionally attach a Meet link.
    Returns the created event dict (includes hangoutLink if Meet was added).
    """
    service = _build_service(access_token, refresh_token)

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": end.isoformat(), "timeZone": timezone},
        "attendees": [{"email": attendee_email}],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    if add_meet_link:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": f"bookme-{int(start.timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }

    event = service.events().insert(
        calendarId="primary",
        body=event_body,
        conferenceDataVersion=1 if add_meet_link else 0,
        sendUpdates="all",  # sends Google invites to attendees
    ).execute()

    return event


def delete_event(access_token: str, refresh_token: str, event_id: str) -> bool:
    """Cancel a calendar event by ID."""
    try:
        service = _build_service(access_token, refresh_token)
        service.events().delete(calendarId="primary", eventId=event_id, sendUpdates="all").execute()
        return True
    except HttpError:
        return False
