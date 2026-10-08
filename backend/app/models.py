"""SQLAlchemy models. Single-user local app, so plots have no owner."""

import datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Plot(Base):
    __tablename__ = "plots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    crop_id: Mapped[str] = mapped_column(String, nullable=False)
    stage_id: Mapped[str] = mapped_column(String, nullable=False)
    location_name: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    sowing_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    assessment: Mapped["Assessment | None"] = relationship(
        "Assessment",
        back_populates="plot",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Assessment(Base):
    __tablename__ = "assessments"
    plot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("plots.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # The inputs this row was scored with, compared against the plot to decide if it is still valid.
    location_key: Mapped[str] = mapped_column(String, nullable=False)
    stage_id: Mapped[str] = mapped_column(String, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    primary_hazard: Mapped[str] = mapped_column(String, nullable=False)
    hazard_indices: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    forecast: Mapped[str] = mapped_column(Text, nullable=False)  # JSON normalised intervals
    forecast_fetched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    advisory: Mapped[str] = mapped_column(Text, nullable=False)  # JSON Advisory
    advisory_source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    plot: Mapped["Plot"] = relationship("Plot", back_populates="assessment")
