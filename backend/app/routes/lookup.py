"""Lookup routes: crops catalogue and geocoding."""

from fastapi import APIRouter, Depends, Query

from app.deps import get_current_user
from app.domain.crops import CROPS
from app.models import User
from app.schemas import CropSummary, GeocodeCandidate, StageSummary
from app.services.weather import geocode

router = APIRouter(tags=["lookup"])


@router.get("/crops", response_model=list[CropSummary])
def get_crops(_current_user: User = Depends(get_current_user)) -> list[CropSummary]:
    result: list[CropSummary] = []
    for crop in CROPS.values():
        sorted_stages = sorted(crop.stages.values(), key=lambda s: s.order)
        stage_summaries = [
            StageSummary(
                id=s.id,
                name=s.name,
                bbch=s.bbch,
                order=s.order,
            )
            for s in sorted_stages
        ]
        result.append(
            CropSummary(
                id=crop.id,
                common_name=crop.common_name,
                scientific_name=crop.scientific_name,
                stages=stage_summaries,
            )
        )
    return result


@router.get("/geocode", response_model=list[GeocodeCandidate])
def geocode_location(
    q: str = Query(default=""),
    _current_user: User = Depends(get_current_user),
) -> list[GeocodeCandidate]:
    candidates = geocode(q)
    return [GeocodeCandidate(**c) for c in candidates]
