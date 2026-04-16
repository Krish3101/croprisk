"""Soil API Routes"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_logger
from models.database import get_db
from models.schemas import SoilReportCreate
from services.soil_service import add_soil_report, get_all_soil_reports

logger = get_logger(__name__)
router = APIRouter()


@router.get("/soil", response_model=None)
def get_soil(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get all soil reports."""
    logger.info("Soil endpoint called")
    try:
        return get_all_soil_reports(db)
    except Exception as e:
        logger.error(f"Failed to fetch soil reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch soil reports")


@router.post("/soil/add", response_model=None)
def add_soil(soil_data: SoilReportCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Add a new soil report."""
    logger.info(f"Adding soil report for location: {soil_data.location}")

    try:
        return add_soil_report(
            db,
            nitrogen=soil_data.nitrogen,
            phosphorus=soil_data.phosphorus,
            potassium=soil_data.potassium,
            ph=soil_data.ph,
            moisture=soil_data.moisture,
            location=soil_data.location,
        )
    except Exception as e:
        logger.error(f"Error adding soil report: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add soil report")
