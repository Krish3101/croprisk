from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlotCreate(BaseModel):
    name: str
    crop_type: str
    location: str
    growth_stage: str
    sowing_date: str


class PlotUpdate(BaseModel):
    name: str | None = None
    crop_type: str | None = None
    location: str | None = None
    growth_stage: str | None = None
    sowing_date: str | None = None


class RiskAssessmentResponse(BaseModel):
    id: int
    plot_id: int
    risk_score: int
    severity: str
    primary_risk: str | None
    analysis: str
    recommendation: str
    weather_summary: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlotResponse(BaseModel):
    id: int
    name: str
    crop_type: str
    location: str
    growth_stage: str
    sowing_date: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlotWithRiskResponse(PlotResponse):
    latest_risk: RiskAssessmentResponse | None = None
