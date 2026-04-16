"""Pydantic Schemas
Data Transfer Objects (DTOs) for API requests and responses
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=6, max_length=128)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=200)


class ExpenseCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    amount: float = Field(..., gt=0, le=10000000)
    type: str = Field(..., pattern=r"^(income|expense)$")
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=1000)
    crop_id: int | None = Field(None, ge=1)

    @validator("date")
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")


class CropCreate(BaseModel):
    crop: str = Field(..., min_length=2, max_length=100)
    plot: str = Field(..., min_length=2, max_length=100)

    @validator("crop", "plot")
    def validate_no_special_chars(cls, v):
        if not v.replace(" ", "").replace("-", "").replace("_", "").isalnum():
            raise ValueError("Only alphanumeric characters, spaces, hyphens, and underscores allowed")
        return v.strip()


class CropStageUpdate(BaseModel):
    stage: str = Field(..., min_length=2, max_length=50)


class SoilReportCreate(BaseModel):
    nitrogen: float = Field(..., ge=0, le=1000, description="Nitrogen in kg/ha")
    phosphorus: float = Field(..., ge=0, le=1000, description="Phosphorus in kg/ha")
    potassium: float = Field(..., ge=0, le=1000, description="Potassium in kg/ha")
    ph: float = Field(..., ge=0, le=14, description="pH level")
    moisture: float = Field(..., ge=0, le=100, description="Moisture percentage")
    location: str | None = Field("default", max_length=100)

    @validator("location")
    def validate_location(cls, v):
        if v:
            return v.strip()
        return "default"
