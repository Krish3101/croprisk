"""Pydantic schemas for request validation and response serialization."""

import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- Auth ---
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format.")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str


# --- Crops & Stages ---
class StageSummary(BaseModel):
    id: str
    name: str
    bbch: str
    order: int


class CropSummary(BaseModel):
    id: str
    common_name: str
    scientific_name: str
    stages: list[StageSummary]


# --- Geocoding ---
class GeocodeCandidate(BaseModel):
    display_name: str
    city: str | None = None
    state: str | None = None
    country: str | None = None
    country_code: str | None = None
    latitude: float
    longitude: float


# --- Advisory ---
class Action(BaseModel):
    timeframe: Literal["immediate_24h", "preventative_72h"]
    directive: str = Field(..., min_length=15, max_length=200)


class Advisory(BaseModel):
    headline: str = Field(..., min_length=10, max_length=120)
    impact_analysis: str = Field(..., min_length=40, max_length=350)
    actions: list[Action] = Field(..., min_length=1, max_length=2)
    monitoring_focus: str = Field(..., min_length=15, max_length=150)


class AdvisoryResponse(Advisory):
    source: Literal["bypass", "llm", "fallback"]


# --- Plots ---
class PlotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    crop_id: str
    stage_id: str
    location_name: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    sowing_date: datetime.date

    @field_validator("sowing_date")
    @classmethod
    def validate_sowing_date(cls, v: datetime.date) -> datetime.date:
        today = datetime.date.today()
        if v > today:
            raise ValueError("Sowing date cannot be in the future.")
        if (today - v).days > 400:
            raise ValueError("Sowing date cannot be more than 400 days in the past.")
        return v


class PlotUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    crop_id: str | None = None
    stage_id: str | None = None
    location_name: str | None = Field(default=None, min_length=1)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    sowing_date: datetime.date | None = None

    @field_validator("sowing_date")
    @classmethod
    def validate_sowing_date(cls, v: datetime.date | None) -> datetime.date | None:
        if v is None:
            return v
        today = datetime.date.today()
        if v > today:
            raise ValueError("Sowing date cannot be in the future.")
        if (today - v).days > 400:
            raise ValueError("Sowing date cannot be more than 400 days in the past.")
        return v


# --- Dashboard Plot Summary ---
class CropRef(BaseModel):
    id: str
    common_name: str


class StageRef(BaseModel):
    id: str
    name: str
    bbch: str


class LatestRiskSummary(BaseModel):
    score: int
    severity: str
    primary_threat: str
    created_at: str
    is_stale: bool = False


class PlotSummary(BaseModel):
    id: int
    name: str
    crop: CropRef
    stage: StageRef
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    sowing_date: str
    days_after_sowing: int
    latest_risk: LatestRiskSummary | None


# --- Risk Detail View ---
class PlotDetailInfo(BaseModel):
    id: int
    name: str
    crop: str
    crop_id: str | None = None
    scientific_name: str
    stage: str
    stage_id: str | None = None
    bbch: str
    location_name: str
    latitude: float | None = None
    longitude: float | None = None
    sowing_date: str
    days_after_sowing: int


class RiskDetailInfo(BaseModel):
    score: int
    severity: str
    primary_threat: str
    hazard_indices: dict[str, float]
    created_at: str
    is_stale: bool


class WeatherDigestSchema(BaseModel):
    peak_temp_c: float
    min_temp_c: float
    total_rain_mm: float
    max_wind_kmh: float
    peak_humidity_pct: float
    longest_disease_window_h: int


class ForecastIntervalSchema(BaseModel):
    timestamp: str
    temperature_c: float
    relative_humidity: float
    wind_kmh: float
    rain_mm: float


class WeatherInfo(BaseModel):
    digest: WeatherDigestSchema
    intervals: list[ForecastIntervalSchema]


class PlotRiskResponse(BaseModel):
    plot: PlotDetailInfo
    risk: RiskDetailInfo
    advisory: AdvisoryResponse
    weather: WeatherInfo
