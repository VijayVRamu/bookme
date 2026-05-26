"""
BookMe — FastAPI backend entry point.

Start locally:
  uvicorn main:app --reload --port 8000

API docs (auto-generated):
  http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import create_tables
from routers import auth, availability, bookings

settings = get_settings()

app = FastAPI(
    title="BookMe API",
    description="Calendly-style appointment booking backed by Google Calendar",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(availability.router)
app.include_router(bookings.router)


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    create_tables()
    print("✅ BookMe API is running — docs at /docs")


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
