"""Dashboard API Routes"""


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from config import get_logger, settings
from models.database import get_db, User
from utils.helpers import get_current_active_user
from services.ai_service import generate_dashboard_insight
from services.price_service import get_market_price
from services.weather_service import get_weather

logger = get_logger(__name__)
router = APIRouter()

@router.get("/dashboard/insight", response_model=None)
async def get_dashboard_insight(
    city: str = Query(None, description="City for weather"),
    crop: str = Query(None, description="Crop for price"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Get AI-generated insight for the dashboard."""
    # Use config defaults if not provided
    city = city or settings.DEFAULT_CITY
    crop = crop or settings.DEFAULT_CROP

    logger.info(f"Dashboard insight endpoint called for {city}, {crop}")

    try:
        w = get_weather(db, city)
        p = get_market_price(db, crop, settings.DEFAULT_STATE)

        w_str = f"{w.get('temp', 25)}C, {w.get('weather', 'Clear')}" if "error" not in w else "Unknown"
        p_str = f"{p.get('crop', crop)}: {p.get('modal_price', 'N/A')}" if "error" not in p else "Unknown"

        insight = await generate_dashboard_insight(w_str, p_str)
        return {"insight": insight}
    except Exception as e:
        logger.error(f"Dashboard insight generation failed: {e}")
        return {"insight": "Unable to generate insights at this time. Please try again later."}
