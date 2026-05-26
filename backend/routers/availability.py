"""
Availability router — returns open time slots for a given host + date range.

GET /availability/{username}/{meeting_type_slug}?date=2026-06-10
  → Returns a list of available 30-min slots for that day, excluding Google Calendar busy times.
"""

from datetime import datetime, timedelta, date as Date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from database import get_db
from models.user import User
from models.booking import MeetingType, Booking
from services.google_calendar import get_busy_times

router = APIRouter(prefix="/availability", tags=["availability"])


def _slots_for_day(
    target_date: Date,
    windows: list[dict],
    duration: int,
    timezone: str,
) -> list[datetime]:
    """
    Generate candidate slot start times for a given day based on
    the host's availability windows.
    """
    tz = ZoneInfo(timezone)
    weekday = target_date.weekday() + 1  # Mon=1 … Sun=0 (matches JS convention)
    # Remap Sunday
    if target_date.isoweekday() == 7:
        weekday = 0

    slots = []
    for window in windows:
        if window.get("day") != weekday:
            continue
        start_h, start_m = map(int, window["start"].split(":"))
        end_h, end_m = map(int, window["end"].split(":"))

        cursor = datetime(target_date.year, target_date.month, target_date.day,
                          start_h, start_m, tzinfo=tz)
        end_dt = datetime(target_date.year, target_date.month, target_date.day,
                          end_h, end_m, tzinfo=tz)

        while cursor + timedelta(minutes=duration) <= end_dt:
            slots.append(cursor)
            cursor += timedelta(minutes=duration)

    return slots


@router.get("/{username}/{slug}")
def get_availability(
    username: str,
    slug: str,
    date: str = Query(..., description="ISO date: YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """Return available slots for a specific day."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    meeting_type = (
        db.query(MeetingType)
        .filter(MeetingType.host_id == user.id, MeetingType.slug == slug, MeetingType.is_active == True)
        .first()
    )
    if not meeting_type:
        raise HTTPException(status_code=404, detail="Meeting type not found")

    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")

    tz = ZoneInfo(user.timezone)
    day_start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, tzinfo=tz)
    day_end = day_start + timedelta(days=1)

    # Generate candidate slots from availability windows
    candidates = _slots_for_day(
        target_date,
        meeting_type.availability_windows or _default_windows(),
        meeting_type.duration_minutes,
        user.timezone,
    )

    if not candidates:
        return {"slots": [], "timezone": user.timezone}

    # Fetch Google Calendar busy blocks
    busy_blocks = []
    if user.google_access_token and user.google_refresh_token:
        try:
            busy_blocks = get_busy_times(
                user.google_access_token,
                user.google_refresh_token,
                day_start.replace(tzinfo=None),
                day_end.replace(tzinfo=None),
                user.timezone,
            )
        except Exception as e:
            print(f"[availability] Google Calendar error: {e}")

    # Also block already-confirmed bookings in the DB
    db_bookings = (
        db.query(Booking)
        .filter(
            Booking.host_id == user.id,
            Booking.start_time >= day_start.replace(tzinfo=None),
            Booking.start_time < day_end.replace(tzinfo=None),
            Booking.status == "confirmed",
        )
        .all()
    )
    for b in db_bookings:
        busy_blocks.append({"start": b.start_time, "end": b.end_time})

    # Filter out busy slots
    duration = timedelta(minutes=meeting_type.duration_minutes)
    available = []
    for slot in candidates:
        slot_end = slot + duration
        slot_naive = slot.replace(tzinfo=None)
        slot_end_naive = slot_end.replace(tzinfo=None)

        is_busy = any(
            slot_naive < block["end"] and slot_end_naive > block["start"]
            for block in busy_blocks
        )
        if not is_busy:
            available.append(slot.isoformat())

    return {"slots": available, "timezone": user.timezone}


def _default_windows() -> list[dict]:
    """Mon–Fri 9am–5pm default if host hasn't configured custom hours."""
    return [
        {"day": d, "start": "09:00", "end": "17:00"}
        for d in range(1, 6)  # Monday=1 to Friday=5
    ]
