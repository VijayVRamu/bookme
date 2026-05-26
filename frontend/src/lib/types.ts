// ── Shared TypeScript types ───────────────────────────────────────────────────

export interface Host {
  id: number;
  name: string;
  email: string;
  username: string;
  title?: string;
  avatar_url?: string;
  timezone: string;
}

export interface MeetingType {
  id: number;
  slug: string;
  name: string;
  duration_minutes: number;
  description?: string;
  location: "google_meet" | "zoom" | "phone" | "in_person";
  color: string;
}

export interface AvailabilityResponse {
  slots: string[];   // ISO 8601 datetime strings
  timezone: string;
}

export interface BookingPayload {
  username: string;
  meeting_type_slug: string;
  start_time: string;  // ISO 8601
  timezone: string;
  guest_name: string;
  guest_email: string;
  guest_notes?: string;
}

export interface BookingResponse {
  uid: string;
  guest_name: string;
  guest_email: string;
  host_name: string;
  meeting_type_name: string;
  start_time: string;
  end_time: string;
  timezone: string;
  meet_link?: string;
  status: "confirmed" | "cancelled" | "rescheduled";
}
