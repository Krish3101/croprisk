"""Weather API Routes"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config import get_logger, settings
from models.database import get_db
from services.weather_service import get_weather as get_weather_service
from services.weather_service import get_weather_forecast as get_weather_forecast_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/weather", response_model=None)
def get_weather(city: str = Query(None, description="City name"), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get weather information for a specific city."""
    # Use config default if not provided
    city = city.strip() if city else settings.DEFAULT_CITY
    
    # Input validation
    if not city:
        return {"error": "City name is required"}
    if len(city) > 100:
        city = city[:100]
    # Remove any potentially harmful characters
    city = "".join(c for c in city if c.isalnum() or c.isspace() or c in "-'")
    if not city:
        return {"error": "Invalid city name"}

    logger.info(f"Weather endpoint called for city: {city}")
    return get_weather_service(db, city)


@router.get("/weather/forecast", response_model=None)
def get_weather_forecast(
    city: str = Query(None, description="City name"), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Get 5-day weather forecast for a specific city."""
    # Use config default if not provided
    city = city.strip() if city else settings.DEFAULT_CITY
    
    # Input validation
    if not city:
        return {"error": "City name is required"}
    if len(city) > 100:
        city = city[:100]
    # Remove any potentially harmful characters
    city = "".join(c for c in city if c.isalnum() or c.isspace() or c in "-'")
    if not city:
        return {"error": "Invalid city name"}

    logger.info(f"Weather forecast endpoint called for city: {city}")
    return get_weather_forecast_service(db, city)
