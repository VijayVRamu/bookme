from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class MeetingType(Base):
    """A bookable slot type (e.g. '30-Minute Meeting')."""
    __tablename__ = "meeting_types"

    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slug = Column(String, nullable=False)              # e.g. "30min"
    name = Column(String, nullable=False)              # e.g. "30-Minute Meeting"
    duration_minutes = Column(Integer, default=30)
    description = Column(Text, nullable=True)
    location = Column(String, default="google_meet")   # google_meet | zoom | phone | in_person
    color = Column(String, default="#0069ff")
    is_active = Column(Boolean, default=True)

    # Availability windows stored as JSON: [{"day": 1, "start": "09:00", "end": "17:00"}, ...]
    # day: 0=Sunday … 6=Saturday
    availability_windows = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)

    host = relationship("User", back_populates="meeting_types")
    bookings = relationship("Booking", back_populates="meeting_type")


class Booking(Base):
    """A confirmed appointment."""
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True, nullable=False)  # public-facing UUID
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meeting_type_id = Column(Integer, ForeignKey("meeting_types.id"), nullable=False)

    # Guest info
    guest_name = Column(String, nullable=False)
    guest_email = Column(String, nullable=False)
    guest_notes = Column(Text, nullable=True)

    # Timing
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    timezone = Column(String, nullable=False)

    # Google Calendar / Meet
    google_event_id = Column(String, nullable=True)
    meet_link = Column(String, nullable=True)

    # Status
    status = Column(String, default="confirmed")  # confirmed | cancelled | rescheduled
    cancellation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    host = relationship("User", back_populates="bookings")
    meeting_type = relationship("MeetingType", back_populates="bookings")
