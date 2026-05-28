"""
Bookings router — create, retrieve, and cancel bookings.

POST /bookings                    → create a new booking
GET  /bookings/{uid}              → get booking by public UID
DELETE /bookings/{uid}            → cancel a booking
GET  /bookings/host/{username}    → list all bookings for a host (auth required)
"""

import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.booking import Booking, MeetingType
from services.google_calendar import create_event, delete_event
from services.email import send_confirmation_to_guest, send_notification_to_host, send_cancellation_email
from config import get_settings

router = APIRouter(prefix="/bookings", tags=["bookings"])
settings = get_settings()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    username: str           # host's username
    meeting_type_slug: str
    start_time: datetime    # ISO 8601, e.g. "2026-06-10T10:00:00"
    timezone: str           # IANA timezone, e.g. "America/Los_Angeles"
    guest_name: str
    guest_email: EmailStr
    guest_notes: str = ""


class BookingResponse(BaseModel):
    uid: str
    guest_name: str
    guest_email: str
    host_name: str
    meeting_type_name: str
    start_time: datetime
    end_time: datetime
    timezone: str
    meet_link: str 
    status: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=BookingResponse, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    """Create a booking, add it to Google Calendar, and send emails."""

    # 1. Resolve host + meeting type
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Host not found")

    meeting_type = (
        db.query(MeetingType)
        .filter(
            MeetingType.host_id == user.id,
            MeetingType.slug == payload.meeting_type_slug,
            MeetingType.is_active == True,
        )
        .first()
    )
    if not meeting_type:
        raise HTTPException(status_code=404, detail="Meeting type not found")

    # 2. Check for double-booking
    end_time = payload.start_time + timedelta(minutes=meeting_type.duration_minutes)
    conflict = (
        db.query(Booking)
        .filter(
            Booking.host_id == user.id,
            Booking.status == "confirmed",
            Booking.start_time < end_time,
            Booking.end_time > payload.start_time,
        )
        .first()
    )
    if conflict:
        raise HTTPException(status_code=409, detail="This slot is no longer available")

    # 3. Create Google Calendar event
    google_event_id = None
    meet_link = None
    if user.google_access_token and user.google_refresh_token:
        try:
            event = create_event(
                access_token=user.google_access_token,
                refresh_token=user.google_refresh_token,
                summary=f"{meeting_type.name} with {payload.guest_name}",
                description=payload.guest_notes or "",
                start=payload.start_time,
                end=end_time,
                attendee_email=payload.guest_email,
                timezone=payload.timezone,
                add_meet_link=True,
            )
            google_event_id = event.get("id")
            meet_link = event.get("hangoutLink")
        except Exception as e:
            print(f"[bookings] Google Calendar error: {e}")
            # Don't block the booking if Calendar fails

    # 4. Persist booking
    booking = Booking(
        uid=str(uuid.uuid4()),
        host_id=user.id,
        meeting_type_id=meeting_type.id,
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        guest_notes=payload.guest_notes,
        start_time=payload.start_time,
        end_time=end_time,
        timezone=payload.timezone,
        google_event_id=google_event_id,
        meet_link=meet_link,
        status="confirmed",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # 5. Send emails
    cancel_url = f"{settings.app_url}/cancel/{booking.uid}"
    send_confirmation_to_guest(
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        host_name=user.name,
        start_time=payload.start_time,
        end_time=end_time,
        timezone=payload.timezone,
        duration_minutes=meeting_type.duration_minutes,
        meet_link=meet_link or "",
        cancel_url=cancel_url,
    )
    send_notification_to_host(
        host_name=user.name,
        host_email=user.email,
        guest_name=payload.guest_name,
        guest_email=payload.guest_email,
        guest_notes=payload.guest_notes,
        start_time=payload.start_time,
        timezone=payload.timezone,
        duration_minutes=meeting_type.duration_minutes,
        meet_link=meet_link or "",
    )

    return BookingResponse(
        uid=booking.uid,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        host_name=user.name,
        meeting_type_name=meeting_type.name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        timezone=booking.timezone,
        meet_link=booking.meet_link,
        status=booking.status,
    )


@router.get("/{uid}", response_model=BookingResponse)
def get_booking(uid: str, db: Session = Depends(get_db)):
    """Fetch a booking by its public UID (used on confirmation + cancel pages)."""
    booking = db.query(Booking).filter(Booking.uid == uid).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return BookingResponse(
        uid=booking.uid,
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        host_name=booking.host.name,
        meeting_type_name=booking.meeting_type.name,
        start_time=booking.start_time,
        end_time=booking.end_time,
        timezone=booking.timezone,
        meet_link=booking.meet_link,
        status=booking.status,
    )


@router.delete("/{uid}", status_code=200)
def cancel_booking(uid: str, db: Session = Depends(get_db)):
    """Cancel a booking and remove the Google Calendar event."""
    booking = db.query(Booking).filter(Booking.uid == uid).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == "cancelled":
        raise HTTPException(status_code=400, detail="Already cancelled")

    host = booking.host

    # Remove from Google Calendar
    if booking.google_event_id and host.google_access_token and host.google_refresh_token:
        delete_event(host.google_access_token, host.google_refresh_token, booking.google_event_id)

    booking.status = "cancelled"
    db.commit()

    send_cancellation_email(
        guest_name=booking.guest_name,
        guest_email=booking.guest_email,
        host_name=host.name,
        start_time=booking.start_time,
        timezone=booking.timezone,
    )

    return {"message": "Booking cancelled"}


@router.get("/host/{username}")
def list_host_bookings(username: str, db: Session = Depends(get_db)):
    """List upcoming bookings for a host (add JWT auth middleware in production)."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Host not found")

    bookings = (
        db.query(Booking)
        .filter(Booking.host_id == user.id, Booking.start_time >= datetime.utcnow())
        .order_by(Booking.start_time)
        .all()
    )
    return [
        {
            "uid": b.uid,
            "guest_name": b.guest_name,
            "guest_email": b.guest_email,
            "start_time": b.start_time.isoformat(),
            "end_time": b.end_time.isoformat(),
            "meet_link": b.meet_link,
            "status": b.status,
        }
        for b in bookings
    ]
