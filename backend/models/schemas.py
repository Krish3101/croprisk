from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    
    class Config:
        from_attributes = True

class PlotCreate(BaseModel):
    name: str
    crop_type: str
    location: str
    growth_stage: str
    sowing_date: str

class PlotUpdate(BaseModel):
    name: Optional[str] = None
    crop_type: Optional[str] = None
    location: Optional[str] = None
    growth_stage: Optional[str] = None
    sowing_date: Optional[str] = None

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

    class Config:
        from_attributes = True

class PlotResponse(BaseModel):
    id: int
    name: str
    crop_type: str
    location: str
    growth_stage: str
    sowing_date: str
    created_at: datetime

    class Config:
        from_attributes = True

class PlotWithRiskResponse(PlotResponse):
    latest_risk: Optional[RiskAssessmentResponse] = None
