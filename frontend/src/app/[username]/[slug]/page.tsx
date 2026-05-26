"use client";

/**
 * Public booking page — /[username]/[slug]
 * e.g. /vijay/30min
 *
 * This is the page your guests visit to book a meeting with you.
 * It mirrors the interactive prototype we built, now wired to the real API.
 */

import { useState, useCallback } from "react";
import { format, addMonths, subMonths, startOfMonth, endOfMonth,
         eachDayOfInterval, isSameMonth, isSameDay, isBefore,
         startOfDay, parseISO } from "date-fns";
import { getAvailability, createBooking } from "@/lib/api";
import type { BookingResponse } from "@/lib/types";

interface Props {
  params: { username: string; slug: string };
}

type Step = "pick" | "form" | "confirmed";

export default function BookingPage({ params }: Props) {
  const { username, slug } = params;

  const [step, setStep] = useState<Step>("pick");
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [slots, setSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [confirmation, setConfirmation] = useState<BookingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [fname, setFname] = useState("");
  const [lname, setLname] = useState("");
  const [email, setEmail] = useState("");
  const [notes, setNotes] = useState("");

  // Calendar helpers
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const calDays = eachDayOfInterval({ start: monthStart, end: monthEnd });
  const today = startOfDay(new Date());

  const handleDateClick = useCallback(async (date: Date) => {
    setSelectedDate(date);
    setSelectedSlot(null);
    setLoadingSlots(true);
    setError(null);
    try {
      const dateStr = format(date, "yyyy-MM-dd");
      const res = await getAvailability(username, slug, dateStr);
      setSlots(res.slots);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Could not load slots");
      setSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  }, [username, slug]);

  const handleSlotClick = (slot: string) => {
    setSelectedSlot(slot);
    setTimeout(() => setStep("form"), 200);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) return;
    setSubmitting(true);
    setError(null);
    try {
      const booking = await createBooking({
        username,
        meeting_type_slug: slug,
        start_time: selectedSlot,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        guest_name: `${fname} ${lname}`.trim(),
        guest_email: email,
        guest_notes: notes,
      });
      setConfirmation(booking);
      setStep("confirmed");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Booking failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-3xl overflow-hidden flex flex-col md:flex-row">

        {/* ── Sidebar ── */}
        <div className="md:w-64 bg-white border-b md:border-b-0 md:border-r border-gray-100 p-8 flex flex-col gap-5">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
              {username[0].toUpperCase()}
            </div>
            <div>
              <div className="font-bold text-gray-900 capitalize">{username}</div>
              <div className="text-xs text-gray-400">Host</div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4 space-y-2">
            <div className="font-bold text-blue-600 capitalize">{slug.replace(/-/g, " ")} meeting</div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>🕐</span> 30 minutes
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>📹</span> Google Meet
            </div>
          </div>

          <div className="text-xs text-gray-400 flex items-center gap-1">
            <span>📅</span> Google Calendar connected
          </div>
        </div>

        {/* ── Main ── */}
        <div className="flex-1 p-8">

          {/* Step: Pick date/time */}
          {step === "pick" && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-bold">Select a date &amp; time</h2>
                <p className="text-sm text-gray-400 mt-1">Available slots from Google Calendar</p>
              </div>

              <div className="flex flex-col md:flex-row gap-6">
                {/* Calendar */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-4">
                    <button onClick={() => setCurrentMonth(m => subMonths(m, 1))}
                      className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center hover:bg-blue-50 hover:border-blue-300 transition-colors text-gray-600">
                      ‹
                    </button>
                    <span className="font-semibold text-sm">{format(currentMonth, "MMMM yyyy")}</span>
                    <button onClick={() => setCurrentMonth(m => addMonths(m, 1))}
                      className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center hover:bg-blue-50 hover:border-blue-300 transition-colors text-gray-600">
                      ›
                    </button>
                  </div>

                  <div className="grid grid-cols-7 gap-1 text-center">
                    {["Su","Mo","Tu","We","Th","Fr","Sa"].map(d => (
                      <div key={d} className="text-xs font-semibold text-gray-400 py-1">{d}</div>
                    ))}
                    {/* Empty cells for first week */}
                    {Array.from({ length: monthStart.getDay() }).map((_, i) => (
                      <div key={`e-${i}`} />
                    ))}
                    {calDays.map(day => {
                      const isPast = isBefore(startOfDay(day), today);
                      const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                      const isDisabled = isPast || isWeekend;
                      const isSelected = selectedDate && isSameDay(day, selectedDate);
                      const isToday = isSameDay(day, today);

                      return (
                        <button key={day.toISOString()}
                          disabled={isDisabled}
                          onClick={() => !isDisabled && handleDateClick(day)}
                          className={[
                            "aspect-square rounded-full text-sm font-medium transition-all",
                            isDisabled ? "text-gray-200 cursor-default" : "cursor-pointer hover:bg-blue-50 hover:text-blue-600",
                            isSelected ? "!bg-blue-600 !text-white font-bold" : "",
                            isToday && !isSelected ? "border-2 border-blue-500 text-blue-600 font-bold" : "",
                            !isDisabled && !isSelected && !isToday ? "text-gray-800 font-semibold" : "",
                          ].join(" ")}
                        >
                          {format(day, "d")}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Time slots */}
                <div className="w-full md:w-44">
                  {selectedDate ? (
                    <>
                      <div className="text-sm font-bold text-blue-600 mb-3">
                        {format(selectedDate, "EEE, MMM d")}
                      </div>
                      {loadingSlots ? (
                        <div className="text-sm text-gray-400 animate-pulse">Loading slots…</div>
                      ) : slots.length === 0 ? (
                        <div className="text-sm text-gray-400">No slots available</div>
                      ) : (
                        <div className="flex flex-col gap-2 max-h-72 overflow-y-auto pr-1">
                          {slots.map(slot => (
                            <button key={slot}
                              onClick={() => handleSlotClick(slot)}
                              className={[
                                "border-2 rounded-xl py-2.5 text-sm font-semibold transition-all",
                                selectedSlot === slot
                                  ? "bg-blue-600 border-blue-600 text-white"
                                  : "border-blue-500 text-blue-600 hover:bg-blue-50",
                              ].join(" ")}
                            >
                              {format(parseISO(slot), "h:mm a")}
                            </button>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-sm text-gray-400 mt-4">← Pick a date</div>
                  )}
                </div>
              </div>

              {error && <p className="text-sm text-red-500">{error}</p>}
            </div>
          )}

          {/* Step: Booking form */}
          {step === "form" && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-bold">Enter your details</h2>
                <p className="text-sm text-gray-400 mt-1">A confirmation will be sent to your email</p>
              </div>

              {/* Selected slot badge */}
              <div className="flex items-center gap-3 bg-blue-50 rounded-xl p-3">
                <span>📅</span>
                <span className="text-sm font-semibold text-blue-700">
                  {selectedDate && format(selectedDate, "EEEE, MMMM d")} at{" "}
                  {selectedSlot && format(parseISO(selectedSlot), "h:mm a")}
                </span>
                <button onClick={() => setStep("pick")}
                  className="ml-auto text-xs text-blue-500 underline">
                  Change
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex-1 space-y-1">
                    <label className="text-sm font-semibold text-gray-700">First name *</label>
                    <input required value={fname} onChange={e => setFname(e.target.value)}
                      placeholder="Jane"
                      className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
                  </div>
                  <div className="flex-1 space-y-1">
                    <label className="text-sm font-semibold text-gray-700">Last name *</label>
                    <input required value={lname} onChange={e => setLname(e.target.value)}
                      placeholder="Smith"
                      className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-semibold text-gray-700">Email *</label>
                  <input required type="email" value={email} onChange={e => setEmail(e.target.value)}
                    placeholder="jane@company.com"
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-semibold text-gray-700">
                    Agenda <span className="text-gray-400 font-normal">(optional)</span>
                  </label>
                  <textarea value={notes} onChange={e => setNotes(e.target.value)}
                    rows={3} placeholder="What would you like to discuss?"
                    className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" />
                </div>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <div className="flex gap-3 pt-2">
                  <button type="button" onClick={() => setStep("pick")}
                    className="px-5 py-3 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-gray-50 transition-colors">
                    ← Back
                  </button>
                  <button type="submit" disabled={submitting}
                    className="flex-1 py-3 rounded-xl bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 transition-colors disabled:opacity-60">
                    {submitting ? "Booking…" : "Confirm booking →"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Step: Confirmation */}
          {step === "confirmed" && confirmation && (
            <div className="flex flex-col items-center text-center gap-6 py-4">
              <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center text-4xl animate-bounce">
                ✅
              </div>
              <div>
                <h2 className="text-2xl font-extrabold">You&apos;re confirmed!</h2>
                <p className="text-gray-400 mt-1 text-sm">
                  A calendar invite + Google Meet link have been sent to{" "}
                  <strong>{confirmation.guest_email}</strong>
                </p>
              </div>

              <div className="bg-gray-50 rounded-xl p-5 w-full max-w-sm text-left space-y-3">
                <div className="flex items-start gap-3">
                  <span>👤</span>
                  <div>
                    <div className="font-semibold">{confirmation.guest_name}</div>
                    <div className="text-xs text-gray-400">with {confirmation.host_name}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <span>📅</span>
                  <div>
                    <div className="font-semibold">
                      {format(parseISO(confirmation.start_time), "EEEE, MMMM d, yyyy")}
                    </div>
                    <div className="text-xs text-gray-400">
                      {format(parseISO(confirmation.start_time), "h:mm a")} · 30 min · Google Meet
                    </div>
                  </div>
                </div>
              </div>

              {confirmation.meet_link && (
                <a href={confirmation.meet_link} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-3 bg-white border-2 border-green-400 rounded-xl px-5 py-3 w-full max-w-sm hover:bg-green-50 transition-colors">
                  <span className="text-xl">📹</span>
                  <div className="text-left">
                    <div className="text-green-600 font-semibold text-sm">Join Google Meet</div>
                    <div className="text-gray-400 text-xs font-mono truncate">{confirmation.meet_link}</div>
                  </div>
                </a>
              )}

              <button onClick={() => {
                setStep("pick"); setSelectedDate(null); setSelectedSlot(null);
                setSlots([]); setFname(""); setLname(""); setEmail(""); setNotes("");
              }}
                className="text-sm text-gray-400 hover:text-blue-600 transition-colors underline">
                Book another time
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
