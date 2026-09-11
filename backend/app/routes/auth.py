"""Authentication routes: register, login, logout, and me."""

import datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import EmailTakenError, InvalidCredentialsError
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, UserResponse
from app.security import (
    COOKIE_NAME,
    SESSION_MAX_AGE,
    create_session_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    existing = db.query(User).filter(User.email.ilike(req.email)).first()
    if existing:
        raise EmailTakenError()

    now_iso = datetime.datetime.now(datetime.UTC).isoformat()
    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        created_at=now_iso,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(id=user.id, email=user.email)


@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserResponse)
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)) -> UserResponse:
    user = db.query(User).filter(User.email.ilike(req.email)).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise InvalidCredentialsError()

    token = create_session_token(user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )
    return UserResponse(id=user.id, email=user.email)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email)
