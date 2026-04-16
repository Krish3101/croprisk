"""Crop Service
Handles crop management operations using SQLite database
"""

from datetime import datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from config import get_logger
from models.database import Crop
from utils.helpers import StorageError

logger = get_logger(__name__)


def add_crop(db: Session, crop_name: str, plot: str) -> dict[str, Any]:
    """Add a new crop to tracking

    Args:
        db: Database session
        crop_name: Crop name
        plot: Plot/field identifier

    Returns:
        Dictionary with status and new crop data

    """
    logger.info(f"Adding crop: {crop_name} to plot: {plot}")

    try:
        new_crop = Crop(crop=crop_name, plot=plot, sown_date=datetime.now().strftime("%d %b %Y"), stage="Sown")

        db.add(new_crop)
        db.commit()
        db.refresh(new_crop)

        logger.info(f"Successfully added crop: {crop_name}")

        return {
            "status": "success",
            "message": "Crop added",
            "data": {
                "id": new_crop.id,
                "crop": new_crop.crop,
                "plot": new_crop.plot,
                "sown_date": new_crop.sown_date,
                "stage": new_crop.stage,
            },
        }
    except Exception as e:
        logger.error(f"Error adding crop: {e}")
        db.rollback()
        raise StorageError(f"Failed to add crop: {e}") from e


def delete_crop(db: Session, crop_id: int) -> dict[str, Any]:
    """Delete a crop by ID

    Args:
        db: Database session
        crop_id: ID of crop to delete

    Returns:
        Dictionary with status and deleted crop data

    """
    logger.info(f"Deleting crop with ID: {crop_id}")

    try:
        crop = db.query(Crop).filter(Crop.id == crop_id).first()

        if not crop:
            logger.warning(f"Crop not found with ID: {crop_id}")
            return {"error": "Crop not found"}

        # Store data for return
        crop_data = {"id": crop.id, "crop": crop.crop, "plot": crop.plot}

        db.delete(crop)
        db.commit()

        logger.info(f"Successfully deleted crop: {crop.crop}")

        return {"status": "success", "message": "Crop deleted", "data": crop_data}
    except Exception as e:
        logger.error(f"Error deleting crop: {e}")
        db.rollback()
        raise StorageError(f"Failed to delete crop: {e}") from e


def get_crops(db: Session) -> list[dict[str, Any]]:
    """Get all tracked crops

    Args:
        db: Database session

    Returns:
        List of crops sorted newest first

    """
    logger.info("Fetching all crops")

    try:
        crops = db.query(Crop).order_by(desc(Crop.created_at)).all()

        return [
            {
                "id": c.id,
                "crop": c.crop,
                "plot": c.plot,
                "sown_date": c.sown_date,
                "stage": c.stage,
                "expected_harvest": c.expected_harvest,
                "notes": c.notes,
            }
            for c in crops
        ]
    except Exception as e:
        logger.error(f"Error fetching crops: {e}")
        return []


def update_crop_stage(db: Session, crop_id: int, stage: str) -> dict[str, Any]:
    """Update crop growth stage

    Args:
        db: Database session
        crop_id: ID of crop to update
        stage: New growth stage

    Returns:
        Dictionary with status and updated crop data

    """
    logger.info(f"Updating crop {crop_id} stage to: {stage}")

    try:
        crop = db.query(Crop).filter(Crop.id == crop_id).first()

        if not crop:
            logger.warning(f"Crop not found with ID: {crop_id}")
            return {"error": "Crop not found"}

        crop.stage = stage
        crop.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(crop)

        logger.info(f"Successfully updated crop stage: {crop.crop}")

        return {
            "status": "success",
            "message": "Crop stage updated",
            "data": {"id": crop.id, "crop": crop.crop, "plot": crop.plot, "stage": crop.stage},
        }
    except Exception as e:
        logger.error(f"Error updating crop stage: {e}")
        db.rollback()
        raise StorageError(f"Failed to update crop stage: {e}") from e
