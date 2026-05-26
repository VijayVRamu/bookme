"""
Email service using Resend (https://resend.com).
Free tier: 3,000 emails/month. Sign up and get an API key.

To swap to SendGrid or another provider, replace the send() call below.
"""

import resend
from datetime import datetime
from config import get_settings

settings = get_settings()
resend.api_key = settings.resend_api_key


def _format_dt(dt: datetime, timezone: str) -> str:
    """Format a datetime nicely for email display."""
    return dt.strftime("%A, %B %-d, %Y at %-I:%M %p") + f" ({timezone})"


def send_confirmation_to_guest(
    guest_name: str,
    guest_email: str,
    host_name: str,
    start_time: datetime,
    end_time: datetime,
    timezone: str,
    duration_minutes: int,
    meet_link: str,
    cancel_url: str,
) -> bool:
    """Send a booking confirmation email to the guest."""
    subject = f"Confirmed: {duration_minutes}-Minute Meeting with {host_name}"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a202c">
      <h2 style="color:#0069ff">Your meeting is confirmed ✅</h2>
      <p>Hi {guest_name},</p>
      <p>Your meeting with <strong>{host_name}</strong> is booked.</p>
      <table style="background:#f7f8fa;border-radius:10px;padding:20px;width:100%;margin:20px 0">
        <tr><td style="padding:6px 0"><strong>📅 When</strong></td><td>{_format_dt(start_time, timezone)}</td></tr>
        <tr><td style="padding:6px 0"><strong>⏱ Duration</strong></td><td>{duration_minutes} minutes</td></tr>
        <tr><td style="padding:6px 0"><strong>📹 Where</strong></td><td><a href="{meet_link}">{meet_link}</a></td></tr>
      </table>
      <a href="{meet_link}" style="display:inline-block;background:#0069ff;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;margin-bottom:20px">
        Join Google Meet
      </a>
      <p style="color:#8b95a5;font-size:13px">
        Need to cancel? <a href="{cancel_url}">Cancel this booking</a>
      </p>
    </div>
    """
    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": guest_email,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[email] Failed to send guest confirmation: {e}")
        return False


def send_notification_to_host(
    host_name: str,
    host_email: str,
    guest_name: str,
    guest_email: str,
    guest_notes: str,
    start_time: datetime,
    timezone: str,
    duration_minutes: int,
    meet_link: str,
) -> bool:
    """Notify the host of a new booking."""
    subject = f"New booking: {guest_name} — {_format_dt(start_time, timezone)}"
    notes_html = f"<p><strong>Notes:</strong> {guest_notes}</p>" if guest_notes else ""
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a202c">
      <h2 style="color:#0069ff">New booking 🎉</h2>
      <p>Hi {host_name}, you have a new meeting request.</p>
      <table style="background:#f7f8fa;border-radius:10px;padding:20px;width:100%;margin:20px 0">
        <tr><td style="padding:6px 0"><strong>👤 Guest</strong></td><td>{guest_name} ({guest_email})</td></tr>
        <tr><td style="padding:6px 0"><strong>📅 When</strong></td><td>{_format_dt(start_time, timezone)}</td></tr>
        <tr><td style="padding:6px 0"><strong>⏱ Duration</strong></td><td>{duration_minutes} minutes</td></tr>
        <tr><td style="padding:6px 0"><strong>📹 Meet</strong></td><td><a href="{meet_link}">{meet_link}</a></td></tr>
      </table>
      {notes_html}
    </div>
    """
    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": host_email,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[email] Failed to send host notification: {e}")
        return False


def send_cancellation_email(
    guest_name: str,
    guest_email: str,
    host_name: str,
    start_time: datetime,
    timezone: str,
) -> bool:
    """Notify the guest that their booking was cancelled."""
    subject = f"Cancelled: Your meeting with {host_name}"
    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a202c">
      <h2>Meeting cancelled</h2>
      <p>Hi {guest_name}, your meeting with <strong>{host_name}</strong> on
      <strong>{_format_dt(start_time, timezone)}</strong> has been cancelled.</p>
      <p style="color:#8b95a5;font-size:13px">If you'd like to reschedule, visit their booking page.</p>
    </div>
    """
    try:
        resend.Emails.send({
            "from": settings.email_from,
            "to": guest_email,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        print(f"[email] Failed to send cancellation email: {e}")
        return False
