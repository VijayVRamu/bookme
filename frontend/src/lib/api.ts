/**
 * API client — all calls go through Next.js's /api rewrite proxy,
 * which forwards to the FastAPI backend at NEXT_PUBLIC_API_URL.
 */

import type {
  AvailabilityResponse,
  BookingPayload,
  BookingResponse,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ── Availability ──────────────────────────────────────────────────────────────

/** Fetch available time slots for a given host, meeting type, and date (YYYY-MM-DD). */
export function getAvailability(
  username: string,
  slug: string,
  date: string
): Promise<AvailabilityResponse> {
  return request(`/availability/${username}/${slug}?date=${date}`);
}

// ── Bookings ──────────────────────────────────────────────────────────────────

/** Create a new booking. */
export function createBooking(payload: BookingPayload): Promise<BookingResponse> {
  return request("/bookings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Fetch a booking by its public UID. */
export function getBooking(uid: string): Promise<BookingResponse> {
  return request(`/bookings/${uid}`);
}

/** Cancel a booking by UID. */
export function cancelBooking(uid: string): Promise<{ message: string }> {
  return request(`/bookings/${uid}`, { method: "DELETE" });
}

/** List upcoming bookings for a host (used in the dashboard). */
export function getHostBookings(username: string): Promise<BookingResponse[]> {
  return request(`/bookings/host/${username}`);
}
