"""Database Models and Setup
SQLAlchemy ORM models for KisanAI
"""

import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database setup
from config import DATA_DIR

# Database setup
db_path = DATA_DIR / "kisanai.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")

# Connection pooling configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,  # Set to True for SQL debugging
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency for getting DB session
def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Models
class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    plot = Column(String(100), nullable=False)
    sown_date = Column(String(20))
    stage = Column(String(50), default="Sown")
    expected_harvest = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    expenses = relationship("Expense", back_populates="crop")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(20), nullable=False, index=True)  # income or expense
    category = Column(String(100))
    date = Column(String(20), nullable=False, index=True)
    description = Column(Text)
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    crop = relationship("Crop", back_populates="expenses")


class SoilReport(Base):
    __tablename__ = "soil_reports"

    id = Column(Integer, primary_key=True, index=True)
    field = Column(String(100), nullable=False, index=True)
    ph = Column(Float, nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    moisture = Column(Float)
    organic_matter = Column(Float)
    last_tested = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, unique=True, index=True)
    temperature = Column(Float)
    condition = Column(String(100))
    humidity = Column(Float)
    wind_speed = Column(Float)
    cached_at = Column(DateTime, default=datetime.utcnow, index=True)


class WeatherForecastCache(Base):
    __tablename__ = "weather_forecast_cache"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100), nullable=False, index=True)
    date = Column(String(20), nullable=False)  # YYYY-MM-DD format
    temperature = Column(Float)
    temp_min = Column(Float)
    temp_max = Column(Float)
    condition = Column(String(100))
    humidity = Column(Float)
    cached_at = Column(DateTime, default=datetime.utcnow, index=True)


class PriceCache(Base):
    __tablename__ = "price_cache"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    modal_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)
    unit = Column(String(50))
    cached_at = Column(DateTime, default=datetime.utcnow, index=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(200))
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create all tables
def init_db() -> None:
    """Initialize database and create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
