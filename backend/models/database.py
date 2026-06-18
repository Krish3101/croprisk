from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime
from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    plots = relationship("Plot", back_populates="user", cascade="all, delete-orphan")

class Plot(Base):
    __tablename__ = "plots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    crop_type = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)  # City or region name
    growth_stage = Column(String(50), nullable=False)
    sowing_date = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="plots")
    risk_assessments = relationship("RiskAssessment", back_populates="plot", cascade="all, delete-orphan")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False)  # LOW, MODERATE, HIGH
    primary_risk = Column(String(100))
    analysis = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    weather_summary = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="risk_assessments")

def init_db():
    Base.metadata.create_all(bind=engine)
