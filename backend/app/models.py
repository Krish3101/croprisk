"""SQLAlchemy ORM models."""

import datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    plots: Mapped[list["Plot"]] = relationship(
        "Plot",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Plot(Base):
    __tablename__ = "plots"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_plots_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_plots_longitude"),
        Index("ix_plots_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    crop_id: Mapped[str] = mapped_column(String, nullable=False)
    stage_id: Mapped[str] = mapped_column(String, nullable=False)
    location_name: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    sowing_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="plots")
    risk_assessment: Mapped["RiskAssessment | None"] = relationship(
        "RiskAssessment",
        back_populates="plot",
        cascade="all, delete-orphan",
        uselist=False,
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        CheckConstraint("score BETWEEN 0 AND 100", name="chk_risk_score"),
        CheckConstraint(
            "severity IN ('LOW', 'MODERATE', 'HIGH')",
            name="chk_risk_severity",
        ),
        CheckConstraint(
            "advisory_source IN ('bypass', 'llm', 'fallback')",
            name="chk_risk_advisory_source",
        ),
    )

    plot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    primary_threat: Mapped[str] = mapped_column(String, nullable=False)
    hazard_indices: Mapped[str] = mapped_column(Text, nullable=False)  # JSON {heat,frost,precip,disease,wind}
    forecast: Mapped[str] = mapped_column(Text, nullable=False)        # JSON normalised intervals
    advisory: Mapped[str] = mapped_column(Text, nullable=False)        # JSON Advisory
    advisory_source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    plot: Mapped["Plot"] = relationship("Plot", back_populates="risk_assessment")
