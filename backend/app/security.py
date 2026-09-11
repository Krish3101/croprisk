"""Password hashing with bcrypt and session JWT handling with pyjwt."""

import datetime

import bcrypt
import jwt

from app.config import settings

COOKIE_NAME = "croprisk_session"
SESSION_MAX_AGE = 24 * 3600  # 24 hours


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_session_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(seconds=SESSION_MAX_AGE),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_session_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        sub = payload.get("sub")
        if sub is None:
            return None
        return int(sub)
    except (jwt.PyJWTError, ValueError):
        return None
