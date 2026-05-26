"""
Google OAuth 2.0 flow for host sign-in.

Flow:
  1. GET /auth/google          → redirects user to Google consent screen
  2. GET /auth/google/callback → exchanges code for tokens, upserts User, returns JWT
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import jwt

from database import get_db
from models.user import User
from config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def _make_flow() -> Flow:
    return Flow.from_client_config(
        client_config={
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uris": [settings.google_redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
    )


def create_jwt(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


@router.get("/google")
def google_login():
    """Step 1 — redirect to Google's consent screen."""
    flow = _make_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Step 2 — exchange auth code for tokens and issue a JWT."""
    flow = _make_flow()
    flow.fetch_token(code=code)
    creds: Credentials = flow.credentials

    # Fetch Google profile
    people_service = build("oauth2", "v2", credentials=creds)
    profile = people_service.userinfo().get().execute()

    email = profile["email"]
    name = profile.get("name", email.split("@")[0])
    picture = profile.get("picture")

    # Upsert user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        username = email.split("@")[0].lower().replace(".", "")
        user = User(email=email, name=name, username=username, avatar_url=picture)
        db.add(user)

    user.google_access_token = creds.token
    user.google_refresh_token = creds.refresh_token or user.google_refresh_token
    user.google_token_expiry = creds.expiry
    user.avatar_url = picture
    db.commit()
    db.refresh(user)

    token = create_jwt(user.id)

    # Redirect to frontend dashboard with token
    return RedirectResponse(f"{settings.app_url}/dashboard?token={token}")


@router.get("/me")
def get_me(token: str, db: Session = Depends(get_db)):
    """Validate a JWT and return the current user's profile."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "username": user.username,
        "title": user.title,
        "avatar_url": user.avatar_url,
        "timezone": user.timezone,
    }
