"""Dashboard API Routes"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from config import get_logger, settings
from models.database import get_db
from services.ai_service import generate_dashboard_insight
from services.crop_service import get_crops
from services.expense_service import get_summary
from services.price_service import get_market_price
from services.weather_service import get_weather

logger = get_logger(__name__)
router = APIRouter()


@router.get("/dashboard", response_model=None)
def get_dashboard_data(
    city: str = Query(None, description="City for weather"),
    crop: str = Query(None, description="Crop for price"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get aggregated data for the dashboard."""
    # Use config defaults if not provided
    city = city or settings.DEFAULT_CITY
    crop = crop or settings.DEFAULT_CROP

    logger.info(f"Dashboard endpoint called with city={city}, crop={crop}")

    try:
        # Fetch all dashboard data with individual error handling
        weather_data = {}
        try:
            weather_data = get_weather(db, city)
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            weather_data = {"error": "Failed to fetch weather"}

        price_data = {}
        try:
            price_data = get_market_price(db, crop, settings.DEFAULT_STATE)
        except Exception as e:
            logger.error(f"Price fetch failed: {e}")
            price_data = {"error": "Failed to fetch prices"}

        crops_data = []
        try:
            crops_data = get_crops(db)
        except Exception as e:
            logger.error(f"Crops fetch failed: {e}")

        finance_data = {}
        try:
            finance_data = get_summary(db)
        except Exception as e:
            logger.error(f"Finance fetch failed: {e}")
            finance_data = {"total_income": 0, "total_expense": 0, "profit": 0}

        return {
            "weather": weather_data,
            "price": price_data,
            "crop_count": len(crops_data),
            "crops": crops_data,
            "financials": {
                "total_income": finance_data.get("total_income", 0),
                "total_expense": finance_data.get("total_expense", 0),
                "profit": finance_data.get("profit", 0),
            },
        }
    except Exception as e:
        logger.error(f"Dashboard data fetch failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch dashboard data")


@router.get("/dashboard/insight", response_model=None)
async def get_dashboard_insight(
    city: str = Query(None, description="City for weather"),
    crop: str = Query(None, description="Crop for price"),
    db: Session = Depends(get_db),
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
