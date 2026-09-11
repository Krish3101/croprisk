"""FastAPI dependencies for authentication and database sessions."""

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import UnauthorizedError
from app.models import User
from app.security import COOKIE_NAME, verify_session_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise UnauthorizedError()

    user_id = verify_session_token(token)
    if user_id is None:
        raise UnauthorizedError()

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError()

    return user
