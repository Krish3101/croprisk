"""Soil Service
Handles soil health data management using SQLAlchemy database
"""

from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from config import get_logger
from models.database import SoilReport
from utils.helpers import StorageError

logger = get_logger(__name__)


def get_all_soil_reports(db: Session) -> list[dict[str, Any]]:
    """Get all soil reports from database

    Args:
        db: Database session

    Returns:
        List of soil report dictionaries

    """
    logger.info("Fetching all soil reports")

    try:
        reports = db.query(SoilReport).order_by(desc(SoilReport.created_at)).all()

        return [
            {
                "id": r.id,
                "location": r.field,  # Map 'field' to 'location' for frontend compatibility
                "ph": r.ph,
                "nitrogen": r.nitrogen,
                "phosphorus": r.phosphorus,
                "potassium": r.potassium,
                "moisture": r.moisture,
                "date": r.last_tested or r.created_at.strftime("%d %b %Y"),
            }
            for r in reports
        ]
    except Exception as e:
        logger.error(f"Error fetching soil reports: {e}")
        return []


def get_soil_report(db: Session, field: str = "default") -> dict[str, Any]:
    """Get soil health report for a specific field

    Args:
        db: Database session
        field: Field name (default: "default")

    Returns:
        Dictionary with soil data or error message

    """
    logger.info(f"Fetching soil report for field: {field}")

    try:
        # Get the most recent report for the field
        report = db.query(SoilReport).filter(SoilReport.field == field).order_by(desc(SoilReport.created_at)).first()

        if report:
            return {
                "id": report.id,
                "field": report.field,
                "ph": report.ph,
                "nitrogen": report.nitrogen,
                "phosphorus": report.phosphorus,
                "potassium": report.potassium,
                "moisture": report.moisture,
                "last_tested": report.last_tested or report.created_at.strftime("%d %b %Y"),
            }

        logger.warning(f"No soil data found for field: {field}")
        return {"error": "No soil data"}

    except Exception as e:
        logger.error(f"Error fetching soil report: {e}")
        return {"error": "Failed to fetch soil data"}


def add_soil_report(
    db: Session,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    moisture: float,
    location: str = "default",
) -> dict[str, Any]:
    """Add a new soil report to the database

    Args:
        db: Database session
        nitrogen: Nitrogen level
        phosphorus: Phosphorus level
        potassium: Potassium level
        ph: pH level
        moisture: Moisture percentage
        location: Field/location name

    Returns:
        Dictionary with status and saved data

    """
    logger.info(f"Adding soil report for location: {location}")

    try:
        new_report = SoilReport(
            field=location,
            ph=float(ph),
            nitrogen=float(nitrogen),
            phosphorus=float(phosphorus),
            potassium=float(potassium),
            moisture=float(moisture),
            last_tested=datetime.now().strftime("%d %b %Y"),
        )

        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        logger.info(f"Soil report saved for location: {location}")

        logger.info(f"Successfully saved soil report for location: {location}")

        return {
            "status": "success",
            "message": "Soil report saved",
            "data": {
                "id": new_report.id,
                "location": new_report.field,
                "ph": new_report.ph,
                "nitrogen": new_report.nitrogen,
                "phosphorus": new_report.phosphorus,
                "potassium": new_report.potassium,
                "moisture": new_report.moisture,
                "date": new_report.last_tested,
            },
        }

    except Exception as e:
        logger.error(f"Error adding soil report: {e}")
        db.rollback()
        raise StorageError(f"Failed to save soil report: {e}") from e
