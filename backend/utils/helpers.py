"""Helper Functions for KisanAI
Authentication, date formatting, and utility exceptions
"""

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from models.database import get_db
from models.schemas import TokenData, User

# ==================== EXCEPTIONS ====================


class StorageError(Exception):
    """Raised when database operations fail"""

    pass


# ==================== CONFIG ====================

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY = settings.SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


# ==================== AUTHENTICATION ====================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing.
    Note: Bcrypt has a 72-byte limit. Longer passwords are truncated.
    """
    from config import get_logger

    logger = get_logger(__name__)

    # Truncate to 72 bytes for bcrypt compatibility
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        logger.warning("Password exceeds 72 bytes and will be truncated")
        password = password_bytes[:72].decode("utf-8", errors="ignore")

    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    """Get user from database"""
    from models.database import User as DBUser

    return db.query(DBUser).filter(DBUser.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user by username and password"""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception from e

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (not disabled)"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# ==================== DATE UTILITIES ====================


def format_date_display(date_str: str) -> str:
    """Format date string for display (e.g. 20 Nov 2023)"""
    if not date_str:
        return ""
    try:
        # Try parsing ISO format first
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except ValueError:
        try:
            # Try parsing YYYY-MM-DD
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except ValueError:
            return date_str


def format_date_iso(date_str: str) -> str | None:
    """Format date string to ISO format"""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.isoformat()
    except ValueError:
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.isoformat()
        except ValueError:
            return None


def get_current_date_display() -> str:
    """Get current date formatted for display"""
    return datetime.now().strftime("%d %b %Y")


def get_current_date_iso() -> str:
    """Get current date in ISO format"""
    return datetime.now().isoformat()


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%d")
