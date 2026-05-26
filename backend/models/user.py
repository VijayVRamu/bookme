from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    """A host who owns a booking page."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)  # e.g. "vijay" → /vijay
    title = Column(String, nullable=True)       # e.g. "Product Manager"
    bio = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    timezone = Column(String, default="America/Los_Angeles")

    # Google OAuth tokens (stored encrypted in production)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)

    # Settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meeting_types = relationship("MeetingType", back_populates="host", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="host", cascade="all, delete-orphan")
