"""Authentication API Routes
User login and registration endpoints
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import get_logger
from models.database import User as DBUser
from models.database import get_db
from models.schemas import Token, User, UserRegister
from utils.helpers import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user with comprehensive validation and error handling"""
    try:
        # Check if username exists
        existing_username = db.query(DBUser).filter(DBUser.username == user_data.username).first()
        if existing_username:
            logger.warning(f"Registration failed: username '{user_data.username}' already exists")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

        # Check if email exists
        existing_email = db.query(DBUser).filter(DBUser.email == user_data.email).first()
        if existing_email:
            logger.warning(f"Registration failed: email '{user_data.email}' already exists")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = DBUser(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"New user registered successfully: {user_data.username}")
        return {"status": "success", "message": "User registered successfully", "username": new_user.username}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed with unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed due to server error"
        )


@router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


@router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """Logout endpoint
    Note: With JWT, actual logout is handled client-side by removing token
    """
    logger.info(f"User logged out: {current_user.username}")
    return {"status": "success", "message": "Logged out successfully"}
