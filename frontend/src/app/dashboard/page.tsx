"use client";

/**
 * Host dashboard — shows upcoming bookings after Google OAuth sign-in.
 * The JWT is passed as a query param by the FastAPI callback redirect.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { format, parseISO } from "date-fns";
import { getHostBookings } from "@/lib/api";
import type { BookingResponse } from "@/lib/types";

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [bookings, setBookings] = useState<BookingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // TODO: decode JWT to get username, or store in localStorage
  // For now we use a placeholder username from localStorage
  const username =
    typeof window !== "undefined" ? localStorage.getItem("bm_username") ?? "vijay" : "vijay";

  useEffect(() => {
    if (token && typeof window !== "undefined") {
      localStorage.setItem("bm_token", token);
    }
  }, [token]);

  useEffect(() => {
    getHostBookings(username)
      .then(setBookings)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [username]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold">Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">Your upcoming meetings</p>
          </div>
          <a
            href={`/${username}/30min`}
            target="_blank"
            className="text-sm text-blue-600 border border-blue-200 bg-blue-50 px-4 py-2 rounded-xl font-semibold hover:bg-blue-100 transition-colors"
          >
            View booking page ↗
          </a>
        </div>

        {/* Booking list */}
        {loading && (
          <div className="text-gray-400 text-sm animate-pulse">Loading bookings…</div>
        )}

        {error && (
          <div className="bg-red-50 text-red-600 rounded-xl p-4 text-sm">{error}</div>
        )}

        {!loading && bookings.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-100 p-12 text-center text-gray-400">
            <div className="text-4xl mb-3">📭</div>
            <p className="font-semibold">No upcoming bookings</p>
            <p className="text-sm mt-1">Share your booking page to get started.</p>
          </div>
        )}

        {bookings.map(b => (
          <div key={b.uid}
            className="bg-white rounded-xl border border-gray-100 p-5 flex items-start gap-4 shadow-sm hover:shadow-md transition-shadow">
            {/* Date bubble */}
            <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-blue-50 flex flex-col items-center justify-center">
              <span className="text-xs font-bold text-blue-400 uppercase">
                {format(parseISO(b.start_time), "MMM")}
              </span>
              <span className="text-xl font-extrabold text-blue-600 leading-none">
                {format(parseISO(b.start_time), "d")}
              </span>
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="font-bold text-gray-900">{b.guest_name}</div>
              <div className="text-sm text-gray-400">{b.guest_email}</div>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                <span>🕐 {format(parseISO(b.start_time), "h:mm a")}</span>
                <span>· 30 min</span>
              </div>
            </div>

            {/* Meet link */}
            {b.meet_link && (
              <a href={b.meet_link} target="_blank" rel="noopener noreferrer"
                className="flex-shrink-0 text-sm font-semibold text-green-600 border border-green-200 bg-green-50 px-3 py-2 rounded-xl hover:bg-green-100 transition-colors">
                📹 Join
              </a>
            )}

            {/* Status badge */}
            <span className={[
              "flex-shrink-0 text-xs font-bold px-2.5 py-1 rounded-full",
              b.status === "confirmed" ? "bg-green-50 text-green-600" : "bg-gray-100 text-gray-400",
            ].join(" ")}>
              {b.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
