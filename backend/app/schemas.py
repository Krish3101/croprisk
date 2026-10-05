"""Pydantic request and response models. Requests forbid unknown fields and trim strings."""

import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Advisory (also the shape the LLM must reply with)


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    timeframe: Literal["immediate_24h", "preventative_72h"]
    directive: str = Field(..., min_length=15, max_length=250)


class Advisory(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str = Field(..., min_length=10, max_length=140)
    impact_analysis: str = Field(..., min_length=30, max_length=400)
    actions: list[Action] = Field(..., min_length=1, max_length=3)
    monitoring_focus: str = Field(..., min_length=15, max_length=200)


class AdvisoryResponse(Advisory):
    source: Literal["bypass", "llm", "fallback"]


# Crops & Stages
class StageSummary(BaseModel):
    id: str
    name: str
    bbch: str
    order: int
    t_crit_heat: float
    t_crit_frost: float


class CropSummary(BaseModel):
    id: str
    common_name: str
    scientific_name: str
    stages: list[StageSummary]


# Geocoding
class GeocodeCandidate(BaseModel):
    display_name: str
    city: str | None = None
    state: str | None = None
    country: str | None = None
    latitude: float
    longitude: float


# Plots Request / Response Models
class PlotCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=100)
    crop_id: str = Field(..., min_length=1, max_length=50)
    stage_id: str = Field(..., min_length=1, max_length=100)
    location_name: str = Field(..., min_length=1, max_length=200)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    sowing_date: datetime.date

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field name cannot be empty or whitespace only.")
        return v.strip()

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
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    crop_id: str | None = Field(default=None, min_length=1, max_length=50)
    stage_id: str | None = Field(default=None, min_length=1, max_length=100)
    location_name: str | None = Field(default=None, min_length=1, max_length=200)
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    sowing_date: datetime.date | None = None

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str | None) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field name cannot be empty or whitespace only.")
        return v.strip() if v is not None else None

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

    @model_validator(mode="after")
    def reject_nulls(self) -> "PlotUpdateRequest":
        # Fields can be left out, but not sent as null.
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null.")
        return self


# Dashboard Plot Summary
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
    is_stale: bool


class PlotSummary(BaseModel):
    id: int
    name: str
    crop: CropRef
    stage: StageRef
    location_name: str
    latitude: float
    longitude: float
    sowing_date: str
    days_after_sowing: int
    latest_risk: LatestRiskSummary | None = None


# Detailed Plot Risk Evaluation Response
class PlotDetailInfo(BaseModel):
    id: int
    name: str
    crop: str
    crop_id: str
    scientific_name: str
    stage: str
    stage_id: str
    bbch: str
    location_name: str
    latitude: float
    longitude: float
    sowing_date: str
    days_after_sowing: int


class RiskDetail(BaseModel):
    score: int
    severity: str
    primary_threat: str
    hazard_indices: dict[str, float]
    created_at: str
    is_stale: bool
    forecast_fetched_at: str


class IntervalItem(BaseModel):
    timestamp: str
    temperature_c: float
    relative_humidity: float
    wind_kmh: float
    rain_mm: float


class WeatherSection(BaseModel):
    digest: dict[str, Any]
    intervals: list[IntervalItem]


class PlotRiskResponse(BaseModel):
    plot: PlotDetailInfo
    risk: RiskDetail
    advisory: AdvisoryResponse
    weather: WeatherSection
    refreshed: bool = False


# Health check response
class HealthResponse(BaseModel):
    status: str
    db: bool
    weather_key: bool
    llm_key: bool
    catalogue_version: str
    schema_version: int
