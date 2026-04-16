"""Crop API Routes"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config import get_logger
from models.database import get_db
from models.schemas import CropCreate, CropStageUpdate
from services.crop_service import (
    add_crop as add_crop_service,
)
from services.crop_service import (
    delete_crop as delete_crop_service,
)
from services.crop_service import (
    get_crops as get_crops_service,
)
from services.crop_service import (
    update_crop_stage as update_crop_stage_service,
)

logger = get_logger(__name__)
router = APIRouter()


class CropDelete(BaseModel):
    id: int = Field(..., ge=1)


@router.get("/crops", response_model=None)
def get_crops(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get list of all tracked crops."""
    logger.info("Crops list endpoint called")
    try:
        return get_crops_service(db)
    except Exception as e:
        logger.error(f"Failed to fetch crops: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch crops")


@router.post("/crops/add", response_model=None)
def add_crop(crop_data: CropCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Add a new crop to track."""
    logger.info(f"Adding crop: {crop_data.crop} to plot: {crop_data.plot}")
    try:
        return add_crop_service(db, crop_data.crop, crop_data.plot)
    except Exception as e:
        logger.error(f"Failed to add crop: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to add crop")


@router.post("/crops/delete", response_model=None)
def delete_crop(delete_data: CropDelete, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a tracked crop."""
    logger.info(f"Deleting crop with id: {delete_data.id}")
    try:
        result = delete_crop_service(db, delete_data.id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete crop: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete crop")


@router.patch("/crops/{crop_id}/stage", response_model=None)
def update_stage(crop_id: int, stage_data: CropStageUpdate, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Update crop growth stage."""
    logger.info(f"Updating crop {crop_id} to stage: {stage_data.stage}")
    try:
        result = update_crop_stage_service(db, crop_id, stage_data.stage)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update crop stage: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update crop stage")
