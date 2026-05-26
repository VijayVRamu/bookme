# BookMe — Calendly-style scheduling app

**Stack:** Next.js 14 (frontend) · FastAPI (backend) · SQLite/PostgreSQL · Google Calendar API · Resend email

---

## Project structure

```
bookme/
├── frontend/          # Next.js 14 App Router
│   └── src/
│       ├── app/
│       │   ├── page.tsx                    # Landing / sign-in
│       │   ├── [username]/[slug]/page.tsx  # Public booking page
│       │   └── dashboard/page.tsx          # Host dashboard
│       ├── lib/
│       │   ├── api.ts                      # API client
│       │   └── types.ts                    # Shared TypeScript types
│       └── app/globals.css
├── backend/           # FastAPI
│   ├── main.py                 # Entry point
│   ├── config.py               # Settings (reads .env)
│   ├── database.py             # SQLAlchemy setup
│   ├── models/
│   │   ├── user.py             # User / host model
│   │   └── booking.py         # Booking + MeetingType models
│   ├── routers/
│   │   ├── auth.py             # Google OAuth flow
│   │   ├── availability.py    # Free slot calculation
│   │   └── bookings.py        # Create / cancel bookings
│   └── services/
│       ├── google_calendar.py  # Calendar API integration
│       └── email.py            # Resend email service
├── vercel.json         # Vercel deployment config
└── .gitignore
```

---

## Quick start (local dev)

### 1. Clone & set up environment

```bash
git clone https://github.com/VijayVRamu/bookme.git
cd bookme
```

### 2. Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in your Google OAuth credentials and Resend API key

uvicorn main:app --reload --port 8000
# API docs → http://localhost:8000/docs
```

### 3. Frontend

```bash
cd frontend
npm install

cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

npm run dev
# App → http://localhost:3000
```
